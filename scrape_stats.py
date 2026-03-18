from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx

from industry_metadata import (
    EMPLOYMENT_CODES,
    INDUSTRY_BY_ANY_CODE,
    NON_PRIVATE_WAGE_CODES,
    PRIVATE_WAGE_CODES,
    clean_indicator_name,
)

API_URL = 'https://data.stats.gov.cn/easyquery.htm'
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / 'raw'
DATA_DIR = BASE_DIR / 'data'
TIME_RANGE = 'LAST20'
REQUEST_DELAY_SECONDS = 1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Scrape Chinese employment and wage data from data.stats.gov.cn'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch remote payloads even when cached files already exist.',
    )
    return parser.parse_args()


def build_params(indicator_code: str) -> Dict[str, str]:
    return {
        'm': 'QueryData',
        'dbcode': 'hgnd',
        'rowcode': 'zb',
        'colcode': 'sj',
        'wds': '[]',
        'dfwds': json.dumps(
            [
                {'wdcode': 'zb', 'valuecode': indicator_code},
                {'wdcode': 'sj', 'valuecode': TIME_RANGE},
            ],
            ensure_ascii=False,
            separators=(',', ':'),
        ),
        'k1': str(int(time.time() * 1000)),
    }


def raw_path_for(indicator_code: str) -> Path:
    return RAW_DIR / f'{indicator_code}_{TIME_RANGE}.json'


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Referer': 'https://data.stats.gov.cn/easyquery.htm?cn=C01',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'X-Requested-With': 'XMLHttpRequest',
}

MAX_RETRIES = 3


def fetch_indicator(
    client: httpx.Client, indicator_code: str, force: bool = False
) -> Dict[str, Any]:
    raw_path = raw_path_for(indicator_code)
    if raw_path.exists() and not force:
        return json.loads(raw_path.read_text(encoding='utf-8'))

    params = build_params(indicator_code)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.get(API_URL, params=params, headers=HEADERS, timeout=30.0)
            response.raise_for_status()
            payload = response.json()
            break
        except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError) as exc:
            if attempt == MAX_RETRIES:
                raise
            print(f'  Retry {attempt}/{MAX_RETRIES} for {indicator_code}: {exc}')
            time.sleep(2.0 * attempt)
    raw_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    time.sleep(REQUEST_DELAY_SECONDS)
    return payload


def build_lookup(returndata: Dict[str, Any], wdcode: str, use_cname: bool = True) -> Dict[str, str]:
    for wdnode in returndata.get('wdnodes', []):
        if wdnode.get('wdcode') != wdcode:
            continue
        return {
            node.get('code'): (node.get('cname') if use_cname else node.get('code'))
            for node in wdnode.get('nodes', [])
            if node.get('code')
        }
    return {}


def parse_numeric(value: Any):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value

    text = str(value).strip().replace(',', '')
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def parse_payload(payload: Dict[str, Any], series_kind: str) -> List[Dict[str, Any]]:
    returndata = payload.get('returndata') or {}
    year_lookup = build_lookup(returndata, 'sj', use_cname=False)  # year codes are "2024", cnames are "2024年"
    name_lookup = build_lookup(returndata, 'zb', use_cname=True)
    rows: List[Dict[str, Any]] = []

    for datanode in returndata.get('datanodes', []):
        data_payload = datanode.get('data') or {}
        if data_payload.get('hasdata') is False:
            continue

        raw_value = data_payload.get('data')
        value = parse_numeric(raw_value)
        if value is None:
            continue

        wd_map = {
            item.get('wdcode'): item.get('valuecode')
            for item in datanode.get('wds', [])
            if item.get('wdcode')
        }
        indicator_code = wd_map.get('zb')
        year_code = wd_map.get('sj')
        if not indicator_code or not year_code:
            continue

        industry = INDUSTRY_BY_ANY_CODE.get(indicator_code)
        if industry is None:
            fallback_name = clean_indicator_name(name_lookup.get(indicator_code, indicator_code))
            industry = {
                'employment_code': indicator_code,
                'name': fallback_name or indicator_code,
            }

        row = {
            'industry_code': industry['employment_code'],
            'industry_name': industry['name'],
            'year': year_lookup.get(year_code, year_code),
            'value': value,
        }
        if series_kind != 'employment':
            row['wage_type'] = series_kind
        rows.append(row)

    rows.sort(key=lambda item: (item['industry_code'], int(item['year'])))
    return rows


def write_csv(path: Path, fieldnames: List[str], rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fetch_all(force: bool = False) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    employment_rows: List[Dict[str, Any]] = []
    wage_rows: List[Dict[str, Any]] = []

    headers = {
        'User-Agent': 'cn-jobs/0.1 (+https://data.stats.gov.cn)',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'{API_URL}?{urlencode(build_params("A040601"))}',
    }

    with httpx.Client(timeout=30.0, headers=headers, follow_redirects=True) as client:
        for indicator_code in EMPLOYMENT_CODES:
            payload = fetch_indicator(client, indicator_code, force=force)
            employment_rows.extend(parse_payload(payload, 'employment'))

        for indicator_code in NON_PRIVATE_WAGE_CODES:
            payload = fetch_indicator(client, indicator_code, force=force)
            wage_rows.extend(parse_payload(payload, 'non_private'))

        for indicator_code in PRIVATE_WAGE_CODES:
            payload = fetch_indicator(client, indicator_code, force=force)
            wage_rows.extend(parse_payload(payload, 'private'))

    write_csv(
        DATA_DIR / 'employment_by_industry.csv',
        ['industry_code', 'industry_name', 'year', 'value'],
        employment_rows,
    )
    write_csv(
        DATA_DIR / 'wages_by_industry.csv',
        ['industry_code', 'industry_name', 'wage_type', 'year', 'value'],
        wage_rows,
    )

    print(
        'Wrote {employment_count} employment rows and {wage_count} wage rows.'.format(
            employment_count=len(employment_rows),
            wage_count=len(wage_rows),
        )
    )


def main() -> None:
    args = parse_args()
    fetch_all(force=args.force)


if __name__ == '__main__':
    main()
