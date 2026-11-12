import html, json, os, sys, time
from pathlib import Path
from google import genai
from google.genai import types

MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
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
        answer = client.models.generate_content(model=MODEL, contents=case["prompt"]).text or ""
    except Exception as e:
        answer = f"ERROR: {e}"
    print(f"{case['id']}: {time.perf_counter() - start:.1f}s, {answer[:80]!r}", flush=True)
    results.append({
        **case,
        "answer": answer.strip(),
        "passed": case["expected"].lower() in answer.lower(),
        "seconds": round(time.perf_counter() - start, 2),
    })

passed = sum(r["passed"] for r in results)
rows = "".join(
    f"<tr class={'pass' if r['passed'] else 'fail'}><td>{html.escape(r['id'])}</td>"
    f"<td>{html.escape(r['prompt'])}</td><td>{html.escape(r['expected'])}</td>"
    f"<td>{html.escape(r['answer'])}</td><td>{'✅' if r['passed'] else '❌'}</td><td>{r['seconds']}s</td></tr>"
    for r in results
)
out = Path("site"); out.mkdir(exist_ok=True)
(out / "index.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Gemini eval</title>
<style>body{{font-family:system-ui;margin:2rem}}table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:.4rem;vertical-align:top}}
.pass{{background:#eaffea}}.fail{{background:#ffecec}}</style>
<h1>{MODEL}: {passed}/{len(results)} passed</h1>
<p>Run {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}, commit {os.environ.get('GITHUB_SHA', 'local')[:7]}</p>
<table><tr><th>id</th><th>prompt</th><th>expected</th><th>answer</th><th>result</th><th>time</th></tr>{rows}</table>""")
(out / "results.json").write_text(json.dumps(results, indent=2))
print(f"{passed}/{len(results)} passed")

# Wrong answers are results worth publishing; API errors mean the run itself is broken.
errors = [r["id"] for r in results if r["answer"].startswith("ERROR:")]
if errors:
    sys.exit(f"API errors in {len(errors)} case(s): {', '.join(errors)}")