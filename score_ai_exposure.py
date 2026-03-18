from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

SYSTEM_PROMPT = '''
你是一名研究中国就业结构与生成式 AI 影响的分析师。

任务：
1. 根据给定的中国行业描述，评估该行业在未来 3 到 5 年内被生成式 AI、软件自动化、机器人和智能系统改变工作任务的暴露程度。
2. 分值范围为 0 到 10。
   - 0 表示几乎不受影响，主要工作必须在线下、体力或高度现场判断中完成。
   - 5 表示部分任务会被明显重塑，但核心岗位仍需要大量人工执行。
   - 10 表示大量日常任务都可以被 AI、软件代理或自动化系统替代、压缩或显著提效。
3. 只评估任务暴露，不评估行业景气度、政策支持或行业规模。
4. 使用中国语境进行判断，优先考虑这些锚点：
   - 电商运营、直播电商、平台客服、内容生产、销售线索处理
   - 制造业中的工业机器人、机器视觉、MES、质检自动化
   - 交通物流中的智能调度、路线优化、仓储自动化
   - 金融、地产、商务服务中的文档处理、风控辅助、销售支持、报表分析
   - 教育、医疗、政务、公用事业中的行政文书、咨询分诊、知识问答、数字化流程
   - 居民服务、建筑、采矿等强现场和体力岗位的低暴露特征

输出要求：
只返回一个 JSON 对象，不要输出 Markdown，不要输出额外解释。
JSON 格式：
{
  "score": 0-10 的数字,
  "rationale": "3-5 句中文解释，说明哪些任务最容易被 AI 改变、哪些任务仍难替代",
  "anchors": ["2 到 4 个简短中文锚点"],
  "job_description": "2-4 句中文行业工作描述，概括典型岗位和任务"
}
'''.strip()

INDUSTRY_TASK_TEMPLATES = {
    'A040601': '覆盖中国城镇非私营单位整体，就业任务横跨线下服务、制造执行、行政管理和知识工作。',
    'A040602': '典型岗位包括种植养殖、农机操作、农资供应、加工与基层经营管理，工作高度依赖季节、土地和现场操作。',
    'A040603': '典型岗位包括井下作业、露天采掘、安全巡检、选矿加工、设备维护和生产调度，现场安全要求高。',
    'A040604': '典型岗位包括产线操作、工艺工程、质量检测、设备维护、计划排产、采购和工厂管理，既有蓝领现场任务，也有文档与系统流程。',
    'A040605': '典型岗位包括发电供热、燃气和供水运营、设备监控、管网维护、调度值守和安全管理，现场连续运行要求高。',
    'A040606': '典型岗位包括工程施工、测量放线、项目管理、造价预算、材料管理和安全监督，施工现场协同复杂。',
    'A040607': '典型岗位包括司机、调度员、仓储管理员、快递和邮政处理人员、运输计划及网点运营，依赖路线和履约效率。',
    'A040608': '典型岗位包括软件开发、测试、运维、数据分析、产品经理、客服和 IT 解决方案实施，大量工作以数字信息处理为主。',
    'A040609': '典型岗位包括采购、门店销售、渠道运营、电商运营、库存管理、客户服务和市场推广，交易与服务流程标准化程度较高。',
    'A04060A': '典型岗位包括前台接待、客房服务、厨师、服务员、门店运营、供应链管理和平台运营，线下履约和情绪劳动占比高。',
    'A04060B': '典型岗位包括柜面服务、客户经理、投研支持、风控、合规、运营结算和财富管理，文档与规则驱动任务较多。',
    'A04060C': '典型岗位包括经纪销售、招商主管、物业管理、营销策划、估值分析、合同文书和客户跟进，销售与服务并重。',
    'A04060D': '典型岗位包括人力资源、咨询顾问、广告营销、法务辅助、企业服务销售、客户成功和行政外包，文本、沟通和流程工作密集。',
    'A04060E': '典型岗位包括研发工程师、检测检验、设计咨询、实验技术、知识产权服务和科技服务管理，知识密集度较高。',
    'A04060F': '典型岗位包括环保监测、市政设施维护、园林与公园管理、水务巡检、项目管理和公共服务运营，现场与文书并存。',
    'A04060G': '典型岗位包括家政、维修、美容美发、社区服务、洗染、汽车维修接待和门店服务，依赖线下操作和客户互动。',
    'A04060H': '典型岗位包括教师、教研、教务管理、课程运营、培训咨询和内容制作，知识传递与人际互动都很重要。',
    'A04060I': '典型岗位包括医生、护士、药师、康复、社工、挂号收费、病案管理和健康咨询，强监管且临床场景复杂。',
    'A04060J': '典型岗位包括编辑、记者、编导、演员、赛事运营、场馆管理、短视频制作和经纪执行，创意与内容生产并重。',
    'A04060K': '典型岗位包括行政管理、基层政务、社保经办、公共机构运营、文书报送和政策执行，流程型事务较多。',
}

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
INDUSTRIES_JSON = DATA_DIR / 'industries.json'
SCORES_JSON = DATA_DIR / 'scores.json'
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
DASHSCOPE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
DEFAULT_MODEL = 'google/gemini-3-flash-preview'
DEFAULT_DASHSCOPE_MODEL = 'qwen-plus'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Score AI exposure for Chinese industries using OpenRouter.'
    )
    parser.add_argument('--force', action='store_true', help='Re-score industries even if cached.')
    parser.add_argument('--limit', type=int, default=None, help='Only score the first N industries.')
    parser.add_argument('--model', default=None, help='Model name (auto-detected based on provider).')
    parser.add_argument('--provider', default=None, choices=['openrouter', 'dashscope'],
                        help='API provider. Auto-detected from available env keys if not set.')
    return parser.parse_args()


