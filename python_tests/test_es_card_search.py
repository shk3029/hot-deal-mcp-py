import json

import httpx
import pytest

from mci.es_card_client import EsCardClient, build_query
from tools.es_card_search_tools import search_card_detail


def test_combined_filters_and_mapping(monkeypatch):
    monkeypatch.setenv('ES_PASSWORD', 'test-only')
    def respond(request):
        body = json.loads(request.content)
        assert request.url.path == '/cards-all/_search'
        assert body['query']['bool']['filter'] == [
            {'range': {'pvafeat': {'gte': 10000, 'lte': 20000}}},
            {'terms': {'svtcd': ['08', '9']}}]
        assert body['query']['bool']['must'][0]['multi_match']['query'] == '처음'
        return httpx.Response(200, json={'hits': {'total': {'value': 7}, 'hits': [{'_source': {
            'pageid': '001', 'pagetitle': '신한¶PS¶카드¶PE¶ 처음',
            'pvafeat': 15000, 'svtcd': ['08', '9'], 'svtpnm1': None,
        }}]}})
    result = EsCardClient(transport=httpx.MockTransport(respond)).call_with_itf_id(
        'EGN00002', data={'MSG': '처음', 'CRD_BNF': '08,9', 'AFE_MIN_VL': 10000, 'AFE_MAX_VL': 20000})
    assert result['TO_CT'] == 7
    card = result['GRID1'][0]
    assert card['CRD_PD_PGE_N'] == '001'
    assert card['CRD_PD_NM'] == '신한카드 처음'
    assert card['CRD_PD_AFE'] == 15000
    assert card['CRD_PD_BNF_CD'] == '08,9'
    assert card['CRD_PD_BNF_NM1'] == ''


@pytest.mark.parametrize('data', [{'SIZ': 101}, {'SIZ': -1}, {'SIZ': True},
    {'AFE_MIN_VL': 2, 'AFE_MAX_VL': 1}, {'QEE': 'invalid'}, {'CRD_BNF': '*'}, {'CRD_TP': 1}])
def test_invalid_inputs(data):
    with pytest.raises(ValueError):
        build_query(data)


def test_ambiguous_detail_does_not_choose_arbitrary_card():
    class Client:
        def call_with_itf_id(self, *args, **kwargs):
            return {'TO_CT': 2, 'GRID1': [{'CRD_PD_NM': '신한카드 처음'}, {'CRD_PD_NM': '신한카드 처음 체크'}]}
    output = json.loads(search_card_detail(Client(), '처음'))
    assert '정확히' in output['copy_text']
    output = json.loads(search_card_detail(Client(), '신한카드 처음'))
    assert '신한카드 처음' in output['copy_text']


def test_partial_failure_raises(monkeypatch):
    monkeypatch.setenv('ES_PASSWORD', 'test-only')
    client = EsCardClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={'timed_out': True})))
    with pytest.raises(RuntimeError, match='incomplete'):
        client.call_with_itf_id('EGN00002')


@pytest.mark.parametrize('name', ['SOL Plan+', 'SOL Plan＋'])
def test_plus_is_filtered_on_literal_title(name):
    body = build_query({'MSG': name})
    assert body['query']['bool']['filter'][-1] == {
        'wildcard': {'literal_card_title': {'value': '*+*'}}}
    assert body['runtime_mappings']['literal_card_title']['type'] == 'keyword'


def test_plain_name_does_not_need_runtime_field():
    assert 'runtime_mappings' not in build_query({'MSG': '처음'})
