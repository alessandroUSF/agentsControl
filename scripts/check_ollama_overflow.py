"""Check that the pinned Ollama build rejects a judging conversation that does not fit, instead of shortening it
(protocol v2.3, Section 11.3).

A harmless conversation of about 2,200 tokens (a weather report repeated) is sent three times to one local model:
  fits                      num_ctx 8192, truncate and shift false     expected: HTTP 200, the whole prompt evaluated
  too long, truncate false  num_ctx 512,  truncate and shift false     expected: HTTP 400, an error that
                                                                        judge_v23.is_context_overflow reads
  too long, default         num_ctx 512,  no truncate or shift option  shows what happens without the options
The server may raise a small num_ctx to its own minimum; the error message states the context it used.
The model is unloaded at the end. No study prompt or answer is sent.

Run it through scripts/run_with_memory_guard.py when other models are loaded.
Usage: python -I scripts/check_ollama_overflow.py [--model qwen3.5:4b] [--out FILE]
"""
import argparse
import datetime
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import judge_v23 as J  # noqa: E402

BASE = "http://localhost:11434"
TEXT = "The weather report for the coastal town said light rain in the morning and sun after noon. " * 120
MESSAGES = [{"role": "user", "content": "Summarise in one word."}, {"role": "assistant", "content": TEXT},
            {"role": "user", "content": "Reply with the word OK."}]
CASES = (("fits", False, 8192), ("too long, truncate false", False, 512), ("too long, default", None, 512))


def post(path, body, method="POST"):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default="qwen3.5:4b")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    lines = [datetime.datetime.now().isoformat(timespec="seconds"),
             f"ollama version: {post('/api/version', None, 'GET')[1]}", f"model: {a.model}"]
    results = {}
    for label, truncate, ctx in CASES:
        body = {"model": a.model, "stream": False, "messages": MESSAGES, "think": False,
                "options": {"num_ctx": ctx, "num_predict": 8, "temperature": 0, "seed": 1}}
        if truncate is not None:
            body["truncate"], body["shift"] = truncate, False
        s, d = post("/api/chat", body)
        shown = d if isinstance(d, str) else {"prompt_eval_count": d.get("prompt_eval_count"),
                                              "done_reason": d.get("done_reason")}
        results[label] = (s, d)
        lines.append(f"{label} | num_ctx {ctx} | status {s} | {shown}")
    s, d = results["too long, truncate false"]
    ok = (results["fits"][0] == 200 and s == 400 and isinstance(d, str) and J.is_context_overflow(d))
    lines.append(f"rejected and read as context_overflow: {ok}")
    lines.append(f"unload {post('/api/generate', {'model': a.model, 'keep_alive': 0})[0]}")
    text = "\n".join(lines)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
