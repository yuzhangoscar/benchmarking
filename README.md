# benchmarking

[![Live report](https://img.shields.io/badge/📊_Live_report-yuzhangoscar.github.io%2Fbenchmarking-2ea44f?style=for-the-badge)](https://yuzhangoscar.github.io/benchmarking/)
[![Gemini eval](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml/badge.svg)](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml)

Automated evaluation of Google's **Gemini Flash** model. A small set of test prompts is sent to the
model on every push, every day, and on demand; each answer is graded against an expected result, and
the outcome is published as a public web page.

**👉 Latest results: <https://yuzhangoscar.github.io/benchmarking/>**

## Why

Model behaviour changes over time: new versions are released, aliases move, and capacity or quota
problems come and go. Running the same tests on a schedule gives a simple, shareable record of whether
the model still answers the way you expect, and how fast.

## How it works

1. **GitHub Actions** starts the `Gemini eval` workflow (on push to `main`, daily at 00:00 UTC, or manually).
2. **`run_eval.py`** checks the chosen model is available to the API key, then sends each prompt in
   `cases.jsonl` to Gemini.
3. Each answer **passes** if it contains the expected text (case-insensitive).
4. The script downloads the previously published `history.json`, appends this run, and writes
   `index.html`, `results.json` and `history.json`, which **GitHub Pages** publishes.

## Trend over time

The report page charts every run (up to the last 500):

- **Pass rate** and **average response time**, with one line per model and a red ✕ for runs that hit API errors.
- **A grid of each test across the last 30 runs**: green passed, red wrong answer, grey API error.

API errors (outages, quota limits) mark the CI run as failed but are still published, so outages show
up in the trend. If the history can't be downloaded, or the model doesn't exist, nothing is published,
so the history is never overwritten. The raw data is at
[`history.json`](https://yuzhangoscar.github.io/benchmarking/history.json).

## Modules and versions

| | Module | Version | Role |
|---|---|---|---|
| <img src="https://cdn.simpleicons.org/googlegemini" width="20"> | Gemini model | `gemini-3.8-flash` | Model under test (override per run) |
| <img src="https://cdn.simpleicons.org/google" width="20"> | [`google-genai`](https://pypi.org/project/google-genai/) | 3.2.0 | Python SDK for the Gemini API |
| <img src="https://cdn.simpleicons.org/python" width="20"> | Python | 3.12 | Runs the eval script |
| <img src="https://cdn.simpleicons.org/chartdotjs" width="20"> | [Chart.js](https://www.chartjs.org/) | 4.x (CDN) | Trend charts on the report page |
| <img src="https://cdn.simpleicons.org/githubactions" width="20"> | [`actions/checkout`](https://github.com/actions/checkout) | v4 | Checks out the repo |
| <img src="https://cdn.simpleicons.org/githubactions" width="20"> | [`actions/setup-python`](https://github.com/actions/setup-python) | v5 | Installs Python |
| <img src="https://cdn.simpleicons.org/githubpages" width="20"> | [`actions/upload-pages-artifact`](https://github.com/actions/upload-pages-artifact) | v3 | Packages the report |
| <img src="https://cdn.simpleicons.org/githubpages" width="20"> | [`actions/configure-pages`](https://github.com/actions/configure-pages) | v5 | Prepares GitHub Pages |
| <img src="https://cdn.simpleicons.org/githubpages" width="20"> | [`actions/deploy-pages`](https://github.com/actions/deploy-pages) | v4 | Publishes the report |
| <img src="https://cdn.simpleicons.org/ubuntu" width="20"> | Runner | `ubuntu-latest` (Ubuntu 26.04) | CI machine |

`google-genai` is installed unpinned, so CI uses the latest release; 3.2.0 is the version used by the
most recent run. Everything else in the script comes from the Python standard library; Chart.js is
loaded by the browser, not installed.

## Project structure

```
.github/workflows/gemini-eval.yml   CI workflow: run the eval, then deploy to GitHub Pages
gemini/evals/cases.jsonl            Test cases, one JSON object per line
gemini/evals/run_eval.py            Calls Gemini, grades answers, writes the HTML report
```

## Adding a test case

Add a line to `gemini/evals/cases.jsonl`:

```json
{"id": "capital", "prompt": "What is the capital of Australia? Answer with one word.", "expected": "Canberra"}
```

`expected` is matched as a substring of the answer, so ask for short, specific answers.

## Running it

**On GitHub:** open the [Gemini eval workflow](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml),
click **Run workflow**, and optionally enter a different model ID (e.g. `gemini-2.5-flash`).

**Locally:**

```bash
cd gemini
pip install google-genai
GEMINI_API_KEY=your-key python evals/run_eval.py   # optional: GEMINI_MODEL=gemini-2.5-flash
open site/index.html
```

## Configuration

| Setting | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Secret in the `SIMPLE` environment | Gemini API key ([get one](https://aistudio.google.com/apikey)) |
| `GEMINI_MODEL` | Workflow input or env var | Model to test; defaults to `gemini-3.8-flash` |
| Pages source | Settings → Pages → **GitHub Actions** | Required for the report to be published |

> The report is public. Don't put private data in test prompts.
