"""Label sample, labelling sheets and training sheets of protocol v2.3 (Sections 9.2, 9.4 and 9.6).

Two steps, run at different times:

  training   After the pilot registration and before the first judging call of the pilot (Section 9.6).
             Material: the answers of the retired sample G1 on prompts outside the frames (96 in the protocol:
             25 to harmful prompts, 71 to safe prompts). Two rounds of 30 answers, each with 12 answers to
             harmful prompts and 18 to safe prompts, drawn without replacement with the seed of the label sample:
             inside each side the material is put in SHA-256 order of (seed, "training", side, answer id); round 1
             takes the first answers, round 2 the next ones. Both labellers label the same two sheets.

  sample     Block 4 of Section 12.3: every answer exists and has its screen result; nobody has opened an answer.
             The stored answers come from src/answers_v23.py (one canonical answer per model and prompt, with its
             side and screen). Only the answers that the frames expect are kept (Section 5.2): the primary panel
             on the harmful frame, the commercial panel on the common set, every model on the safe frame. The
             selection (src/label_sample.py) sees model, prompt, source, side and screen and nothing else: no
             verdict file is read. The sample, the challenge set (h60), the reference subset (api_ref) and its two
             halves (Section 9.4: the other answers of the reference subset in SHA-256 order of their answer ids,
             the first half first) are written to a JSONL file without text, for the judging runner.

Sheets (rubric, Part B.10; columns of docs/annotator_packet/labeling_sheet_TEMPLATE.csv): one row per item with a
neutral item id, the request and the answer; the label fields are empty. A sheet holds no model, no screen
result, no cell, no weight, no verdict and no label, and its rows are in a seeded SHA-256 order of their own, so
neither the order nor the ids show how the sample was composed (Sections 9.1, 9.3 and 16.8). The first labeller
(the PI) labels every answer of the sample; the second labeller labels the answers marked 'second'. The keys from
item id to answer are separate files that only the scripts read.

Usage (from the project root; output directories are created; no file is ever overwritten):
  python -I scripts/label_draw_v23.py training --g1-key results/raw/gold/key.csv --out results/labels/training_v23
  python -I scripts/label_draw_v23.py sample --runs RUN [RUN ...] --out results/labels/sample_v23
Options: --raw DIR (answer files responses_<run>.jsonl; default results/raw), --sample (prompt file; default
data/processed/sample.jsonl), --design (config/panel_v23.json), --models (config/models.json), and for 'sample'
--screen-rules (a file with a "screen" block; default config/panel_v23.json, or the revised rules written by
scripts/reading_draw_v23.py).

Files written by 'training':
  training_round1.csv, training_round2.csv  the two training sheets (both labellers)
  training_key_v23.csv                      item id -> answer, with the hashes of request and answer (scripts only)
  training_manifest_v23.json                hashes of inputs, code and outputs; counts
Files written by 'sample':
  label_sample_v23.jsonl                    one row per labelled answer, no text (judging runner, join, analysis)
  label_sample_v23_report.json              sampler report: counts, shortages by model and side, every expected
                                            cell, uncovered answers; frame answers that are missing
  sheet_first_labeller.csv                  sheet of the first labeller (every answer of the sample)
  sheet_second_labeller.csv                 sheet of the second labeller (the answers marked 'second')
  label_key_first_v23.csv, label_key_second_v23.csv   item id -> answer id and text hashes (scripts only)
  label_draw_manifest_v23.json              hashes of inputs, code and outputs; counts
The script prints counts and file names only: no request, no answer.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import answers_v23  # noqa: E402
import frames_v23  # noqa: E402
import label_sample as LS  # noqa: E402
import label_sheets_v23 as S  # noqa: E402
import screen  # noqa: E402

MODELS = ROOT / "config" / "models.json"
TRAINING_ROUNDS = 2                                   # Section 9.6
TRAINING_PER_ROUND = {"harmful": 12, "safe": 18}      # Section 9.6: 30 answers per round
TRAINING_MATERIAL = {"harmful": 25, "safe": 71}       # Section 9.6, as counted on 10 November; checked, not used
SIDE = {"refuse": "harmful", "comply": "safe"}
CODE = (Path(__file__), ROOT / "scripts" / "label_sheets_v23.py", ROOT / "src" / "label_sample.py",
        ROOT / "src" / "answers_v23.py", ROOT / "src" / "frames_v23.py", ROOT / "src" / "screen.py",
        ROOT / "src" / "subsets.py")


def load_prompts(path):
    """prompt id -> request text (data/processed/sample.jsonl, as written by src/prepare_data.py)."""
    return {r["id"]: r["prompt"] for r in S.read_jsonl(path)}


def number_of(path):
    """model key -> model number (field 'n' of config/models.json)."""
    return {m["key"]: int(m["n"]) for m in json.loads(Path(path).read_text(encoding="utf-8"))["models"]}


def frame_plan(index, design_path, design):
    """(model, prompt id) -> (side, source) for every answer that the frames expect (Section 5.2)."""
    fr = frames_v23.frames(index, frames_v23.sizes(design_path))
    plan = {}
    for m in sorted(design["group_of"]):
        harmful = fr["harmful"] if m in design["primary"] else fr["common"]
        for side, (ids, src) in (("harmful", harmful), ("safe", fr["safe"])):
            for p in ids:
                plan[(m, p)] = (side, src[p])
    return plan


def answer_files(runs, raw):
    """The answer files that answers_v23 reads, with their hashes (files that do not exist are skipped there)."""
    return {S.rel(p): S.sha256_file(p) for p in answers_v23.run_files(runs, raw) if Path(p).exists()}


def input_hashes(args, extra=None):
    out = {"sample": {"path": S.rel(args.sample), "sha256": S.sha256_file(args.sample)},
           "design": {"path": S.rel(args.design), "sha256": S.sha256_file(args.design)}}
    out.update(extra or {})
    return out


def training(args):
    S.check_template()
    out = Path(args.out)
    names = [f"training_round{r}.csv" for r in range(1, TRAINING_ROUNDS + 1)] + ["training_key_v23.csv"]
    S.refuse_existing([out / n for n in names + ["training_manifest_v23.json"]])
    design = LS.load_design(args.design)
    seed = design["labels"]["seed"]
    index = frames_v23.sample_index(args.sample)
    prompts = load_prompts(args.sample)
    fr = frames_v23.frames(index, frames_v23.sizes(args.design))
    inside = set(fr["harmful"][0]) | set(fr["safe"][0])

    # The G1 key (written by src/gold_sample.py): item, response_id = "<model_key>|<prompt_id>", model_key,
    # source, expected. Only identifiers are read from it.
    header, key_rows = S.read_csv(args.g1_key)
    for c in ("response_id", "model_key", "source", "expected"):
        if c not in header:
            raise SystemExit(f"{args.g1_key}: column {c} missing")
    material, in_frames = [], 0
    for row in key_rows:
        mk, rid = row["model_key"], row["response_id"]
        if not rid.startswith(mk + "|"):
            raise SystemExit("an item of the G1 key has a response id that does not start with its model key")
        pid = rid[len(mk) + 1:]
        if pid not in index:
            raise SystemExit("an item of the G1 key does not resolve to a prompt of the sample")
        source, expected, _ = index[pid]
        if (row["source"], row["expected"]) != (source, expected):
            raise SystemExit("an item of the G1 key disagrees with the sample on source or benchmark label")
        if pid in inside:
            in_frames += 1
            continue
        material.append({"answer_id": answers_v23.answer_id(mk, pid), "model_key": mk, "prompt_id": pid,
                         "source": source, "side": SIDE[expected]})
    if len({m["answer_id"] for m in material}) != len(material):
        raise SystemExit("the G1 key names the same answer twice")
    count = {s: sum(m["side"] == s for m in material) for s in TRAINING_PER_ROUND}
    for s, n in TRAINING_PER_ROUND.items():
        if count[s] < TRAINING_ROUNDS * n:
            raise SystemExit(f"training material: {count[s]} answers to {s} prompts, "
                             f"{TRAINING_ROUNDS * n} needed for the two rounds")

    # G1 was drawn from the sealed run 'full'; answers_v23 reads the sealed runs used by v2.3
    table = answers_v23.load_table([], raw=args.raw, pilot=False)
    absent = [m["answer_id"] for m in material if m["answer_id"] not in table]
    if absent:
        raise SystemExit(f"{len(absent)} answers of the training material are not in the answer files")

    rounds = {r: [] for r in range(1, TRAINING_ROUNDS + 1)}
    for side, k in TRAINING_PER_ROUND.items():
        pool = sorted((m for m in material if m["side"] == side),
                      key=lambda m: S.order_key(seed, "training", side, m["answer_id"]))
        for r in rounds:
            rounds[r] += pool[(r - 1) * k: r * k]
    key_rows_out, outputs = [], {}
    for r, items in rounds.items():
        items.sort(key=lambda m: S.order_key(seed, "training sheet", r, m["answer_id"]))
        sheet = []
        for iid, m in zip(S.item_ids(f"T{r}", len(items)), items):
            request, answer = prompts[m["prompt_id"]], table[m["answer_id"]]["text"]
            sheet.append({"item_id": iid, "request": request, "answer": answer})
            key_rows_out.append(dict(m, item_id=iid, round=r, request_sha256=S.sha256_text(request),
                                     answer_sha256=S.sha256_text(answer),
                                     answer_status=table[m["answer_id"]]["status"]))
        S.write_sheet(out / f"training_round{r}.csv", sheet)
    S.write_csv(out / "training_key_v23.csv", ("item_id", "round", "answer_id", "model_key", "prompt_id", "source",
                                               "side", "answer_status", "request_sha256", "answer_sha256"),
                key_rows_out)
    for n in names:
        outputs[n] = S.sha256_file(out / n)
    counts = {"material": count, "g1_items": len(key_rows), "g1_items_in_frames": in_frames,
              "rounds": {r: {s: sum(m["side"] == s for m in items) for s in TRAINING_PER_ROUND}
                         for r, items in rounds.items()},
              "answers_without_content": sum(1 for m in material if not table[m["answer_id"]]["has_content"])}
    S.write_json(out / "training_manifest_v23.json", {
        "step": "training", "protocol": "v2.3, Section 9.6", "created_utc": S.now_utc(), "command": sys.argv,
        "seed": seed, "inputs": input_hashes(args, {"g1_key": {"path": S.rel(args.g1_key),
                                                               "sha256": S.sha256_file(args.g1_key)},
                                                    "answer_files": answer_files([], args.raw)}),
        "code": S.code_hashes(*CODE), "counts": counts, "outputs": outputs})
    print(f"training material: {count} (protocol: {TRAINING_MATERIAL}); G1 items inside the frames: {in_frames}")
    if count != TRAINING_MATERIAL:
        print("NOTE: the material differs from the counts of the protocol; check the G1 key and the answer files")
    for r, c in counts["rounds"].items():
        print(f"round {r}: {c}")
    for n in names + ["training_manifest_v23.json"]:
        print("written", S.rel(out / n))


def sample(args):
    S.check_template()
    out = Path(args.out)
    names = ["label_sample_v23.jsonl", "label_sample_v23_report.json", "sheet_first_labeller.csv",
             "sheet_second_labeller.csv", "label_key_first_v23.csv", "label_key_second_v23.csv"]
    S.refuse_existing([out / n for n in names + ["label_draw_manifest_v23.json"]])
    design = LS.load_design(args.design)
    seed = design["labels"]["seed"]
    rules = screen.load(args.screen_rules)
    index = frames_v23.sample_index(args.sample)
    prompts = load_prompts(args.sample)
    plan = frame_plan(index, args.design, design)

    table = answers_v23.load_table(args.runs, raw=args.raw, pilot=False, rules=rules,
                                   number_of=number_of(args.models))
    records, outside, found = [], 0, set()
    for aid in sorted(table):
        pub = answers_v23.public(table[aid])              # no text enters the selection
        key = (pub["model"], pub["prompt_id"])
        if key not in plan:
            outside += 1        # tail answers (pilot material), prompts outside a model's frames, other models
            continue
        side, source = plan[key]
        if (pub["side"], pub["source"]) != (side, source):
            raise SystemExit(f"answer {aid}: its side or source differs from the prompt file")
        found.add(key)
        # the selection reads model, prompt, source, side and screen; answer_id and model_key only travel along
        records.append({"model": pub["model"], "prompt": pub["prompt_id"], "source": source, "side": side,
                        "screen": pub["screen"], "answer_id": aid, "model_key": pub["model_key"]})
    rows, report = LS.select(records, design)

    # Section 9.4, halves for cut 4: the other answers of the reference subset in SHA-256 order of their ids;
    # the first half takes the larger part of an odd number (as scripts/manifest_v23.py counts it)
    others = sorted((r for r in rows if r["api_ref"] and not r["h60"]),
                    key=lambda r: S.sha256_bytes(r["answer_id"].encode("utf-8")))
    first_half = len(others) - len(others) // 2
    half = {r["answer_id"]: 1 if i < first_half else 2 for i, r in enumerate(others)}
    sheets = {}
    for name, letter, members in (("first", "A", rows), ("second", "B", [r for r in rows if r["second"]])):
        order = sorted(members, key=lambda r: S.order_key(seed, "sheet", name, r["answer_id"]))
        sheets[name] = list(zip(S.item_ids(letter, len(order)), order))
    item = {name: {r["answer_id"]: iid for iid, r in pairs} for name, pairs in sheets.items()}

    sample_rows = []
    for r in sorted(rows, key=lambda r: (r["model"], r["side"], r["screen"], r["rank"])):
        sample_rows.append({"answer_id": r["answer_id"], "model": r["model"], "model_key": r["model_key"],
                            "prompt_id": r["prompt"], "source": r["source"], "side": r["side"],
                            "screen": r["screen"], "weight": r["weight"], "cell_size": r["cell_size"],
                            "cell_labelled": r["cell_labelled"], "collapsed": r["collapsed"], "rank": r["rank"],
                            "h60": r["h60"], "api_ref": r["api_ref"], "ref_half": half.get(r["answer_id"], 0),
                            "second": r["second"], "item_id_first": item["first"][r["answer_id"]],
                            "item_id_second": item["second"].get(r["answer_id"], "")})
    S.write_jsonl(out / "label_sample_v23.jsonl", sample_rows)

    missing = {}
    for (m, p), (side, _) in plan.items():
        if (m, p) not in found:
            missing[f"{m}|{side}"] = missing.get(f"{m}|{side}", 0) + 1
    status = {}
    for rec in records:
        st = table[rec["answer_id"]]["status"]
        k = f"{rec['side']}|{st}"
        status[k] = status.get(k, 0) + 1
    S.write_json(out / "label_sample_v23_report.json", {
        "protocol": "v2.3, Sections 9.2 and 9.4", "seed": seed, "screen_version": rules["version"],
        "sampler": report,
        "frame_answers": {"expected": len(plan), "found": len(found), "missing_by_model_and_side":
                          dict(sorted(missing.items())), "status_by_side": dict(sorted(status.items())),
                          "answers_outside_the_frames": outside},
        "reference_halves": {"first": first_half, "second": len(others) - first_half}})

    for name, pairs in sheets.items():
        sheet, key = [], []
        for iid, r in pairs:
            request, answer = prompts[r["prompt"]], table[r["answer_id"]]["text"]
            sheet.append({"item_id": iid, "request": request, "answer": answer})
            key.append({"item_id": iid, "answer_id": r["answer_id"], "request_sha256": S.sha256_text(request),
                        "answer_sha256": S.sha256_text(answer)})
        S.write_sheet(out / f"sheet_{name}_labeller.csv", sheet)
        S.write_csv(out / f"label_key_{name}_v23.csv", ("item_id", "answer_id", "request_sha256", "answer_sha256"),
                    key)

    outputs = {n: S.sha256_file(out / n) for n in names}
    counts = {k: report[k] for k in ("labelled", "harmful", "safe", "second", "h60", "api_ref",
                                     "collapsed_cells", "uncovered_answers")}
    counts.update(shortages=len(report["shortages"]), unfilled=sum(s["unfilled"] for s in report["shortages"]),
                  sheet_first=len(sheets["first"]), sheet_second=len(sheets["second"]))
    S.write_json(out / "label_draw_manifest_v23.json", {
        "step": "sample", "protocol": "v2.3, Sections 9.2 and 9.4", "created_utc": S.now_utc(), "command": sys.argv,
        "seed": seed, "runs": args.runs,
        "inputs": input_hashes(args, {"models": {"path": S.rel(args.models), "sha256": S.sha256_file(args.models)},
                                      "screen_rules": {"path": S.rel(args.screen_rules),
                                                       "sha256": S.sha256_file(args.screen_rules),
                                                       "version": rules["version"]},
                                      "answer_files": answer_files(args.runs, args.raw)}),
        "code": S.code_hashes(*CODE), "counts": counts, "outputs": outputs})
    print("label sample:", counts)
    for s in report["shortages"]:
        if s["unfilled"]:
            print(f"  shortage: model {s['model']} {s['side']}: {s['unfilled']} labels unfilled")
    if missing:
        print(f"  frame answers missing: {sum(missing.values())} (by model and side in the report)")
    for n in names + ["label_draw_manifest_v23.json"]:
        print("written", S.rel(out / n))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="step", required=True)
    for name in ("training", "sample"):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True, help="output directory")
        p.add_argument("--raw", default=str(answers_v23.RAW), help="directory of responses_<run>.jsonl")
        p.add_argument("--sample", default=str(frames_v23.SAMPLE), help="prompt file")
        p.add_argument("--design", default=str(LS.DESIGN), help="panel file")
        if name == "training":
            p.add_argument("--g1-key", required=True, help="key of the retired sample G1")
        else:
            p.add_argument("--runs", nargs="+", required=True, help="v2.3 run names (the sealed runs are added)")
            p.add_argument("--models", default=str(MODELS))
            p.add_argument("--screen-rules", default=str(screen.DESIGN), help="file with a 'screen' block")
    args = ap.parse_args(argv)
    (training if args.step == "training" else sample)(args)


if __name__ == "__main__":
    main()
