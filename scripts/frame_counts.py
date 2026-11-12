"""Counts of existing material by the frames proposed for protocol v2.3 (draft B, 10 November 2026).

Prints aggregate counts only: no prompt text, no answer text, no item-level row of the gold key.
The gold key is read to count G1 items by frame; its SHA-256 is printed so that the sealed hash can be checked.

Frames (proposal, not frozen): within each (source, expected) stratum the prompts are ordered by
subsets.ordered(); harmful strata: rank < 30 = common set, rank < 150 = harmful frame, rest = harmful tail;
safe strata: rank < 45 = safe frame, rest = safe tail.

Usage: python -I scripts/frame_counts.py
"""
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import subsets  # noqa: E402

COMMON, HARM_FRAME, SAFE_FRAME = 30, 150, 45


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    rows = load_jsonl(ROOT / "data" / "processed" / "sample.jsonl")
    strata = collections.defaultdict(list)
    for r in rows:
        strata[(r["source"], r["expected"])].append(r)
    rank = {}
    for key in sorted(strata):
        for i, r in enumerate(subsets.ordered(strata[key], f"{key[0]}|{key[1]}")):
            rank[r["id"]] = (key, i)

    def frame(pid):
        key, i = rank[pid]
        if key[1] == "refuse":
            return "common set" if i < COMMON else ("harmful frame beyond the common set" if i < HARM_FRAME
                                                    else "harmful tail")
        return "safe frame" if i < SAFE_FRAME else "safe tail"

    order = ["common set", "harmful frame beyond the common set", "harmful tail", "safe frame", "safe tail"]

    def show(title, counter):
        print(title)
        for name in order:
            print(f"  {name}: {counter.get(name, 0)}")

    show("Prompts of the sealed sample by frame", collections.Counter(frame(p) for p in rank))

    raw = ROOT / "results" / "raw"
    pilot = {r["prompt_id"] for r in load_jsonl(raw / "responses_pilot_local.jsonl")}
    show(f"Prompts of the earlier local pilot ({len(pilot)} prompts, models 4-6)",
         collections.Counter(frame(p) for p in pilot))

    key_path = raw / "gold" / "key.csv"
    print("G1 key SHA-256:", hashlib.sha256(key_path.read_bytes()).hexdigest())
    with key_path.open(encoding="utf-8", newline="") as f:
        gold = list(csv.DictReader(f))
    ids = sorted(rank, key=len, reverse=True)
    gold_prompts = []
    for g in gold:
        hit = next((p for p in ids if p in g["response_id"]), None)
        if hit is None:
            raise SystemExit("a gold item does not resolve to a sampled prompt")
        gold_prompts.append(hit)
    show(f"G1 items ({len(gold)}) by frame", collections.Counter(frame(p) for p in gold_prompts))
    gp = set(gold_prompts)
    print(f"G1 distinct prompts: {len(gp)}; of them also in the earlier pilot: {len(gp & pilot)}")

    for name in ("harmful tail", "safe tail"):
        tail = {p for p in rank if frame(p) == name}
        free = tail - gp - pilot
        by_source = collections.Counter(rank[p][0][0] for p in free)
        print(f"{name}: {len(tail)} prompts; without G1 prompts {len(tail - gp)}; "
              f"without G1 and earlier-pilot prompts {len(free)} {dict(sorted(by_source.items()))}")

    answered = collections.defaultdict(set)
    for name in ("responses_full.jsonl", "responses_v22_local.jsonl"):
        for r in load_jsonl(raw / name):
            answered[r["model_key"]].add(r["prompt_id"])
    print("Answers that exist, by model and frame (full run and v2.2 local run):")
    for model in sorted(answered):
        c = collections.Counter(frame(p) for p in answered[model])
        missing = collections.Counter(frame(p) for p in rank if p not in answered[model])
        print(f"  {model}: " + ", ".join(f"{n} {c.get(n, 0)}" for n in order)
              + (f"; missing {dict(missing)}" if missing else "; none missing"))


if __name__ == "__main__":
    main()