def load_industries() -> List[Dict[str, Any]]:
    if not INDUSTRIES_JSON.exists():
        raise FileNotFoundError(
            f'Missing {INDUSTRIES_JSON}. Run build_dataset.py before scoring.'
        )
    return json.loads(INDUSTRIES_JSON.read_text(encoding='utf-8'))


def load_existing_scores() -> Dict[str, Dict[str, Any]]:
    if not SCORES_JSON.exists():
        return {}

    payload = json.loads(SCORES_JSON.read_text(encoding='utf-8'))
    if isinstance(payload, list):
        return {item['code']: item for item in payload if 'code' in item}
    if isinstance(payload, dict):
        return payload
    return {}


def save_scores(scores_by_code: Dict[str, Dict[str, Any]]) -> None:
    ordered = [scores_by_code[code] for code in sorted(scores_by_code)]
    temp_path = SCORES_JSON.with_suffix('.json.tmp')
    temp_path.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    temp_path.replace(SCORES_JSON)


def build_prompt(industry: Dict[str, Any]) -> str:
    years = sorted(industry.get('yearly_data', {}).keys(), key=int)
    latest_year = years[-1] if years else None
    earliest_year = years[0] if years else None

    latest = industry.get('yearly_data', {}).get(latest_year, {}) if latest_year else {}
    earliest = industry.get('yearly_data', {}).get(earliest_year, {}) if earliest_year else {}
    trend_lines = []

    if earliest_year and latest_year and earliest_year != latest_year:
        if earliest.get('employment') is not None and latest.get('employment') is not None:
            trend_lines.append(
                '就业规模从 {start_year} 年的 {start_value} 变化到 {end_year} 年的 {end_value}（单位：万人）。'.format(
                    start_year=earliest_year,
                    start_value=earliest['employment'],
                    end_year=latest_year,
                    end_value=latest['employment'],
                )
            )
        if earliest.get('avg_wage') is not None and latest.get('avg_wage') is not None:
            trend_lines.append(
                '非私营单位平均工资从 {start_year} 年的 {start_value} 元增长到 {end_year} 年的 {end_value} 元。'.format(
                    start_year=earliest_year,
                    start_value=earliest['avg_wage'],
                    end_year=latest_year,
                    end_value=latest['avg_wage'],
                )
            )

    latest_line = ''
    if latest_year:
        latest_line = (
            '最新年份 {year} 年，就业 {employment} 万人，非私营单位平均工资 {wage} 元，'
            '私营单位平均工资 {private_wage} 元。'
        ).format(
            year=latest_year,
            employment=latest.get('employment'),
            wage=latest.get('avg_wage'),
            private_wage=latest.get('private_avg_wage'),
        )

    description = INDUSTRY_TASK_TEMPLATES.get(
        industry['code'],
        '该行业包含现场执行、行政协调和数字化管理等多种岗位类型。',
    )

    return '\n'.join(
        [
            f'行业代码：{industry["code"]}',
            f'行业名称：{industry["name"]}',
            f'英文名称：{industry["name_en"]}',
            f'行业类别：{industry["category"]}',
            f'是否汇总项：{industry.get("is_aggregate", False)}',
            f'行业工作描述：{description}',
            latest_line,
            *trend_lines,
            '',
            '请基于以上信息，输出指定 JSON。',
        ]
    ).strip()


