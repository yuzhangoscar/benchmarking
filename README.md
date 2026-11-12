# benchmarking

[![Live report](https://img.shields.io/badge/📊_Live_report-yuzhangoscar.github.io%2Fbenchmarking-2ea44f?style=for-the-badge)](https://yuzhangoscar.github.io/benchmarking/)
[![Gemini eval](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml/badge.svg)](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml)

![Gemini](https://img.shields.io/badge/gemini--3.8--flash-8E75B2?logo=googlegemini&logoColor=white)
![google-genai](https://img.shields.io/badge/google--genai-3.2.0-4285F4?logo=google&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Chart.js](https://img.shields.io/badge/Chart.js-4-FF6384?logo=chartdotjs&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-222222?logo=githubpages&logoColor=white)

Tests Gemini Flash on a schedule and publishes the results, with trends over time, to
**<https://yuzhangoscar.github.io/benchmarking/>**.

Runs on every push to `main`, every three days at 00:00 UTC, and on demand
([Run workflow](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml)).

## Evaluation categories

| Category | Passes when | Requests per test |
|---|---|---|
| `exact` (Exact Evaluation) | The expected text appears in the answer | 1 |
| `llm_judge` (LLM as a Judge) | A judge model finds every required criterion met and the score ≥ `pass_threshold` | 2 |

## Adding a test

One JSON object per line in `gemini/evals/cases.jsonl`:

```json
{"id": "capital", "category": "exact", "prompt": "What is the capital of Australia? One word.", "expected": "Canberra"}
{"id": "email", "category": "llm_judge", "topic": "Write a short email declining a Friday meeting.", "max_words": 100, "pass_threshold": 0.75,
 "criteria": [{"id": "polite", "description": "Polite and professional", "required": true}, {"id": "declines", "description": "Clearly declines the meeting"}]}
```

`llm_judge` fields: `criteria[].required` (default `false`), `max_words` (optional, checked in code),
`pass_threshold` (default `1.0`). In the file, each test must be on a single line.

## Configuration

| Setting | Purpose |
|---|---|
| `GEMINI_API_KEY` | Secret in the `SIMPLE` environment |
| `GEMINI_MODEL` | Model to test (default `gemini-3.8-flash`) |
| `GEMINI_JUDGE_MODEL` | Model that grades `llm_judge` tests (default: same as `GEMINI_MODEL`) |

Both model settings can also be set from the **Run workflow** form. Pages must be set to deploy from **GitHub Actions**.

## Run locally

```bash
cd gemini && pip install google-genai
GEMINI_API_KEY=your-key python evals/run_eval.py && open site/index.html
```

> The report is public. Don't put private data in tests.
