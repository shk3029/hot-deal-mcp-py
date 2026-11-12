import asyncio
import json
import os
from datetime import timedelta
from types import SimpleNamespace

import pytest

os.environ.setdefault('CARD_DATA_SOURCE', 'mock')
from server import mcp
from domain.event_brand import BRAND_NAMES
from domain.event_type import EVENT_TYPE_CODES
from mci.event_client import Event, create_event_client, today_kst
from tools import event_tools


def tool():
    return asyncio.run(mcp.get_tool('getBrandEvents'))


def call(**kwargs):
    return json.loads(tool().fn(**kwargs))


def ids(data):
    return [r['key'] for r in data['widget'].get('children', []) if 'key' in r]


@pytest.fixture(autouse=True)
def mock_mode(monkeypatch):
    monkeypatch.setenv('EVENT_DATA_SOURCE', 'mock')


def test_schema_and_category_codes():
    schema = tool().to_mcp_tool().inputSchema
    assert schema['required'] == []
    assert schema['properties']['brand']['enum'] == BRAND_NAMES
    assert len(BRAND_NAMES) == len(set(BRAND_NAMES)) == 98
    assert schema['properties']['event_type']['enum'] == list(EVENT_TYPE_CODES)
    assert EVENT_TYPE_CODES == {'쇼핑문화':51, '앱테크':52, '여행숙박':53, '카드결제':54, '청소년':55}
    assert len(tool().description) <= 1024
    assert all(len(p['description']) <= 1024 for p in schema['properties'].values())
    assert ', '.join(BRAND_NAMES) not in schema['properties']['brand']['description']


@pytest.mark.parametrize('arguments,kind,count', [
    ({}, 'ListView', 5),
    ({'event_type':'여행숙박'}, 'ListView', 5),
    ({'brand':'SOL LINK 체크카드'}, 'Card', 1),
    ({'brand':'스타벅스'}, 'ListView', 2),
    ({'brand':'슈퍼SOL'}, 'ListView', 5),
    ({'event_type':'앱테크'}, 'Card', 1),
    ({'event_type':'청소년'}, 'Card', 1),
])
def test_planning_examples(arguments, kind, count):
    result = asyncio.run(tool().run(arguments))
    data = json.loads(result.content[0].text)
    assert data['widget']['type'] == kind
    assert data['copy_text'].count('[자세히 보기 (목업)]') == count
    assert '더 많은 이벤트 보기' in data['copy_text']
    assert '실제 이벤트 또는 개인별 참여 가능 여부' in data['copy_text']
    assert result.structured_content == {'result': result.content[0].text}


def test_list_row_layout_and_more_button_last(monkeypatch):
    from kakao.events import mock_events_url
    monkeypatch.setenv('EVENT_MOCK_BASE_URL','http://testserver')
    data = call()
    children = data['widget']['children']
    rows = [r for r in children if 'key' in r]
    assert len(rows) == 5
    for row in rows:
        image, texts, detail = row['children']
        assert image['type'] == 'Image' and image['src'].endswith(f"/mock-events/{row['key']}/thumbnail.svg")
        summary, title = texts['children']
        assert summary['type'] == 'Text' and '(목업)' in summary['value']
        assert title['type'] == 'Caption' and title['value'].startswith('[목업]')
        assert detail['iconEnd'] == 'chevron-right'
        assert detail['onClickAction']['payload']['target']['url'] == mock_events_url(row['key'])
    more = children[-1]['children'][0]
    assert more['label'] == '더 많은 이벤트 보기'
    assert more['onClickAction']['payload']['target']['url'] == mock_events_url()
    card = call(brand='SOL LINK 체크카드')['widget']['children']
    assert card[-2]['type'] == 'Row' and card[-1]['label'] == '더 많은 이벤트 보기'


def test_brand_overrides_category_even_when_category_is_wrong():
    assert call(brand='스타벅스', event_type='여행숙박') == call(brand='스타벅스')
    text = call(brand='스타벅스')['copy_text']
    assert '쇼핑문화' in text and '카드결제' in text
    assert call(brand='SOL LINK 체크카드', event_type='카드결제')['widget']['type'] == 'Card'
    assert call(brand='스타벅스', event_type='없는분류') == call(brand='스타벅스')


@pytest.mark.parametrize('arguments', [
    {'brand':'CU'}, {'brand':'학원비'}, {'event_type':'학원비'},
    {'brand':''}, {'brand':'스벅'}, {'brand':'스타벅스 '},
    {'brand':'없는브랜드','event_type':'여행숙박'},
])
def test_no_match_and_unsupported_filters_fall_back(arguments):
    data = call(**arguments)
    assert ids(data) == ids(call())
    assert '요청 조건에 맞는' in data['copy_text']
    assert data['copy_text'].count('[자세히 보기 (목업)]') == 5


