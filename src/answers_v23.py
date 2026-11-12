"""Stored answers of protocol v2.3: one canonical answer per (model, prompt), with its side, status and screen.

Answers are the records of src/run_models.py in results/raw/responses_<run>.jsonl. v2.3 runs are named by the
caller. The sealed runs of 7 to 9 November 2026 ('full', 'v22_local', 'pilot_local') hold no answer of the study
(decision D18, Section 3.4): they are refused as v2.3 runs. The training draw alone reads the run of the retired
sample G1 ('full', TRAINING_RUNS), for the training answers of Section 9.6.

Canonical answer of (model, prompt):
  - the last record without a transport error, in file order (the runs as given);
  - otherwise the last record that a v2.3 runner marked as a final rejection (answer status 'error', Section 10.1);
  - otherwise none: the answer is missing (a pending call, or never sent).
Pilot records (pilot = true) serve the pilot only; frame answers never come from them. A record without the pilot
field (the sealed format) counts as a main-run record.

The answer text is read here only to compute the screen (src/screen.py). Nothing in this module prints it.
Standard library only.
"""
import json
from pathlib import Path

import screen as screen_mod

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
SEALED_RUNS = ("full", "pilot_local", "v22_local")   # written 7-9 Nov 2026; hashes in docs/SEALED_HASHES.md
SEALED_USED = ()               # decision D18: no sealed answer is an answer of the study
TRAINING_RUNS = ("full",)      # the run of the retired sample G1, read by the training draw only (Section 9.6)
NOT_USED = ("pilot_local",)    # never read
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
    """Answer files in canonical order: the sealed runs given (none for the answers of the study, decision D18;
    TRAINING_RUNS for the training draw), then the v2.3 runs in the order given. A sealed name among the v2.3 runs
    is refused."""
    bad = [r for r in v23_runs if r in SEALED_RUNS]
    if bad:
        raise ValueError(f"runs {bad} are sealed: they hold no answer of the study (decision D18, Section 3.4)")
    names = list(sealed) + [r for r in v23_runs if r not in sealed]
    for r in names:
        if r in NOT_USED:
            raise ValueError(f"run {r} is not used in v2.3 (Section 3.4)")
    return [Path(raw) / f"responses_{r}.jsonl" for r in names]


def canonical(records, pilot=False):
    """{(model_key, prompt_id): record}. pilot=False keeps the main-run records, pilot=True the pilot records.
    Records of a run in SEALED_USED (none since decision D18) would count for both."""
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
