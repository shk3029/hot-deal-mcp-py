"""Read-only EGN00002 adapter for cards-all; no MCI configuration required.

ES_URL (default https://localhost:9200), ES_INDEX (cards-all), ES_CA_CERT,
ES_USER (elastic), ES_PASSWORD or ES_API_KEY configure the connection.
MSG searches card names; CRD_BNF is one service code or a list/comma-separated
codes (OR). Name, service and inclusive annual-fee bounds combine with AND.
SIZ is 0..100; QEE is score/date/high_rate/low_rate. TO_CT is the full count.
Only these search parameters are supported; other parameters are rejected.
"""
from __future__ import annotations

import json
import logging
import os
import re
import ssl
from typing import Any
from urllib.parse import quote

import httpx


response_logger = logging.getLogger("mci.es.response")
if not response_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    response_logger.addHandler(handler)
response_logger.setLevel(logging.INFO)
response_logger.propagate = False


FIELD_MAP = {
    'pageid': 'CRD_PD_PGE_N', 'pagetitle': 'CRD_PD_NM',
    'pagecont': 'CRD_PD_DESC', 'pageurl': 'CRD_PD_URL',
    'thumbimgurl': 'CRD_PD_IMG_URL', 'pdbstf': 'TAG_BST_VL',
    'pdpfrf': 'TAG_LAT_VL', 'pdcsbf': 'TAG_CSB_VL',
    **{f'svtpnm{i}': f'CRD_PD_BNF_NM{i}' for i in range(1, 4)},
    **{f'svtptt{i}': f'CRD_PD_BNF_DL{i}' for i in range(1, 4)},
}


def display_text(value: Any) -> str:
    return str(value if value is not None else '').replace('¶PS¶', '').replace('¶PE¶', '').strip()


def to_mci_card(source: dict[str, Any]) -> dict[str, Any]:
    result = {dest: display_text(source.get(src)) for src, dest in FIELD_MAP.items()}
    codes = source.get('svtcd') or []
    result['CRD_PD_BNF_CD'] = ','.join(str(c) for c in codes) if isinstance(codes, list) else str(codes)
    result['CRD_PD_AFE'] = int(source.get('pvafeat') or 0)
    return result


def _integer(value: Any, name: str) -> int:
    if isinstance(value, bool) or not re.fullmatch(r'\d+', str(value)):
        raise ValueError(f'{name} must be a nonnegative integer')
    return int(value)


def build_query(data: dict[str, Any]) -> dict[str, Any]:
    unknown = data.keys() - {'MSG', 'CRD_BNF', 'SIZ', 'QEE', 'AFE_MIN_VL', 'AFE_MAX_VL'}
    if unknown:
        raise ValueError(f'Unsupported EGN00002 parameters: {sorted(unknown)}')
    size = _integer(data.get('SIZ', 5), 'SIZ')
    low = _integer(data.get('AFE_MIN_VL', 0), 'AFE_MIN_VL')
    high = _integer(data.get('AFE_MAX_VL', 5_000_000), 'AFE_MAX_VL')
    if size > 100 or low > high:
        raise ValueError('SIZ must be 0..100 and AFE_MIN_VL <= AFE_MAX_VL')
    name = data.get('MSG') or ''
    if not isinstance(name, str):
        raise ValueError('MSG must be a string')
    name = display_text(name).replace("＋", "+")
    filters: list[dict[str, Any]] = [{'range': {'pvafeat': {'gte': low, 'lte': high}}}]
    codes = data.get('CRD_BNF')
    if codes is not None and codes != '' and codes != []:
        codes = codes if isinstance(codes, list) else str(codes).split(',')
        if any(isinstance(c, bool) or not re.fullmatch(r'\d+', str(c).strip()) for c in codes):
            raise ValueError('CRD_BNF must contain numeric service codes')
        filters.append({'terms': {'svtcd': [str(c).strip() for c in codes]}})
    query: dict[str, Any] = {'bool': {'filter': filters}}
    if name:
        query['bool']['must'] = [{'multi_match': {
            'query': name, 'fields': ['originalpagetitle^3', 'pagetitle'],
            'operator': 'and',
        }}]
        query['bool']['should'] = [{'match_phrase': {'originalpagetitle': {'query': name, 'boost': 5}}}]
    sort = data.get('QEE', 'score')
    orders = {
        'score': [{'_score': 'desc'}, {'pageid': 'desc'}],
        'date': [{'pageid': 'desc'}],
        'high_rate': [{'pvafeat': 'desc'}, {'pageid': 'desc'}],
        'low_rate': [{'pvafeat': 'asc'}, {'pageid': 'desc'}],
    }
    if sort not in orders:
        raise ValueError('QEE must be score/date/high_rate/low_rate')
    body = {'size': size, 'track_total_hits': True, 'query': query, 'sort': orders[sort],
            '_source': [*FIELD_MAP, 'svtcd', 'pvafeat']}
    if '+' in name or '＋' in name:
        # Nori drops punctuation. A runtime keyword over the original title
        # preserves the product's '+' without changing the stored index/schema.
        body['runtime_mappings'] = {'literal_card_title': {
            'type': 'keyword',
            'script': {'source': """
                def title = params._source.originalpagetitle;
                if (title == null) { title = params._source.pagetitle; }
                if (title != null) { emit(title.replace('＋', '+')); }
            """},
        }}
        filters.append({'wildcard': {'literal_card_title': {'value': '*+*'}}})
    return body


class EsCardClient:
    def __init__(self, *, transport: httpx.BaseTransport | None = None) -> None:
        self.base_url = os.getenv('ES_URL', 'https://localhost:9200').rstrip('/')
        self.index = os.getenv('ES_INDEX', 'cards-all')
        ca = os.getenv('ES_CA_CERT')
        self.verify = ssl.create_default_context(cafile=ca)
        self.transport = transport
        self.api_key = os.getenv('ES_API_KEY')
        self.password = os.getenv('ES_PASSWORD')
        self.user = os.getenv('ES_USER', 'elastic')

    def call_with_itf_id(self, itf_id: str, data: dict[str, Any] | None = None,
                         include_sensitive: bool = False) -> dict[str, Any]:
        # Public card catalog: this compatibility flag does not change fields.
        if itf_id != 'EGN00002':
            raise ValueError(f'Unsupported interface: {itf_id}')
        body = build_query(data or {})
        if not self.api_key and self.password is None:
            raise RuntimeError('Set ES_PASSWORD or ES_API_KEY')
        headers = {'Authorization': f'ApiKey {self.api_key}'} if self.api_key else {}
        auth = None if self.api_key else (self.user, self.password)
        with httpx.Client(verify=self.verify, timeout=30, transport=self.transport) as client:
            response = client.post(f'{self.base_url}/{quote(self.index, safe="")}/_search',
                                   json=body, headers=headers, auth=auth)
            try:
                response_body = response.json()
            except ValueError:
                response_body = response.text
            response_logger.info(
                "source=es interface=%s index=%s http_status=%s response=%s",
                itf_id, self.index, response.status_code,
                json.dumps(response_body, ensure_ascii=False, separators=(',', ':')),
            )
            response.raise_for_status()
            result = response_body
        if result.get('timed_out') or result.get('_shards', {}).get('failed', 0):
            raise RuntimeError('Elasticsearch returned incomplete search results')
        hits = result['hits']
        return {'GRID1': [to_mci_card(hit['_source']) for hit in hits['hits']],
                'TO_CT': hits['total']['value']}
