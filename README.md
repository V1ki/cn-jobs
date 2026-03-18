# cn-jobs 🇨🇳

中国就业市场可视化与 AI 暴露度评估，灵感来自 [karpathy/jobs](https://github.com/karpathy/jobs)。

基于国家统计局 2006–2024 年的行业数据，用 Squarified Treemap 展示 19 个国民经济行业门类的就业规模、薪资水平和 AI 暴露度。

## Live Demo

👉 **[jobs.v1ki.cc](https://jobs.v1ki.cc)**

## Screenshots

| AI 暴露度 | 平均工资 |
|-----------|---------|
| ![AI Exposure](docs/treemap-ai.png) | ![Wage](docs/treemap-wage.png) |

| 就业变化 | 历史对比 (2010) |
|---------|----------------|
| ![Change](docs/treemap-change.png) | ![2010](docs/treemap-2010.png) |

## Data Sources

| 数据 | 来源 | 指标代码 | 单位 |
|------|------|----------|------|
| 就业人数 | 国家统计局年度数据 | A0406xx | 万人 |
| 非私营单位平均工资 | 国家统计局年度数据 | A040Ixx | 元/年 |
| 私营单位平均工资 | 国家统计局年度数据 | A040Mxx | 元/年 |

API: `https://data.stats.gov.cn/easyquery.htm`

## Quick Start

```bash
pip install httpx python-dotenv

# 1. Scrape stats (cached, safe to re-run)
python scrape_stats.py

# 2. Merge employment + wage data
python build_dataset.py

# 3. AI exposure scoring (requires API key, see below)
python score_ai_exposure.py

# 4. Build frontend data
python build_site_data.py

# 5. Local preview
cd site && python -m http.server 8080
```

## AI Scoring Setup

```bash
cp .env.example .env
# Edit .env and add your API key
```

| Provider | Env Var | Default Model |
|----------|---------|---------------|
| DashScope (Alibaba Cloud) | `DASHSCOPE_API_KEY` | qwen-plus |
| OpenRouter | `OPENROUTER_API_KEY` | google/gemini-3-flash-preview |

## Visualization Modes

- **AI 暴露度** — 0-10, red = higher exposure
- **平均工资** — Log scale, shows wage gap across industries
- **就业变化** — YoY employment change, green = growth
- **工资增长** — YoY wage growth rate

Year slider covers 2006–2024.

## Methodology

AI exposure score (0-10) measures "how much AI will reshape this industry", NOT "will this industry disappear".

- 0-1: Physical on-site work (farming, construction)
- 4-5: Hybrid (healthcare, public administration)
- 8-9: Highly digital (software, finance)
- 10: Pure information processing

> ⚠️ A high score does not predict job loss. The score does not account for demand elasticity, latent demand, regulatory barriers, or social preferences for human workers.

## Project Structure

```text
cn-jobs/
├── scrape_stats.py          # NBS API scraper
├── build_dataset.py         # Data merging & metrics
├── score_ai_exposure.py     # LLM-based AI exposure scoring
├── build_site_data.py       # Frontend JSON builder
├── industry_metadata.py     # Industry metadata
├── data/                    # Processed data
├── raw/                     # NBS API response cache
├── site/                    # Frontend (single HTML + JSON)
│   └── index.html           # Squarified Treemap app
└── docs/                    # Screenshots for README
```

## Credits

- [karpathy/jobs](https://github.com/karpathy/jobs) — Inspiration & methodology
- [国家统计局](https://data.stats.gov.cn/) — Data source

## License

MIT
