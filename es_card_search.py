"""Standalone card-search pilot; does not import or change the existing server.

Required environment:
  export ES_CA_CERT='/Users/js/IdeaProjects/es/elasticsearch-9.5.3/config/certs/http_ca.crt'
  export ES_USER=elastic
  read -s 'ES_PASSWORD?ES password: '; export ES_PASSWORD

Run with project virtualenv:
  .venv/bin/python es_card_search.py --name '신한카드 처음'
  .venv/bin/python es_card_search.py --service-code 8 --max-fee 20000
  .venv/bin/python es_card_search.py --name '신한카드 처음' --widget
  .venv/bin/python es_card_search.py --serve --port 8081

The standalone MCP endpoint is http://127.0.0.1:8081/mcp and registers only
getCreditCardDetail(cardName). CLI searches return EGN00002 GRID1/TO_CT JSON.
Service codes and fee constraints are available through CLI/EsCardClient;
recommendation and popular-card tools are not registered in this pilot.
Date sorting follows the existing pageid-desc convention, not a release date.
"""
from __future__ import annotations

import argparse
import json
from mci.es_card_client import EsCardClient


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--name', default='')
    p.add_argument('--service-code', default='')
    p.add_argument('--min-fee', type=int, default=0)
    p.add_argument('--max-fee', type=int, default=5_000_000)
    p.add_argument('--size', type=int, default=5)
    p.add_argument('--sort', choices=['score', 'date', 'high_rate', 'low_rate'], default='score')
    p.add_argument('--widget', action='store_true')
    p.add_argument('--serve', action='store_true')
    p.add_argument('--port', type=int, default=8081)
    a = p.parse_args()
    client = EsCardClient()
    if a.serve:
        from fastmcp import FastMCP
        from tools.es_card_search_tools import register_es_card_search_tools
        mcp = FastMCP('shinhan-es-card-search')
        register_es_card_search_tools(mcp, client)
        mcp.run(transport='http', host='127.0.0.1', port=a.port, path='/mcp',
                stateless_http=True, json_response=True)
    elif a.widget:
        if a.service_code or a.min_fee != 0 or a.max_fee != 5_000_000:
            p.error('--widget supports card name only; use JSON mode for filters')
        from tools.es_card_search_tools import search_card_detail
        print(search_card_detail(client, a.name))
    else:
        result = client.call_with_itf_id('EGN00002', data={
            'MSG': a.name, 'CRD_BNF': a.service_code, 'SIZ': a.size, 'QEE': a.sort,
            'AFE_MIN_VL': a.min_fee, 'AFE_MAX_VL': a.max_fee,
        })
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
