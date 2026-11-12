# benchmarking

[![Live report](https://img.shields.io/badge/📊_Live_report-yuzhangoscar.github.io%2Fbenchmarking-2ea44f?style=for-the-badge)](https://yuzhangoscar.github.io/benchmarking/)
[![Gemini eval](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml/badge.svg)](https://github.com/yuzhangoscar/benchmarking/actions/workflows/gemini-eval.yml)

Automated evaluation of Google's **Gemini Flash** model. A small set of test prompts is sent to the
model on every push, every three days, and on demand. Each answer is graded either against an expected
result or by an LLM judge against written criteria, and the outcome is published as a public web page.

**👉 Latest results: <https://yuzhangoscar.github.io/benchmarking/>**

## Why

Model behaviour changes over time: new versions are released, aliases move, and capacity or quota
problems come and go. Running the same tests on a schedule gives a simple, shareable record of whether
the model still answers the way you expect, and how fast.

## How it works

1. **GitHub Actions** starts the `Gemini eval` workflow: on push to `main`, every three days at 00:00 UTC
   (11:00 Sydney time during daylight saving), or manually. The schedule runs on days 1, 4, 7, … 31 of
   each month, so at a month's end the gap can be one or two days instead of three.
2. **`run_eval.py`** checks the chosen model is available to the API key, then sends each prompt in
   `cases.jsonl` to Gemini.
3. Each answer is graded by its test's **evaluation category** (see below).
4. The script downloads the previously published `history.json`, appends this run, and writes
   `index.html`, `results.json` and `history.json`, which **GitHub Pages** publishes.

## Evaluation categories

Every test has a `category` that decides how its answer is graded. The report shows each test's
category and a pass count per category.

| Category | Label | How an answer passes | Requests per test | Tests |
|---|---|---|---|---|
| `exact` | Exact Evaluation | The expected text appears in the answer (case-insensitive) | 1 | `capital`, `math`, `json` |
| `llm_judge` | LLM as a Judge | A judge model grades the answer against each criterion | 2 | `explain-recursion`, `decline-email`, `faithful-summary`, `unknown-book`, `battery-disposal` |

A test with a missing or unknown category, or missing fields, stops the run before any Gemini request is made.

### LLM as a Judge

For open-ended tasks with no single right answer:

1. The model under test answers the test's `topic`.
2. The **judge model** receives the topic, the answer and the criteria, and returns a verdict for each
   criterion (met or not, a quote from the answer as evidence, and a reason) as structured JSON at
   temperature 0.
3. Word limits (`max_words`) are counted in code, not by the judge, and always count as required.
4. **Score** = criteria met ÷ all criteria. The test **passes** if every required criterion is met and
   the score reaches `pass_threshold` (default 1.0, meaning every criterion).

By default the judge is the model under test, so Gemini grades its own answers. Models tend to rate
their own writing generously, so set `GEMINI_JUDGE_MODEL` (or the **judge model** box when running the
workflow manually) to use a different judge. If the judge request fails, or it skips or invents
criteria, the test counts as an **API error** (grey), not a failure.

The report shows each criterion as ✓ or ✗ with the judge's reason, and charts the category's average
score over time.

## Trend over time

The report page charts every run (up to the last 500):

- **Pass rate**, **LLM as a Judge average score** and **average response time**, with one line per model
  and a red ✕ for runs that hit API errors.
- **A grid of each test across the last 30 runs**: green passed, red failed, grey API error.

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
most recent run. The script also uses `pydantic` (installed with `google-genai`) for the judge's output
schema; everything else comes from the Python standard library. Chart.js is loaded by the browser, not installed.

## Project structure

```
.github/workflows/gemini-eval.yml   CI workflow: run the eval, then deploy to GitHub Pages
gemini/evals/cases.jsonl            Test cases, one JSON object per line
gemini/evals/run_eval.py            Calls Gemini, grades answers by category, writes the HTML report
```

## Adding a test case

Add a line to `gemini/evals/cases.jsonl`:

```json
{"id": "capital", "category": "exact", "prompt": "What is the capital of Australia? Answer with one word.", "expected": "Canberra"}
```

For `exact` tests, `expected` is matched as a substring of the answer, so ask for short, specific answers.

An `llm_judge` test gives a `topic` and a list of `criteria` (written on one line in the file; spread out here):

```json
{
  "id": "decline-email",
  "category": "llm_judge",
  "topic": "Write a short email to a colleague named Sam declining a meeting on Friday at 3pm and proposing two alternative times.",
  "max_words": 100,
  "criteria": [
    {"id": "polite", "description": "The tone is polite and professional", "required": true},
    {"id": "two-times", "description": "Proposes exactly two specific alternative times (day and time)", "required": true},
    {"id": "no-over-apology", "description": "Apologises at most once"}
  ],
  "pass_threshold": 0.75
}
```

| Field | Meaning |
|---|---|
| `topic` | The request sent to the model under test |
| `criteria[].id` / `description` | A short name and one specific, checkable statement. Avoid vague words like "good" |
| `criteria[].required` | Failing it fails the test whatever the score (default `false`) |
| `max_words` | Optional word limit, checked in code |
| `pass_threshold` | Fraction of criteria that must be met, between 0 and 1 (default `1.0`) |

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
| `GEMINI_JUDGE_MODEL` | Workflow input or env var | Model that grades `llm_judge` tests; defaults to `GEMINI_MODEL` |
| Pages source | Settings → Pages → **GitHub Actions** | Required for the report to be published |

> The report is public. Don't put private data in test prompts.
