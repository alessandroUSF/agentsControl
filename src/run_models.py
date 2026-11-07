"""Send the evaluation prompts to the enabled models, with a hard spending cap.

Usage (from the project root):
  python -I src/run_models.py --dry-run               # cost estimate only, no API call
  python -I src/run_models.py --pilot 50              # 50 stratified prompts per enabled model
  python -I src/run_models.py                         # full sample
  python -I src/run_models.py --models claude-haiku-5.5,gpt-5.6-luna   # only these keys

Safety and control:
  * Commercial APIs (Anthropic, OpenAI) only get prompts with expected="comply" and Alessandro's own
    prompts; the benchmarks' harmful prompts run only on the local models (providers.allowed).
  * BUDGET_USD (in .env) is a hard cap for THIS run. Before each call the runner reserves the
    worst case (prompt + max_output_tokens at list price) and stops when the next reservation
    would cross the cap. Actual cost comes from the usage the provider reports.
  * Raw answers go to results/raw/ (git-ignored: answers to harmful prompts are never published).
  * results/logs/calls_<run>.jsonl keeps an audit line per call WITHOUT the answer text
    (model, prompt id, tokens, cost, latency, stop reason, request id). That log can be published.
  * Re-running the same command resumes: (model, prompt) pairs already answered are skipped.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import random
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import providers  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "processed" / "sample.jsonl"
CONFIG = ROOT / "config" / "models.json"
RAW = ROOT / "results" / "raw"
LOGS = ROOT / "results" / "logs"
PILOT_SEED = 20261107


def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


def read_jsonl(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def pilot_subset(rows, n):
    """n prompts split evenly across (source, expected) strata, fixed seed."""
    rng = random.Random(PILOT_SEED)
    strata = {}
    for r in rows:
        strata.setdefault((r["source"], r["expected"]), []).append(r)
    keys = sorted(strata)
    base, extra = divmod(n, len(keys))
    out = []
    for i, k in enumerate(keys):
        out += rng.sample(strata[k], min(len(strata[k]), base + (1 if i < extra else 0)))
    return out


def est_input_tokens(prompt):
    return len(prompt) // 4 + 12


def cost(m, tin, tout):
    return (tin * m["price_in"] + tout * m["price_out"]) / 1e6


class Budget:
    def __init__(self, cap):
        self.cap, self.spent, self.reserved = cap, 0.0, 0.0
        self.lock = threading.Lock()
        self.stopped = False

    def reserve(self, amount):
        with self.lock:
            if self.stopped or self.spent + self.reserved + amount > self.cap:
                self.stopped = True
                return False
            self.reserved += amount
            return True

    def settle(self, reserved, actual):
        with self.lock:
            self.reserved -= reserved
            self.spent += actual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pilot", type=int, default=0, help="number of prompts for a pilot run")
    ap.add_argument("--models", default="", help="comma-separated model keys (default: enabled ones)")
    ap.add_argument("--run", default="", help="run name (default: pilot or full)")
    args = ap.parse_args()

    load_env()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))["models"]
    if args.models:
        wanted = set(args.models.split(","))
        models = [m for m in cfg if m["key"] in wanted]
        missing = wanted - {m["key"] for m in models}
        if missing:
            sys.exit(f"unknown model keys: {sorted(missing)}")
    else:
        models = [m for m in cfg if m["enabled"]]
    if not models and not args.dry_run:
        sys.exit("No model enabled. Set enabled=true in config/models.json or pass --models.")
    if not models:
        models = cfg  # dry run with nothing enabled: estimate every candidate

    rows = read_jsonl(SAMPLE)
    if args.pilot:
        rows = pilot_subset(rows, args.pilot)
    run = args.run or ("pilot" if args.pilot else "full")

    # ---- estimate -------------------------------------------------------------------------
    print(f"run={run} prompts={len(rows)}")
    total = 0.0
    for m in models:
        mine = [r for r in rows if providers.allowed(m, r)]
        tin = sum(est_input_tokens(r["prompt"]) for r in mine)
        c = cost(m, tin, m["est_output_tokens"] * len(mine))
        worst = cost(m, tin, m["max_output_tokens"] * len(mine))
        total += c
        print(f"  {m['key']:26s} {len(mine):5d} prompts  est ${c:7.2f}  (worst ${worst:7.2f})  price: {m['price_checked']}")
    print(f"  {'TOTAL (models only)':22s} est ${total:7.2f}   [judge calls are extra]")
    if args.dry_run:
        return

    cap = float(os.environ.get("BUDGET_USD", "0") or 0)
    if cap <= 0:
        sys.exit("Set BUDGET_USD in .env before a real run.")
    budget = Budget(cap)
    print(f"budget cap for this run: ${cap:.2f}")

    RAW.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    raw_path, log_path = RAW / f"responses_{run}.jsonl", LOGS / f"calls_{run}.jsonl"
    done = {(r["model_key"], r["prompt_id"]) for r in read_jsonl(raw_path) if not r.get("error")}
    write_lock = threading.Lock()

    def one(m, prov, r):
        if not providers.allowed(m, r):  # second guard, in case the filter above is ever changed
            raise RuntimeError(f"blocked: {r['id']} may not go to {m['key']}")
        reserve = cost(m, est_input_tokens(r["prompt"]), m["max_output_tokens"])
        if not budget.reserve(reserve):
            return "budget"
        rec = {"run": run, "model_key": m["key"], "provider": m["provider"], "model": m["model"],
               "prompt_id": r["id"], "source": r["source"], "category": r["category"],
               "expected": r["expected"], "framing": r["framing"],
               "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
        actual = 0.0
        try:
            out = providers.timed_call(prov, r["prompt"])
            actual = cost(m, out["input_tokens"], out["output_tokens"])
            rec.update(out, cost_usd=round(actual, 6), error=None)
        except Exception as e:  # recorded, not fatal: re-running retries the failed pairs
            rec.update(text=None, error=f"{type(e).__name__}: {str(e)[:300]}", cost_usd=0.0)
        finally:
            budget.settle(reserve, actual)
        log = {k: v for k, v in rec.items() if k != "text"}
        with write_lock:
            with open(raw_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            with open(log_path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(log, ensure_ascii=False) + "\n")
        return "error" if rec["error"] else "ok"

    for m in models:
        todo = [r for r in rows if providers.allowed(m, r) and (m["key"], r["id"]) not in done]
        print(f"\n{m['key']}: {len(todo)} to run ({len(rows) - len(todo)} already done)")
        if not todo:
            continue
        prov = providers.make(m)
        counts = {"ok": 0, "error": 0, "budget": 0}
        with ThreadPoolExecutor(max_workers=m.get("workers", 1)) as pool:
            futs = [pool.submit(one, m, prov, r) for r in todo]
            for i, f in enumerate(as_completed(futs), 1):
                counts[f.result()] += 1
                if i % 25 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)}  ok={counts['ok']} err={counts['error']}  spent=${budget.spent:.3f}")
        if counts["budget"]:
            print(f"STOPPED: budget cap reached (${budget.spent:.2f} of ${cap:.2f}).")
            break
    print(f"\nspent this run: ${budget.spent:.3f}  -> {raw_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
