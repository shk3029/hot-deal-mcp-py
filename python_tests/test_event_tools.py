import asyncio
import json
import os
from datetime import date, timedelta

import pytest

os.environ.setdefault('CARD_DATA_SOURCE', 'mock')
from server import mcp
from domain.event_brand import BRAND_NAMES
from domain.event_type import EVENT_TYPE_CODES
from mci.event_client import EVENT_ITF_ID, event_request, parse_events, today_kst
from mci.event_mock import mock_event_rows
from mci.mock_client import MockMciClient
from tools.event_tools import find_events


def tool():
    return asyncio.run(mcp.get_tool('getBrandEvents'))


def call(**kwargs):
    return json.loads(tool().fn(**kwargs))


def ids(data):
    return [r['key'] for r in data['widget'].get('children', []) if 'key' in r]


class RecordingClient:
    """요청 전문을 기록하고 목업 응답(또는 지정 응답)을 돌려준다."""

    def __init__(self, responses=None):
        self.requests = []
        self._responses = responses
        self._mock = MockMciClient()

    def call_with_itf_id(self, itf_id, data=None, include_sensitive=False):
        self.requests.append((itf_id, dict(data)))
        if self._responses is not None:
            return self._responses.pop(0)
        return self._mock.call_with_itf_id(itf_id, data, include_sensitive)


def row(key, start, end, **extra):
    return {'MOB_WB_EVT_RCN': key, 'MOB_WB_EVT_NM': f'title-{key}', 'MOB_WB_EVT_TXT': 'summary',
            'MOB_WB_BNF_CTG': '쇼핑문화', 'HPG_EVT_CTG_IMG_URL': '/img/a.png',
            'HPG_EVT_DL_PGE_URL': '/evt/a.html', 'MOB_WB_EVT_STD': start, 'MOB_WB_EVT_EDD': end,
            'DIS_F': 'Y', **extra}


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


@pytest.mark.parametrize('brand,event_type,msg,cag_cd', [
    (None, None, '', ''),
    ('스타벅스', None, '스타벅스', ''),
    (None, '여행숙박', '', '53'),
    (None, '청소년', '', '55'),
    ('스타벅스', '여행숙박', '스타벅스', ''),
])
def test_egn00003_request(brand, event_type, msg, cag_cd):
    client = RecordingClient()
    find_events(client, brand, event_type)
    itf_id, data = client.requests[0]
    assert itf_id == EVENT_ITF_ID == 'EGN00003'
    assert data == {'CHL': 'sol-hpg', 'CAG': 'event', 'MSG': msg, 'CAG_CD': cag_cd, 'QEE': 'now_event'}


@pytest.mark.parametrize('arguments', [
    {'brand':'CU'}, {'brand':'학원비'}, {'event_type':'학원비'}, {'brand':'스벅'},
    {'brand':'없는브랜드','event_type':'여행숙박'},
])
def test_no_match_or_unsupported_falls_back_to_latest(arguments):
    client = RecordingClient()
    label, events, notice = find_events(client, arguments.get('brand'), arguments.get('event_type'))
    assert label == '전체 최신' and len(events) == 5 and '요청 조건에 맞는' in notice
    assert client.requests[-1][1] == event_request()
    # 지원하지 않는 값은 MCI 키워드로 보내지 않는다.
    assert all(data['MSG'] in ('', 'CU') for _, data in client.requests)


def test_date_filter_keeps_mci_order_and_inclusive_bounds():
    today = date(2026, 11, 16)
    grid = [row('a', '20261116', '20261116'), row('ended', '20261001', '20261115'),
            row('b', '20261101', '20261130'), row('upcoming', '20261117', '20261231'),
            row('bad', '2026111', '20261231'), row('c', '2026-11-01', '2026.11.30')]
    assert [e.id for e in parse_events({'GRID1': grid}, today=today)] == ['a', 'b', 'c']
    with pytest.raises(TypeError):
        parse_events({'GRID1': 'x'}, today=today)


def test_parser_accepts_confirmed_full_field_names():
    # 정의서의 실제 전체 영문명이 가칭과 달라도 접두어가 같으면 읽는다.
    grid = [{'MOB_WB_EVT_RCV_NO': '1', 'MOB_WB_EVT_NM': 't', 'MOB_WB_EVT_STR_DT': '20260101',
             'MOB_WB_EVT_END_DT': '20991231', 'HPG_EVT_CTG_IMG': 'i', 'HPG_EVT_DL_PG_URL': 'u'}]
    event = parse_events({'GRID1': grid}, today=date(2026, 11, 16))[0]
    assert (event.id, event.thumbnail_url, event.detail_url) == ('1', 'i', 'u')


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
    assert len(ids(data)) == count
    assert ('더 많은 이벤트 보기' in data['copy_text']) == (kind == 'ListView')
    assert 'ended' not in ids(data) and 'upcoming' not in ids(data)
    assert result.structured_content == {'result': result.content[0].text}


def test_brand_overrides_category():
    assert call(brand='스타벅스', event_type='여행숙박') == call(brand='스타벅스')
    assert ids(call(brand='스타벅스')) == ['starbucks-shopping', 'starbucks-payment']


