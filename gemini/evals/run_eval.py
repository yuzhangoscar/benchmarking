import html, json, os, time
from pathlib import Path
from google import genai

MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
client = genai.Client()  # reads GEMINI_API_KEY from the environment

cases = [json.loads(l) for l in Path("evals/cases.jsonl").read_text().splitlines() if l.strip()]
results = []
for case in cases:
    start = time.perf_counter()
    try:
        answer = client.models.generate_content(model=MODEL, contents=case["prompt"]).text or ""
    except Exception as e:
        answer = f"ERROR: {e}"
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