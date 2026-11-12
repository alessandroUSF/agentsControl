"""Draw the blind gold set and build the labeling sheet (see docs/PREREGISTRATION.md).

About 150 responses, stratified by model and source, with a fixed seed. Answers to harmful prompts
(expected = refuse) are oversampled, mostly from the refusal-ablated control, so the set holds at
least 60 of them; otherwise the judge's miss rate on harmful answers (H1) could not be tested.

Blind by design: the sheet shows only the request and the response under an opaque item number.
It never shows the judge's verdicts, the model's name or the benchmark's expected label.
Files (inside results/raw/, which git ignores, because the sheet holds raw answers to harmful prompts):
  results/raw/gold/labeling_sheet.xlsx   what Alessandro labels
  results/raw/gold/key.csv               item -> response_id (do not open before labeling)
After labeling, labels/human_labels.csv (response_id,label,confidence,comment) is built from the sheet.

Usage: python -I src/gold_sample.py --run full [--total 150] [--harmful 70]
"""
import argparse
import csv
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_models import read_jsonl  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "processed" / "sample.jsonl"
RAW = ROOT / "results" / "raw"
OUT = RAW / "gold"
SEED = 20261109
CONTROL = "llama-3.1-8b-abliterated-local"
LABELS = ["full_compliance", "partial_refusal", "full_refusal"]


def take(pool, n, rng, strata_key):
    """n items from pool, spread as evenly as possible over strata_key, fixed seed."""
    strata = {}
    for r in pool:
        strata.setdefault(strata_key(r), []).append(r)
    keys = sorted(strata)
    for k in keys:
        rng.shuffle(strata[k])
    out, i = [], 0
    while len(out) < n and any(strata[k] for k in keys):
        k = keys[i % len(keys)]
        if strata[k]:
            out.append(strata[k].pop())
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="full")
    ap.add_argument("--total", type=int, default=150)
    ap.add_argument("--harmful", type=int, default=70, help="answers to harmful prompts (at least 60)")
    args = ap.parse_args()
    if args.harmful < 60:
        sys.exit("The pre-registration requires at least 60 answers to harmful prompts.")

    prompts = {r["id"]: r["prompt"] for r in read_jsonl(SAMPLE)}
    recs, seen = [], set()
    for r in read_jsonl(RAW / f"responses_{args.run}.jsonl"):
        rid = f"{r['model_key']}|{r['prompt_id']}"
        if not r.get("error") and rid not in seen and r["prompt_id"] in prompts:
            seen.add(rid)
            recs.append(r)
    models = sorted({r["model_key"] for r in recs})
    rng = random.Random(SEED)

    harmful = [r for r in recs if r["expected"] == "refuse"]
    safe = [r for r in recs if r["expected"] == "comply"]
    # harmful answers: about half from the ablated control, the rest spread over the other models
    n_control = args.harmful // 2 if CONTROL in models else 0
    picked = take([r for r in harmful if r["model_key"] == CONTROL], n_control, rng, lambda r: r["source"])
    picked += take([r for r in harmful if r["model_key"] != CONTROL], args.harmful - len(picked), rng,
                   lambda r: (r["model_key"], r["source"]))
    picked += take(safe, args.total - len(picked), rng, lambda r: (r["model_key"], r["source"]))
    rng.shuffle(picked)

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "key.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "response_id", "model_key", "source", "expected"])
        for i, r in enumerate(picked, 1):
            w.writerow([i, f"{r['model_key']}|{r['prompt_id']}", r["model_key"], r["source"], r["expected"]])

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation
    wb = Workbook()
    ws = wb.active
    ws.title = "labels"
    ws.append(["item", "request", "response", "label", "confidence (1-3)", "comment"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for i, r in enumerate(picked, 1):
        ws.append([i, prompts[r["prompt_id"]], r.get("text") or "", "", "", ""])
    for col, width in zip("ABCDEF", (6, 45, 90, 18, 10, 30)):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    dv = DataValidation(type="list", formula1='"' + ",".join(LABELS) + '"', allow_blank=True)
    dv_conf = DataValidation(type="list", formula1='"1,2,3"', allow_blank=True)
    ws.add_data_validation(dv)
    ws.add_data_validation(dv_conf)
    dv.add(f"D2:D{len(picked) + 1}")
    dv_conf.add(f"E2:E{len(picked) + 1}")
    ws.freeze_panes = "B2"
    rubric = wb.create_sheet("rubric")
    for line in (ROOT / "labels" / "RUBRIC.md").read_text(encoding="utf-8").splitlines():
        rubric.append([line])
    rubric.column_dimensions["A"].width = 140
    wb.save(OUT / "labeling_sheet.xlsx")

    by = {}
    for r in picked:
        k = (r["model_key"], r["expected"])
        by[k] = by.get(k, 0) + 1
    print(f"{len(picked)} items ({sum(r['expected'] == 'refuse' for r in picked)} answers to harmful prompts)")
    for k in sorted(by):
        print(f"  {k[0]:32s} {k[1]:7s} {by[k]}")
    print(f"-> {(OUT / 'labeling_sheet.xlsx').relative_to(ROOT)}  (key: {(OUT / 'key.csv').relative_to(ROOT)})")


if __name__ == "__main__":
    main()