@pytest.mark.parametrize('brand', BRAND_NAMES)
def test_all_enum_values_are_accepted(brand):
    result = asyncio.run(tool().run({'brand':brand}))
    assert set(json.loads(result.content[0].text)) == {'widget','copy_text'}


def test_list_row_layout_and_more_button_last(monkeypatch):
    monkeypatch.setenv('EVENT_LIST_URL', 'https://example.test/events')
    children = call()['widget']['children']
    rows = [r for r in children if 'key' in r]
    assert len(rows) == 5
    for item in rows:
        image, texts, detail = item['children']
        assert image['type'] == 'Image' and image['src'].endswith('/thumbnail.svg')
        summary, title = texts['children']
        assert summary['type'] == 'Text' and title['type'] == 'Caption'
        assert detail['iconEnd'] == 'chevron-right'
        assert detail['onClickAction'] == item['onClickAction']
    more = children[-1]['children'][0]
    assert more['label'] == '더 많은 이벤트 보기'
    assert more['onClickAction']['payload']['target']['url'] == 'https://example.test/events?param=fr_kkt'
    card = call(brand='SOL LINK 체크카드')['widget']['children']
    row, detail = card[-2:]
    assert row['type'] == 'Row' and [c['type'] for c in row['children']] == ['Image', 'Col']
    assert detail['label'] == '자세히 보기'
    url = detail['onClickAction']['payload']['target']['url']
    assert url.endswith('/mock-events/sol-link?param=fr_kkt')
    assert '더 많은 이벤트 보기' not in json.dumps(card, ensure_ascii=False)
    assert 'chevron-right' not in json.dumps(card)


def test_more_events_default_url(monkeypatch):
    monkeypatch.delenv('EVENT_LIST_URL', raising=False)
    more = call()['widget']['children'][-1]['children'][0]
    assert more['onClickAction']['payload']['target']['url'] == (
        'https://www.shinhancard.com/mob/MOBFM829N/MOBFM829R03.shc?sourcePage=R01&param=fr_kkt')


def test_relative_urls_become_shinhancard_urls():
    from kakao.events import event_list
    today = today_kst()
    grid = [row('a', (today - timedelta(days=1)).strftime('%Y%m%d'),
                (today + timedelta(days=1)).strftime('%Y%m%d'))]
    widget = event_list('x', parse_events({'GRID1': grid}, today=today))['widget']
    image, _ = widget['children'][1]['children']
    detail = widget['children'][2]
    assert detail['label'] == '자세히 보기'
    assert image['src'] == 'https://cdn.www.shinhancard.com/img/a.png'
    assert detail['onClickAction']['payload']['target']['url'] == 'https://www.shinhancard.com/evt/a.html?param=fr_kkt'


def test_referrer_is_not_duplicated():
    from kakao.common import add_card_referrer
    url = 'https://www.shinhancard.com/evt/a.html?x=1&param=fr_kkt'
    assert add_card_referrer(url) == url
    assert add_card_referrer('') == ''


def test_empty_result_and_backend_failure(monkeypatch):
    empty = {'GRID1': []}
    label, events, notice = find_events(RecordingClient([empty, empty]), '스타벅스', None)
    assert events == [] and notice
    from kakao.events import event_list
    assert '현재 진행 중인 이벤트가 없습니다' in event_list(label, events, notice=notice)['copy_text']
    with pytest.raises(TypeError):
        find_events(RecordingClient([{'GRID1': None}]), None, None)


def test_mock_rows_include_out_of_period_events():
    keys = {r['MOB_WB_EVT_RCN'] for r in mock_event_rows()}
    assert {'ended', 'upcoming'} <= keys


@pytest.mark.parametrize('name,arguments', [
    ('getCreditCardRecommendationsWithSelector',{}),
    ('getCreditCardDetail',{'cardName':'신한카드 Mr.Life'}),
    ('getPopularCreditCards',{}),
    ('getFinancialLifeKnowledgeArticles',{'category':'금융'}),
])
def test_existing_tools(name,arguments):
    result=asyncio.run(asyncio.run(mcp.get_tool(name)).run(arguments))
    assert set(json.loads(result.content[0].text))=={'widget','copy_text'}


def test_http_schema_and_optional_arguments():
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


def test_preview_landing_links(monkeypatch):
    from fastapi.testclient import TestClient
    from preview.app import app
    monkeypatch.setenv('EVENT_MOCK_BASE_URL','http://testserver')
    with TestClient(app) as client:
        for path in ['/mock-events', '/mock-events/sol-link']:
            r=client.get(path)
            assert r.status_code==200 and '가상 데이터' in r.text
        assert client.get('/mock-events/not-found').status_code==404
        assert client.get('/mock-events/ended').status_code==404
        thumb=client.get('/mock-events/sol-link/thumbnail.svg')
        assert thumb.status_code==200 and thumb.headers['content-type'].startswith('image/svg+xml')
        monkeypatch.setenv('CARD_DATA_SOURCE','mci')
        assert client.get('/mock-events').status_code==503