def extract_json_object(text: str) -> Dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith('{'):
        return json.loads(stripped)

    match = re.search(r'\{.*\}', stripped, re.DOTALL)
    if not match:
        raise ValueError('Model response did not contain a JSON object.')
    return json.loads(match.group(0))


def request_score(
    client: httpx.Client, api_key: str, model: str, industry: Dict[str, Any],
    provider: str = 'openrouter',
) -> Dict[str, Any]:
    api_url = DASHSCOPE_URL if provider == 'dashscope' else OPENROUTER_URL
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    if provider == 'openrouter':
        headers['HTTP-Referer'] = 'https://github.com/karpathy/jobs'
        headers['X-Title'] = 'cn-jobs'

    response = client.post(
        api_url,
        headers=headers,
        json={
            'model': model,
            'response_format': {'type': 'json_object'},
            'messages': [
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': build_prompt(industry)},
            ],
            'temperature': 0.2,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()

    choices = payload.get('choices') or []
    if not choices:
        raise ValueError('OpenRouter response did not include any choices.')

    message = choices[0].get('message') or {}
    content = message.get('content')
    if isinstance(content, list):
        joined = ''.join(
            part.get('text', '') if isinstance(part, dict) else str(part) for part in content
        )
    else:
        joined = str(content or '')

    parsed = extract_json_object(joined)
    score = parsed.get('score')
    if score is None:
        raise ValueError('Model response did not contain a score.')

    return {
        'code': industry['code'],
        'name': industry['name'],
        'name_en': industry['name_en'],
        'category': industry['category'],
        'model': model,
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'score': float(score),
        'rationale': parsed.get('rationale', ''),
        'anchors': parsed.get('anchors', []),
        'job_description': parsed.get('job_description', ''),
        'generated_prompt': build_prompt(industry),
    }


def main() -> None:
    args = parse_args()
    load_dotenv(BASE_DIR / '.env')
    # Also check parent directories for .env (convenient for monorepo setups)
    for parent in BASE_DIR.parents:
        candidate = parent / '.env'
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break

    # Auto-detect provider
    provider = args.provider
    api_key = None
    if provider == 'dashscope' or (provider is None and os.getenv('DASHSCOPE_API_KEY')):
        api_key = os.getenv('DASHSCOPE_API_KEY')
        provider = 'dashscope'
    elif provider == 'openrouter' or (provider is None and os.getenv('OPENROUTER_API_KEY')):
        api_key = os.getenv('OPENROUTER_API_KEY')
        provider = 'openrouter'

    if not api_key:
        raise RuntimeError(
            'No API key found. Set DASHSCOPE_API_KEY or OPENROUTER_API_KEY in .env or environment.'
        )

    industries = load_industries()
    if args.limit is not None:
        industries = industries[: args.limit]

    scores_by_code = load_existing_scores()
    client = httpx.Client(timeout=90.0)

    try:
        for industry in industries:
            code = industry['code']
            if industry.get('is_aggregate'):
                if args.force or code not in scores_by_code:
                    scores_by_code[code] = {
                        'code': code,
                        'name': industry['name'],
                        'name_en': industry['name_en'],
                        'category': industry['category'],
                        'model': 'rule-based',
                        'updated_at': datetime.now(timezone.utc).isoformat(),
                        'score': None,
                        'rationale': '汇总项代表全部城镇单位，不适合作为单一行业评估 AI 暴露度。',
                        'anchors': ['汇总行业', '不单独评分'],
                        'job_description': INDUSTRY_TASK_TEMPLATES.get(code, ''),
                        'generated_prompt': build_prompt(industry),
                    }
                    save_scores(scores_by_code)
                continue

            if not args.force and code in scores_by_code and scores_by_code[code].get('score') is not None:
                continue

            model = args.model or (DEFAULT_DASHSCOPE_MODEL if provider == 'dashscope' else DEFAULT_MODEL)
            result = request_score(client, api_key, model, industry, provider=provider)
            scores_by_code[code] = result
            save_scores(scores_by_code)
            print(f'Scored {code} {industry["name"]}: {result["score"]}')
    except KeyboardInterrupt:
        save_scores(scores_by_code)
        raise
    finally:
        client.close()

    print(f'Wrote {len(scores_by_code)} score records to {SCORES_JSON}')


if __name__ == '__main__':
    main()
