"""Dated inventory for protocol v2.3: the prompt sample, the frames, the answers that exist, the retired sample G1,
the pilot material and the exposure history of the answers. Counts only.

What the script uses:
  data/processed/sample.jsonl      identifier, source and benchmark label of each prompt
  results/raw/responses_*.jsonl    of each record: model key, provider, prompt identifier, benchmark label, error flag
  results/raw/gold/key.csv         of each row: the response identifier, to find its prompt
  config/*.json                    design constants and the fixed pilot prompts (identifiers)
It prints no prompt, no answer and no item-level row. It never opens the labelling sheet.

Usage: python -I scripts/data_inventory.py            print the inventory
       python -I scripts/data_inventory.py --write    write docs/DATA_INVENTORY.md
"""
import csv
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import frames_v23  # noqa: E402

RAW = ROOT / "results" / "raw"
LOGS = ROOT / "results" / "logs"
SAMPLE = ROOT / "data" / "processed" / "sample.jsonl"
FRAME_RUNS = ("responses_full.jsonl", "responses_v22_local.jsonl")      # the runs that the frames use
V1_PILOT = "responses_pilot_local.jsonl"

HISTORY = [
    ("7 November 2026",
     "Technical pilot of version 1 (run `pilot_local`): models 4, 5 and 6 answered 50 prompts. The public version 1 "
     "records the technical checks made on these 150 answers: errors, truncation, latency and output length."),
    ("7 and 8 November 2026",
     "Run `full` under version 1: models 4, 5 and 6 answered the 1,050 prompts. The runner wrote the answers and a "
     "call log without answer text."),
    ("8 November 2026",
     "The hashes of the files of both runs were recorded. The sampler of G1 (`src/gold_sample.py`, seed 20261109) "
     "selected 150 answers of the run `full` by model, source and benchmark label, skipped error records, copied "
     "the request and the answer of each drawn item into a labelling sheet and printed counts only. The hashes of "
     "the sheet and of its key were recorded on the same day."),
    ("8 and 9 November 2026",
     "Run `v22_local` under protocol v2.2: models 15, 16 and 17 answered the 1,050 prompts; model 18 had answered "
     "1,007 when the run was stopped."),
    ("10 November 2026",
     "`scripts/frame_counts.py`, `scripts/pilot_prompts_v23.py` and this script used, of each answer record, the "
     "model key, the provider, the prompt identifier, the benchmark label and the error flag, and of each row of "
     "the G1 key the response identifier. They printed counts. After that the hashes of the `v22_local` files were "
     "recorded and the run name was sealed in the code. `scripts/check_sealed_hashes.py` reads the bytes of each "
     "file to hash them."),
    ("11 November 2026",
     "The time of the first call of run `v22_local` was read from its call log (`results/logs/calls_v22_local.jsonl`, "
     "which holds no answer text) for the dates of protocol Section 3.2. No answer file was opened."),
    ("12 November 2026",
     "Decision D18: the answers of the sealed runs are not used; every answer of the study is generated after the "
     "pilot registration with seed 20261126. The 96 answers of G1 outside the frames stay the training material. No "
     "answer file was opened."),
    ("13 November 2026",
     "While preparing decision D22, the AI assistant ran seven commands on `results/raw/responses_v22_local.jsonl`. "
     "They counted the reasoning blocks that models 16 and 17 write into their output and measured their length, "
     "screened the answers with and without the block (counts by model, prompt category and benchmark label; for "
     "model 17: of 500 answers to harmful prompts, 366 move from screen-positive to screen-negative when the block "
     "is split off and 2 the other way), and printed in the assistant's session the first 140 characters, and the 60 "
     "characters from the closing tag, of three answers of model 16 to safe prompts. A command that looked for "
     "reasoning blocks in stored judge outputs found no such file."),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def jsonl(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def by_source(ids, src):
    c = Counter(src[p] for p in ids)
    return ", ".join(f"{s} {n}" for s, n in sorted(c.items()))


def build():
    L = []
    w = L.append
    design = json.loads((ROOT / "config" / "panel_v23.json").read_text(encoding="utf-8"))
    models = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]
    key_of = {m["n"]: m["key"] for m in models}
    number_of = {m["key"]: m["n"] for m in models}
    index = frames_v23.sample_index()
    fr = frames_v23.frames(index)
    common, harmful, safe = set(fr["common"][0]), set(fr["harmful"][0]), set(fr["safe"][0])
    h_tail, s_tail = set(fr["harmful_tail"][0]), set(fr["safe_tail"][0])
    source = {p: v[0] for p, v in index.items()}

    def place(p):
        if p in common:
            return "common set"
        if p in harmful:
            return "harmful frame beyond the common set"
        if p in h_tail:
            return "harmful tail"
        return "safe frame" if p in safe else "safe tail"

    places = ["common set", "harmful frame beyond the common set", "harmful tail", "safe frame", "safe tail"]

    w("# Data inventory")
    w("")
    w(f"Generated by `python -I scripts/data_inventory.py --write` on {dt.date.today().isoformat()}, for protocol v2.3 "
      "(`docs/STUDY_PROTOCOL_v2.3.md`).")
    w("")
    w("- Counts only. The script prints no prompt, no answer and no item-level row.")
    w("- The principal investigator states that no person has read, screened, judged or labelled an answer listed "
      "here (protocol v2.3, Section 15.3). The statement is signed with the pilot registration.")
    w("- The hashes of the files are in `docs/SEALED_HASHES.md`. `python -I scripts/check_sealed_hashes.py` checks "
      "them.")
    w("- **Decision D18 (12 November 2026).** No answer listed here is an answer of the study. Every answer of the "
      "pilot and of the frames is generated after the pilot registration, with seed 20261126. The only answers of "
      "these files that are read are the 96 answers of the retired sample G1 on prompts outside the frames: they "
      "train the annotators (protocol v2.3, Section 9.6).")
    w("")

    # 1 sample
    sample = list(jsonl(SAMPLE))
    w("## 1. Prompt sample")
    w("")
    w(f"`data/processed/sample.jsonl`: {len(sample):,} benchmark prompts. SHA-256 `{sha256(SAMPLE)}`.")
    w("")
    w("| Source | Benchmark label | Prompts |")
    w("|---|---|---|")
    for (s, e), n in sorted(Counter((r["source"], r["expected"]) for r in sample).items()):
        w(f"| {s} | {'safe (comply)' if e == 'comply' else 'harmful (refuse)'} | {n} |")
    w("")
    own = ROOT / "data" / "own" / "own_prompts.csv"
    if own.exists():
        with open(own, encoding="utf-8-sig", newline="") as f:
            n_own = sum(1 for _ in csv.DictReader(f))
        w(f"`data/own/own_prompts.csv` holds {n_own} prompts written by the author for protocol v2.2. Protocol v2.3 "
          "does not use them (Section 4.1 of the protocol), and no model ever answered one.")
        w("")

    # 2 frames
    w("## 2. Frames of protocol v2.3 (Section 5.1)")
    w("")
    w("A frame is a prefix of one seeded order inside each source (`src/subsets.py`, `src/frames_v23.py`).")
    w("")
    w("| Frame | Prompts | By source |")
    w("|---|---|---|")
    for name, label in (("common", "Common set"), ("harmful", "Harmful frame (contains the common set)"),
                        ("harmful_tail", "Harmful tail (pilot material only)"),
                        ("safe_commercial_controls", "Safe controls of the commercial panel"),
                        ("safe", "Safe frame (contains the commercial safe controls)"),
                        ("safe_tail", "Safe tail (pilot material only)")):
        ids, src = fr[name]
        w(f"| {label} | {len(ids)} | {by_source(ids, src)} |")
    w("")

    # 3 answers by file
    w("## 3. Answers that exist (`results/raw/`)")
    w("")
    w("| File | Records | Error records | Model | Answers | Distinct prompts | To harmful prompts | To safe prompts |")
    w("|---|---|---|---|---|---|---|---|")
    answered, providers, total_ok, unknown = {}, Counter(), 0, 0
    v1_pilot_prompts = set()
    for path in sorted(RAW.glob("responses_*.jsonl")):
        recs = list(jsonl(path))
        providers.update(r.get("provider") for r in recs)
        unknown += sum(1 for r in recs if r["prompt_id"] not in index)
        grouped = {}
        for r in recs:
            grouped.setdefault(r["model_key"], []).append(r)
        for k, (model, rs) in enumerate(sorted(grouped.items(), key=lambda kv: number_of.get(kv[0], 99))):
            ok = [r for r in rs if not r.get("error")]
            total_ok += len(ok)
            if path.name in FRAME_RUNS:
                answered.setdefault(model, set()).update(r["prompt_id"] for r in ok)
            if path.name == V1_PILOT:
                v1_pilot_prompts.update(r["prompt_id"] for r in rs)
            head = f"`{path.name}` | {len(recs):,} | {sum(1 for r in recs if r.get('error'))}" if k == 0 else " | | "
            w(f"| {head} | {number_of.get(model, '?')} `{model}` | {len(ok):,} | {len({r['prompt_id'] for r in ok}):,} | "
              f"{sum(1 for r in ok if r['expected'] == 'refuse'):,} | {sum(1 for r in ok if r['expected'] == 'comply'):,} |")
    w("")
    w(f"- Answers without an error flag, all files: {total_ok:,}.")
    w(f"- Providers of the records: {', '.join(f'{p} {n:,}' for p, n in sorted(providers.items(), key=str))}. "
      "`ollama` is the local runtime: no record comes from an API.")
    w(f"- Records whose prompt is not in the sample: {unknown}.")
    ledger = LOGS / "spend_ledger.jsonl"
    w(f"- Spending ledger (`results/logs/spend_ledger.jsonl`): "
      f"{'exists, ' + str(sum(1 for _ in jsonl(ledger))) + ' entries' if ledger.exists() else 'does not exist; no paid call has been made'}.")
    judged = sorted(p.name for p in (ROOT / "results").iterdir() if p.is_dir() and p.name not in ("raw", "logs"))
    w(f"- Folders with verdicts or labels under `results/`: {', '.join(judged) if judged else 'none'}.")
    w("")

    # 4 coverage
    w("## 4. Coverage of the frames")
    w("")
    w("Answers that the sealed runs `full` and `v22_local` hold, by model of the primary panel. Each model of the "
      f"primary panel answers the harmful frame and the safe frame: {len(harmful)} + {len(safe)} = "
      f"{len(harmful) + len(safe)} prompts. Since decision D18 none of these answers is used: the last column counts "
      "the frame answers that the study generates.")
    w("")
    w("| Model | Harmful frame | Safe frame | Harmful tail | Safe tail | Frame answers to generate (decision D18) |")
    w("|---|---|---|---|---|---|")
    need = len(harmful) + len(safe)
    exist_total = 0
    for n in design["primary_panel"]:
        got = answered.get(key_of[n], set())
        have = len(got & harmful) + len(got & safe)
        exist_total += have
        w(f"| {n} `{key_of[n]}` | {len(got & harmful)} of {len(harmful)} | {len(got & safe)} of {len(safe)} | "
          f"{len(got & h_tail)} of {len(h_tail)} | {len(got & s_tail)} of {len(s_tail)} | {need} |")
    w("")
    primary_total = need * len(design["primary_panel"])
    com = design["groups"]["commercial"]
    com_need = len(common) + len(safe)
    w(f"- Primary panel: {primary_total:,} frame answers, all to be generated after the freeze. The sealed runs hold "
      f"{exist_total:,} of them, which are not used (decision D18).")
    w(f"- Commercial panel ({len(com)} models; model 14 left the study before any call, decision D17 of 12 November "
      f"2026): each answers the common set and the safe frame, {len(common)} + {len(safe)} = {com_need} prompts; "
      f"{com_need * len(com):,} answers, none of which exists.")
    w(f"- All frames: {primary_total + com_need * len(com):,} answers, all still to be generated. Pilot answers come "
      "on top (Section 13 of the protocol).")
    w("- Every answer of the study is written under a new run name, with seed 20261126. The three existing run names "
      "are sealed.")
    w("")

    # 5 v1 pilot
    c = Counter(place(p) for p in v1_pilot_prompts)
    inside = sum(c[x] for x in ("common set", "harmful frame beyond the common set", "safe frame"))
    w("## 5. Technical pilot of version 1")
    w("")
    w(f"`results/raw/{V1_PILOT}`: {len(v1_pilot_prompts)} prompts, answered by models 4, 5 and 6 on 7 November 2026. "
      "Protocol v2.3 does not use these answers.")
    w("")
    w("| Where the prompts lie | Prompts |")
    w("|---|---|")
    for x in places:
        w(f"| {x} | {c.get(x, 0)} |")
    w("")
    w(f"- {inside} of the {len(v1_pilot_prompts)} prompts lie inside the frames. Since decision D18 the frames use no "
      "answer of a sealed run for them: they are generated after the freeze, like every frame answer.")
    w("- All of these prompts are excluded from the pilot of protocol v2.3.")
    w("")

    # 6 G1
    key = RAW / "gold" / "key.csv"
    g1_prompts = []
    if key.exists():
        with open(key, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        ids = sorted(index, key=len, reverse=True)
        for g in rows:
            hit = next((p for p in ids if p in g["response_id"]), None)
            if hit is None:
                raise SystemExit("a row of the G1 key does not resolve to a prompt of the sample")
            g1_prompts.append(hit)
        c = Counter(place(p) for p in g1_prompts)
        outside = c["harmful tail"] + c["safe tail"]
        w("## 6. Retired sample G1")
        w("")
        w(f"`results/raw/gold/key.csv`: {len(rows)} answers of models 4 to 6, drawn on 8 November 2026 under protocol "
          f"v2.2; {len(set(g1_prompts))} distinct prompts. The key is counted here and never listed.")
        w("")
        w("| Where the prompts lie | Answers |")
        w("|---|---|")
        for x in places:
            w(f"| {x} | {c.get(x, 0)} |")
        w("")
        w("- G1 is retired: protocol v2.3 draws a new probability sample for the labels (Section 9).")
        w(f"- The {outside} answers on tail prompts are the training material of the annotators (Section 9.6). They "
          "are the only answers of the sealed runs that are read (decision D18).")
        w("- The labelling sheet has the hash that was recorded on 8 November 2026, so nothing has been written "
          "into it. No label exists.")
        w("")

    # 7 pilot material
    gp, vp = set(g1_prompts), v1_pilot_prompts
    w("## 7. Pilot material of protocol v2.3 (Section 13.2)")
    w("")
    w("| Tail | Prompts | Without the prompts of G1 and of the version-1 pilot | By source |")
    w("|---|---|---|---|")
    for label, tail in (("Harmful tail", h_tail), ("Safe tail", s_tail)):
        free = tail - gp - vp
        w(f"| {label} | {len(tail)} | {len(free)} | {by_source(free, source)} |")
    w("")
    fixed = ROOT / "config" / "pilot_prompts_v23.json"
    if fixed.exists():
        d = json.loads(fixed.read_text(encoding="utf-8"))
        in_frames = 0
        for i, rnd in enumerate(d["rounds"], 1):
            ids = set(rnd["harmful"]) | set(rnd["safe"])
            in_frames += len(ids & (harmful | safe))
            w(f"- Round {i} (`config/pilot_prompts_v23.json`): {len(rnd['harmful'])} harmful and {len(rnd['safe'])} "
              f"safe prompts; {len(rnd['api'])} of them are answered by the models reached through an API. "
              f"Prompts shared with G1 or the version-1 pilot: {len(ids & (gp | vp))}.")
        w(f"- Pilot prompts that lie inside a frame: {in_frames}.")
        w("")

    # 8 history
    w("## 8. Exposure history of the answers")
    w("")
    w("| Date | What was done |")
    w("|---|---|")
    for date, text in HISTORY:
        w(f"| {date} | {text} |")
    w("")
    w("- Apart from the sampler of G1, no script copied an answer text. Until 12 November no script printed, "
      "screened, classified or summarised one; the commands of 13 November are in the table.")
    w("- No judging call has been made. No verdict and no label exists.")
    w("- No call to an API has been made. No money has been spent on model calls.")
    w("")
    return "\n".join(L)


def main():
    text = build()
    if "--write" in sys.argv:
        out = ROOT / "docs" / "DATA_INVENTORY.md"
        out.write_text(text, encoding="utf-8", newline="")
        print(f"written: {out.relative_to(ROOT).as_posix()} ({len(text.splitlines())} lines)")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
