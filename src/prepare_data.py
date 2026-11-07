"""Normalize the benchmarks into one JSONL file and draw a stratified sample with a fixed seed.

Usage (from the project root):  python -I src/prepare_data.py
Output: data/processed/prompts_all.jsonl (every prompt) and data/processed/sample.jsonl (the evaluation sample).

Schema (one JSON object per line):
  id        unique id, e.g. "xstest-12", "orhard-0457", "ortoxic-0031", "own-af-003"
  source    xstest | or-bench-hard | or-bench-toxic | own
  category  benchmark category (XSTest "type"; OR-Bench "category"; own categories)
  expected  "comply" (safe prompt: a refusal is over-refusal) or "refuse" (unsafe prompt: compliance is harmful)
  prompt    the user message
  framing   context framing applied to the prompt (only own prompts: none | adult_writer | student)

Sample sizes and seed are fixed in docs/PREREGISTRATION.md.
"""
import csv
import json
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OWN = ROOT / "data" / "own" / "own_prompts.csv"
OUT = ROOT / "data" / "processed"

SEED = 20261106
SAMPLE = {              # prompts per source
    "xstest": None,     # None = keep all 450
    "or-bench-hard": 300,
    "or-bench-toxic": 300,
}
FRAMINGS = {            # wording is fixed before the own prompts are run
    "none": "{prompt}",
    "adult_writer": "{prompt}",  # to be written: context sentence for an adult-fiction screenwriter
    "student": "{prompt}",       # to be written: context sentence for a student
}


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load():
    rows = []
    for r in read_csv(RAW / "xstest" / "xstest_prompts.csv"):
        rows.append({"id": f"xstest-{r['id']}", "source": "xstest", "category": r["type"],
                     "expected": "comply" if r["label"] == "safe" else "refuse",
                     "prompt": r["prompt"], "framing": "none"})
    for name, src, exp in (("or-bench-hard-1k.csv", "or-bench-hard", "comply"),
                           ("or-bench-toxic.csv", "or-bench-toxic", "refuse")):
        tag = "orhard" if src == "or-bench-hard" else "ortoxic"
        for i, r in enumerate(read_csv(RAW / "or-bench" / name)):
            rows.append({"id": f"{tag}-{i:04d}", "source": src, "category": r["category"],
                         "expected": exp, "prompt": r["prompt"], "framing": "none"})
    if OWN.exists():
        for r in read_csv(OWN):
            if not r.get("prompt", "").strip():
                continue
            for fr, template in FRAMINGS.items():
                rows.append({"id": f"own-{r['id']}-{fr}", "source": "own", "category": r["category"],
                             "expected": r["expected"], "prompt": template.format(prompt=r["prompt"]),
                             "framing": fr})
    return rows


def stratified(rows, n, rng):
    """Sample n rows keeping each category's share (largest-remainder rounding)."""
    if n is None or n >= len(rows):
        return list(rows)
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    quotas = {c: n * len(v) / len(rows) for c, v in by_cat.items()}
    alloc = {c: int(q) for c, q in quotas.items()}
    for c in sorted(quotas, key=lambda c: quotas[c] - alloc[c], reverse=True)[: n - sum(alloc.values())]:
        alloc[c] += 1
    out = []
    for c in sorted(by_cat):
        out += rng.sample(by_cat[c], alloc[c])
    return out


def main():
    rows = load()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    sample = []
    for src in ("xstest", "or-bench-hard", "or-bench-toxic"):
        sample += stratified([r for r in rows if r["source"] == src], SAMPLE[src], rng)
    sample += [r for r in rows if r["source"] == "own"]
    for path, data in ((OUT / "prompts_all.jsonl", rows), (OUT / "sample.jsonl", sample)):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    count = {}
    for r in sample:
        count[(r["source"], r["expected"])] = count.get((r["source"], r["expected"]), 0) + 1
    print(f"all prompts: {len(rows)} | sample: {len(sample)}")
    for k in sorted(count):
        print(f"  {k[0]:15s} expected={k[1]:7s} {count[k]}")


if __name__ == "__main__":
    main()
