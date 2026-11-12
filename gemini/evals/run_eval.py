import html, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path
from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
# The published history.json from the previous run; unset when running locally.
HISTORY_URL = os.environ.get("HISTORY_URL")
MAX_HISTORY = 500


def load_history() -> list[dict]:
    if not HISTORY_URL:
        return []
    try:
        # The query string bypasses the Pages CDN cache, so back-to-back runs see each other.
        with urllib.request.urlopen(f"{HISTORY_URL}?t={int(time.time())}", timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("No published history yet; starting a new one.")
            return []
        raise


# Fail before calling the model if history can't be read: publishing without it would erase the trend.
history = load_history()
print(f"Loaded {len(history)} previous run(s).")

# Reads GEMINI_API_KEY from the environment. Without a timeout a stuck request hangs the CI job.
client = genai.Client(http_options=types.HttpOptions(timeout=60_000, retry_options=types.HttpRetryOptions(attempts=2)))

available = sorted(
    m.name.removeprefix("models/")
    for m in client.models.list()
    if "generateContent" in (m.supported_actions or [])
)
print("Flash models available to this key:", ", ".join(n for n in available if "flash" in n))
if MODEL not in available:
    sys.exit(f"Model '{MODEL}' is not available to this API key. Set GEMINI_MODEL to one of the models listed above.")

cases = [json.loads(l) for l in Path("evals/cases.jsonl").read_text().splitlines() if l.strip()]
results = []
for case in cases:
    start = time.perf_counter()
    try:
        answer, error = client.models.generate_content(model=MODEL, contents=case["prompt"]).text or "", False
    except Exception as e:
        answer, error = f"ERROR: {e}", True
    seconds = round(time.perf_counter() - start, 2)
    status = "error" if error else "pass" if case["expected"].lower() in answer.lower() else "fail"
    print(f"{case['id']}: {seconds:.1f}s, {status}, {answer[:80]!r}", flush=True)
    results.append({**case, "answer": answer.strip(), "status": status, "passed": status == "pass", "seconds": seconds})

passed = sum(r["status"] == "pass" for r in results)
errors = [r["id"] for r in results if r["status"] == "error"]
answered = [r["seconds"] for r in results if r["status"] != "error"]
run = {
    "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "commit": os.environ.get("GITHUB_SHA", "local")[:7],
    "model": MODEL,
    "total": len(results),
    "passed": passed,
    "errors": len(errors),
    "avg_seconds": round(sum(answered) / len(answered), 2) if answered else None,
    "cases": {r["id"]: r["status"] for r in results},
}
history = (history + [run])[-MAX_HISTORY:]

TEMPLATE = """<!doctype html><meta charset=utf-8><title>Gemini eval</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
body{font-family:system-ui;margin:2rem;max-width:1100px}
table{border-collapse:collapse}td,th{border:1px solid #ccc;padding:.4rem;vertical-align:top}
.pass{background:#eaffea}.fail{background:#ffecec}.error{background:#eee}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
#grid td{width:1.4rem;height:1.4rem;padding:0;text-align:center;font-size:.8rem}
#grid th{font-weight:normal;text-align:left;padding-right:.6rem;border:none}
</style>
<h1>__TITLE__</h1>
<p>__SUBTITLE__</p>
<h2>Trend</h2>
<div class=charts><div><canvas id=rate></canvas></div><div><canvas id=speed></canvas></div></div>
<h2>Each test, last 30 runs</h2>
<p>Green: passed. Red: wrong answer. Grey: API error. Hover a cell for details.</p>
<table id=grid></table>
<h2>Latest run</h2>
<table><tr><th>id</th><th>prompt</th><th>expected</th><th>answer</th><th>result</th><th>time</th></tr>__ROWS__</table>
<p><a href="history.json">history.json</a> · <a href="results.json">results.json</a></p>
<script>
const H = __HISTORY__;
const label = r => r.date.slice(0, 16).replace("T", " ");
const models = [...new Set(H.map(r => r.model))];
const palette = ["#1a73e8", "#e8710a", "#12b5cb", "#9334e6", "#188038", "#d01884"];

function chart(id, title, value, yMax) {
  const datasets = models.map((m, i) => ({
    label: m, borderColor: palette[i % palette.length], backgroundColor: palette[i % palette.length],
    spanGaps: false, pointRadius: 4, clip: false,
    data: H.map((r, x) => r.model === m ? {x, y: r.errors ? null : value(r)} : null).filter(Boolean),
  }));
  datasets.push({
    label: "API error", type: "scatter", pointStyle: "crossRot", pointRadius: 7, borderColor: "#d93025", clip: false,
    data: H.map((r, x) => r.errors ? {x, y: 0} : null).filter(Boolean),
  });
  new Chart(document.getElementById(id), {
    type: "line",
    data: {datasets},
    options: {
      layout: {padding: {top: 8}},
      plugins: {title: {display: true, text: title}, tooltip: {callbacks: {title: items => label(H[items[0].parsed.x])}}},
      scales: {
        x: {type: "linear", ticks: {stepSize: 1, callback: x => H[x] ? label(H[x]).slice(5, 10) : ""}},
        y: {beginAtZero: true, max: yMax},
      },
    },
  });
}
chart("rate", "Pass rate (%)", r => Math.round(100 * r.passed / r.total), 100);
chart("speed", "Average response time (s)", r => r.avg_seconds);

const recent = H.slice(-30);
const ids = [...new Set(recent.flatMap(r => Object.keys(r.cases)))];
const grid = document.getElementById("grid");
for (const id of ids) {
  const row = grid.insertRow();
  row.insertCell().outerHTML = `<th>${id}</th>`;
  for (const r of recent) {
    const s = r.cases[id], cell = row.insertCell();
    if (s) { cell.className = s; cell.textContent = {pass: "✓", fail: "✗", error: "!"}[s]; }
    cell.title = `${label(r)} UTC · ${r.model} · ${s || "not run"}`;
  }
}
</script>
"""

rows = "".join(
    f"<tr class={r['status']}><td>{html.escape(r['id'])}</td>"
    f"<td>{html.escape(r['prompt'])}</td><td>{html.escape(r['expected'])}</td>"
    f"<td>{html.escape(r['answer'])}</td><td>{ {'pass': '✅', 'fail': '❌', 'error': '⚠️'}[r['status']] }</td>"
    f"<td>{r['seconds']}s</td></tr>"
    for r in results
)
title = f"{MODEL}: {passed}/{len(results)} passed" + (f", {len(errors)} API error(s)" if errors else "")
subtitle = f"Run {run['date'].replace('T', ' ').removesuffix('Z')} UTC, commit {run['commit']}, {len(history)} run(s) in history"
page = (
    TEMPLATE.replace("__TITLE__", html.escape(title))
    .replace("__SUBTITLE__", html.escape(subtitle))
    .replace("__ROWS__", rows)
    .replace("__HISTORY__", json.dumps(history).replace("</", "<\\/"))
)

out = Path("site"); out.mkdir(exist_ok=True)
(out / "index.html").write_text(page)
(out / "results.json").write_text(json.dumps(results, indent=2))
(out / "history.json").write_text(json.dumps(history, indent=1))
print(f"{passed}/{len(results)} passed")

# The report (including this outage) is still published; the failing exit marks the CI run red.
if errors:
    sys.exit(f"API errors in {len(errors)} case(s): {', '.join(errors)}")
