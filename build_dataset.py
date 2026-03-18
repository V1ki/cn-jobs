from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from industry_metadata import INDUSTRIES

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
EMPLOYMENT_CSV = DATA_DIR / 'employment_by_industry.csv'
WAGES_CSV = DATA_DIR / 'wages_by_industry.csv'
OUTPUT_JSON = DATA_DIR / 'industries.json'


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f'Missing input file: {path}')

    with path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def to_number(value: str):
    text = str(value).strip()
    if not text:
        return None
    number = float(text)
    if number.is_integer():
        return int(number)
    return number


def pct_change(previous_value: Any, current_value: Any):
    if previous_value in (None, 0) or current_value is None:
        return None
    return round(((float(current_value) - float(previous_value)) / float(previous_value)) * 100, 2)


def merge_rows() -> List[Dict[str, Any]]:
    employment_rows = read_csv_rows(EMPLOYMENT_CSV)
    wage_rows = read_csv_rows(WAGES_CSV)

    employment_map: Dict[str, Dict[int, Any]] = {}
    wages_map: Dict[str, Dict[str, Dict[int, Any]]] = {}

    for row in employment_rows:
        code = row['industry_code']
        year = int(row['year'])
        employment_map.setdefault(code, {})[year] = to_number(row['value'])

    for row in wage_rows:
        code = row['industry_code']
        wage_type = row['wage_type']
        year = int(row['year'])
        wages_map.setdefault(code, {}).setdefault(wage_type, {})[year] = to_number(row['value'])

    output: List[Dict[str, Any]] = []
    for industry in INDUSTRIES:
        code = industry['employment_code']
        years = sorted(
            set(employment_map.get(code, {}).keys())
            | set(wages_map.get(code, {}).get('non_private', {}).keys())
            | set(wages_map.get(code, {}).get('private', {}).keys())
        )

        yearly_data: Dict[str, Dict[str, Any]] = {}
        previous_employment = None
        previous_non_private_wage = None
        previous_private_wage = None

        for year in years:
            employment = employment_map.get(code, {}).get(year)
            avg_wage = wages_map.get(code, {}).get('non_private', {}).get(year)
            private_avg_wage = wages_map.get(code, {}).get('private', {}).get(year)

            yearly_data[str(year)] = {
                'employment': employment,
                'avg_wage': avg_wage,
                'private_avg_wage': private_avg_wage,
                'employment_change_pct': pct_change(previous_employment, employment),
                'wage_growth_pct': pct_change(previous_non_private_wage, avg_wage),
                'private_wage_growth_pct': pct_change(previous_private_wage, private_avg_wage),
            }

            if employment is not None:
                previous_employment = employment
            if avg_wage is not None:
                previous_non_private_wage = avg_wage
            if private_avg_wage is not None:
                previous_private_wage = private_avg_wage

        output.append(
            {
                'code': code,
                'name': industry['name'],
                'name_en': industry['name_en'],
                'category': industry['category'],
                'is_aggregate': industry['is_aggregate'],
                'yearly_data': yearly_data,
            }
        )

    return output


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    industries = merge_rows()
    OUTPUT_JSON.write_text(
        json.dumps(industries, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f'Wrote {len(industries)} industries to {OUTPUT_JSON}')


if __name__ == '__main__':
    main()
