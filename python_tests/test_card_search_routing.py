from unittest.mock import Mock

import pytest

from mci.card_client import create_card_client


@pytest.fixture
def clients(monkeypatch):
    default, search = Mock(), Mock()
    monkeypatch.setenv('CARD_DATA_SOURCE', 'mock')
    monkeypatch.setenv('CARD_SEARCH_DATA_SOURCE', 'es')
    monkeypatch.setattr('mci.mock_client.MockMciClient', lambda: default)
    monkeypatch.setattr('mci.es_card_client.EsCardClient', lambda: search)
    return default, search


def test_name_search_routes_and_forwards_flags(clients):
    default, search = clients
    data = {'MSG': '신한카드 처음', 'SIZ': 5, 'AFE_MAX_VL': 20000}
    result = create_card_client().call_with_itf_id('EGN00002', data=data, include_sensitive=True)
    assert result is search.call_with_itf_id.return_value
    search.call_with_itf_id.assert_called_once_with('EGN00002', data=data, include_sensitive=True)
    default.call_with_itf_id.assert_not_called()


@pytest.mark.parametrize('itf_id,data', [
    ('EGN00002', {'CRD_BNF': '8'}), ('EGN00002', {'TAG_VL': 'best'}),
    ('EGN00002', {'MSG': '  '}), ('EGN00002', {'MSG': None}), ('EGN00001', {'MSG': '처음'}),
])
def test_other_requests_stay_on_default(clients, itf_id, data):
    default, search = clients
    create_card_client().call_with_itf_id(itf_id, data=data)
    default.call_with_itf_id.assert_called_once_with(itf_id, data=data, include_sensitive=False)
    search.call_with_itf_id.assert_not_called()


@pytest.mark.parametrize('setting', [None, '', 'mock'])
def test_unset_or_same_preserves_original_client(clients, monkeypatch, setting):
    if setting is None:
        monkeypatch.delenv('CARD_SEARCH_DATA_SOURCE')
    else:
        monkeypatch.setenv('CARD_SEARCH_DATA_SOURCE', setting)
    assert create_card_client() is clients[0]


def test_invalid_source(clients, monkeypatch):
    monkeypatch.setenv('CARD_SEARCH_DATA_SOURCE', 'typo')
    with pytest.raises(RuntimeError, match='CARD_SEARCH_DATA_SOURCE'):
        create_card_client()


def test_search_error_does_not_fallback(clients):
    default, search = clients
    search.call_with_itf_id.side_effect = RuntimeError('ES unavailable')
    with pytest.raises(RuntimeError, match='ES unavailable'):
        create_card_client().call_with_itf_id('EGN00002', data={'MSG': '처음'})
    default.call_with_itf_id.assert_not_called()
