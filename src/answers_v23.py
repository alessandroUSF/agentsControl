"""Stored answers of protocol v2.3: one canonical answer per (model, prompt), with its side, status and screen.

Answers are the records of src/run_models.py in results/raw/responses_<run>.jsonl. The sealed runs 'full' and
'v22_local' are used (Section 3.4); 'pilot_local' (the version-1 pilot) is not. v2.3 runs are named by the caller.

Canonical answer of (model, prompt):
  - the last record without a transport error, in file order (sealed runs first, then the v2.3 runs as given);
  - otherwise the last record that a v2.3 runner marked as a final rejection (answer status 'error', Section 10.1);
  - otherwise none: the answer is missing (a pending call, or never sent).
Pilot records (pilot = true) serve the pilot only; frame answers never come from them, and pilot answers of the
sealed runs are the tail answers of those runs (Section 5.3).

The answer text is read here only to compute the screen (src/screen.py). Nothing in this module prints it.
Standard library only.
"""
import json
from pathlib import Path

import screen as screen_mod

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
SEALED_USED = ("full", "v22_local")
NOT_USED = ("pilot_local",)
NO_CONTENT = screen_mod.NO_CONTENT
SIDE = {"refuse": "harmful", "comply": "safe"}


def answer_id(model_key, prompt_id):
    return f"{model_key}|{prompt_id}"


def split_id(aid):
    model_key, prompt_id = aid.split("|", 1)
    return model_key, prompt_id


def read_records(path):
    out = []
    path = Path(path)
    if not path.exists():
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue          # an interrupted write: the runner re-sends that pair
    return out


def run_files(v23_runs, raw=RAW, sealed=SEALED_USED):
    """Answer files in canonical order: the sealed runs used by v2.3, then the v2.3 runs in the order given."""
    names = [r for r in sealed] + [r for r in v23_runs if r not in sealed]
    for r in names:
        if r in NOT_USED:
            raise ValueError(f"run {r} is not used in v2.3 (Section 3.4)")
    return [Path(raw) / f"responses_{r}.jsonl" for r in names]


def canonical(records, pilot=False):
    """{(model_key, prompt_id): record}. pilot=False keeps main-run records of v2.3 runs and every record of the
    sealed runs; pilot=True keeps the pilot records of v2.3 runs and every record of the sealed runs."""
    good, final_err = {}, {}
    for r in records:
        if r.get("run") in NOT_USED:
            continue
        if r.get("run") not in SEALED_USED and bool(r.get("pilot")) != bool(pilot):
            continue
        key = (r["model_key"], r["prompt_id"])
        if not r.get("error"):
            good[key] = r
        elif r.get("final_error"):
            final_err[key] = r
    out = dict(final_err)
    out.update(good)
    return out


def status_of(rec):
    if rec is None:
        return "missing"
    if rec.get("answer_status"):
        return rec["answer_status"]
    return "error" if rec.get("error") else "ok"


def table(records, rules=None, pilot=False, number_of=None):
    """One row per canonical answer: answer_id, model_key, model (number), prompt_id, source, side, status, screen,
    has_content. The text stays in the record (key 'text') for the judging runner; it is never printed."""
    rules = rules or screen_mod.load()
    rows = {}
    for (mk, pid), r in canonical(records, pilot).items():
        st = status_of(r)
        scr = screen_mod.screen(r.get("text") or "", st, rules)
        rows[answer_id(mk, pid)] = {
            "answer_id": answer_id(mk, pid), "model_key": mk, "model": (number_of or {}).get(mk),
            "prompt_id": pid, "source": r.get("source"), "side": SIDE.get(r.get("expected")),
            "status": st, "screen": scr, "has_content": st not in NO_CONTENT and bool((r.get("text") or "").strip()),
            "run": r.get("run"), "model_returned": r.get("model_returned"),
            "served_provider": r.get("served_provider"), "text": r.get("text") or ""}
    return rows


def guard(raw):
    """The answer files of this repository are read (and screened) only after the pilot registration is recorded
    (Sections 3.4 and 14): before it, no code uses an answer text. Synthetic files elsewhere are not affected."""
    import spend_v23
    if Path(raw).resolve() == RAW.resolve() and not spend_v23.registered():
        raise SystemExit("answers_v23: results/raw is read only after the pilot registration is recorded "
                         "(spend_v23.py register --tag TAG)")


def load_table(v23_runs, raw=RAW, pilot=False, rules=None, number_of=None, sealed=SEALED_USED):
    guard(raw)
    recs = []
    for p in run_files(v23_runs, raw, sealed):
        recs += read_records(p)
    return table(recs, rules, pilot, number_of)


def public(row):
    """A row without the answer text (for counts, logs and the label sampler)."""
    return {k: v for k, v in row.items() if k != "text"}
