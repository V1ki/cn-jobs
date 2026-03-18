from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
SITE_DIR = BASE_DIR / 'site'
INDUSTRIES_JSON = DATA_DIR / 'industries.json'
SCORES_JSON = DATA_DIR / 'scores.json'
SITE_DATA_JSON = SITE_DIR / 'data.json'
SITE_SUMMARY_JSON = SITE_DIR / 'summary.json'


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f'Missing input file: {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def latest_year_value(industry: Dict[str, Any], field_name: str):
    years = sorted(industry.get('yearly_data', {}).keys(), key=int)
    for year in reversed(years):
        value = industry.get('yearly_data', {}).get(year, {}).get(field_name)
        if value is not None:
            return year, value
    return None, None


def build_site_payload(
    industries: List[Dict[str, Any]], scores: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    score_map = {item['code']: item for item in scores if 'code' in item}
    payload = []

    for industry in industries:
        score_entry = score_map.get(industry['code'], {})
        yearly_data = {}
        for year, values in industry.get('yearly_data', {}).items():
            yearly_data[year] = {
                'employment': values.get('employment'),
                'wage': values.get('avg_wage'),
                'private_wage': values.get('private_avg_wage'),
                'employment_change_pct': values.get('employment_change_pct'),
                'wage_growth_pct': values.get('wage_growth_pct'),
                'private_wage_growth_pct': values.get('private_wage_growth_pct'),
            }
        payload.append(
            {
                'code': industry['code'],
                'title': industry['name'],
                'title_en': industry['name_en'],
                'category': industry['category'],
                'is_aggregate': industry.get('is_aggregate', False),
                'yearly_data': yearly_data,
                'ai_exposure': {
                    'score': score_entry.get('score'),
                    'rationale': score_entry.get('rationale'),
                    'anchors': score_entry.get('anchors', []),
                    'job_description': score_entry.get('job_description'),
                    'model': score_entry.get('model'),
                    'updated_at': score_entry.get('updated_at'),
                },
            }
        )

    return payload


def build_summary(site_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    years = sorted(
        {
            year
            for industry in site_payload
            for year in industry.get('yearly_data', {}).keys()
        },
        key=int,
    )
    latest_year = years[-1] if years else None

    categories: Dict[str, int] = {}
    latest_scores = []
    latest_wages = []
    latest_employment = []
    aggregate_record = None

    for industry in site_payload:
        category = industry['category']
        categories[category] = categories.get(category, 0) + 1

        if industry.get('is_aggregate'):
            aggregate_record = industry

        score = industry.get('ai_exposure', {}).get('score')
        if score is not None and not industry.get('is_aggregate'):
            latest_scores.append(
                {
                    'code': industry['code'],
                    'title': industry['title'],
                    'score': score,
                }
            )

        wage_year, wage_value = latest_year_value(industry, 'wage')
        if wage_value is not None and not industry.get('is_aggregate'):
            latest_wages.append(
                {
                    'code': industry['code'],
                    'title': industry['title'],
                    'year': wage_year,
                    'wage': wage_value,
                }
            )

        employment_year, employment_value = latest_year_value(industry, 'employment')
        if employment_value is not None and not industry.get('is_aggregate'):
            latest_employment.append(
                {
                    'code': industry['code'],
                    'title': industry['title'],
                    'year': employment_year,
                    'employment': employment_value,
                }
            )

    latest_scores.sort(key=lambda item: item['score'], reverse=True)
    latest_wages.sort(key=lambda item: item['wage'], reverse=True)
    latest_employment.sort(key=lambda item: item['employment'], reverse=True)

    total_employment = None
    total_avg_wage = None
    if aggregate_record and latest_year:
        aggregate_year = aggregate_record.get('yearly_data', {}).get(latest_year, {})
        total_employment = aggregate_year.get('employment')
        total_avg_wage = aggregate_year.get('wage')

    average_ai_exposure = None
    if latest_scores:
        average_ai_exposure = round(
            sum(float(item['score']) for item in latest_scores) / len(latest_scores),
            2,
        )

    return {
        'generated_at': generated_at,
        'industry_count': len(site_payload),
        'years_covered': years,
        'latest_year': latest_year,
        'category_counts': categories,
        'average_ai_exposure': average_ai_exposure,
        'top_ai_exposure': latest_scores[:5],
        'top_wages_latest': latest_wages[:5],
        'top_employment_latest': latest_employment[:5],
        'latest_totals': {
            'employment': total_employment,
            'avg_wage': total_avg_wage,
        },
    }


def main() -> None:
    industries = load_json(INDUSTRIES_JSON)
    scores = load_json(SCORES_JSON)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    site_payload = build_site_payload(industries, scores)
    summary_payload = build_summary(site_payload)

    SITE_DATA_JSON.write_text(
        json.dumps(site_payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    SITE_SUMMARY_JSON.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f'Wrote {SITE_DATA_JSON}')
    print(f'Wrote {SITE_SUMMARY_JSON}')


if __name__ == '__main__':
    main()