@pytest.mark.parametrize('brand', BRAND_NAMES)
def test_all_enum_values_are_accepted(brand):
    result = asyncio.run(tool().run({'brand':brand}))
    assert set(json.loads(result.content[0].text)) == {'widget','copy_text'}


def test_current_dates_latest_order_and_limit(monkeypatch):
    today = today_kst()
    def make(i, start=-1, end=1):
        return Event(id=str(i), brand='스타벅스',event_type='쇼핑문화',title=f'title-{i}',
            description='test', published_date=today-timedelta(days=i),
            start_date=today+timedelta(days=start),end_date=today+timedelta(days=end))
    events = [make(i) for i in range(8,0,-1)] + [make(0,end=-1), make(9,start=1)]
    monkeypatch.setattr(event_tools,'create_event_client',lambda:SimpleNamespace(list_events=lambda:events))
    assert ids(call()) == ['1','2','3','4','5']
    events[:] = [make(1,start=0,end=0)]
    assert call()['widget']['type'] == 'Card'


def test_empty_catalog_and_backend_failure(monkeypatch):
    monkeypatch.setattr(event_tools,'create_event_client',lambda:SimpleNamespace(list_events=lambda:[]))
    assert '현재 진행 중인 이벤트가 없습니다' in call(brand='CU')['copy_text']
    def fail():
        raise OSError('private backend message')
    monkeypatch.setattr(event_tools,'create_event_client',fail)
    with pytest.raises(RuntimeError) as error:
        call()
    assert 'private backend message' not in str(error.value)


@pytest.mark.parametrize('source',[None, 'mci', 'invalid'])
def test_no_automatic_mock_or_real_api_fallback(monkeypatch,source):
    if source is None:
        monkeypatch.delenv('EVENT_DATA_SOURCE',raising=False)
    else:
        monkeypatch.setenv('EVENT_DATA_SOURCE',source)
    with pytest.raises(RuntimeError):
        create_event_client()


@pytest.mark.parametrize('name,arguments', [
    ('getCreditCardRecommendationsWithSelector',{}),
    ('getCreditCardDetail',{'cardName':'신한카드 Mr.Life'}),
    ('getPopularCreditCards',{}),
    ('getFinancialLifeKnowledgeArticles',{'category':'금융'}),
])
def test_existing_tools(name,arguments):
    result=asyncio.run(asyncio.run(mcp.get_tool(name)).run(arguments))
    assert set(json.loads(result.content[0].text))=={'widget','copy_text'}


def test_http_schema_and_optional_arguments(monkeypatch):
    from fastapi.testclient import TestClient
    app=mcp.http_app(path='/mcp',stateless_http=True,json_response=True)
    with TestClient(app) as client:
        def rpc(method,params):
            r=client.post('/mcp',headers={'Accept':'application/json, text/event-stream'},
                json={'jsonrpc':'2.0','id':1,'method':method,'params':params})
            assert r.status_code==200
            return r.json()['result']
        rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}})
        schemas=rpc('tools/list',{})['tools']
        assert next(t for t in schemas if t['name']=='getBrandEvents')['inputSchema']['required']==[]
        for arguments in ({},{'brand':'스타벅스','event_type':'여행숙박'}):
            r=rpc('tools/call',{'name':'getBrandEvents','arguments':arguments})
            assert not r.get('isError')
        monkeypatch.delenv('EVENT_DATA_SOURCE')
        assert rpc('tools/call',{'name':'getBrandEvents','arguments':{}})['isError']


def test_preview_landing_links(monkeypatch):
    from fastapi.testclient import TestClient
    from preview.app import app
    from urllib.parse import urlsplit
    from kakao.events import mock_events_url
    monkeypatch.setenv('EVENT_MOCK_BASE_URL','http://testserver')
    with TestClient(app) as client:
        for path in ['/mock-events', urlsplit(mock_events_url('sol-link')).path]:
            r=client.get(path)
            assert r.status_code==200
            assert '가상 데이터' in r.text
        assert client.get('/mock-events/not-found').status_code==404
        thumb=client.get('/mock-events/sol-link/thumbnail.svg')
        assert thumb.status_code==200 and thumb.headers['content-type'].startswith('image/svg+xml')
        tools=client.get('/api/tools').json()['tools']
        assert next(t for t in tools if t['name']=='getBrandEvents')['inputSchema']['required']==[]
        monkeypatch.delenv('EVENT_DATA_SOURCE')
        assert client.get('/mock-events').status_code==503
