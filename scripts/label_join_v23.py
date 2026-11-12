"""Join the two label files, list the disagreements, record the state of every answer and lock (Section 9.3).

Steps:
  join      Reads the two filled sheets of the label sample with the files of the draw (scripts/label_draw_v23.py)
            and checks every row: known item ids, no missing or repeated row, valid values (rubric, Part B.1).
            Writes
              labels_joined_v23.csv        one row per answer of the sample: the labels of each labeller, the
                                           status of each (label, skipped, blank, incomplete, not_planned) and,
                                           where both gave harmful_content, whether they agree
              adjudication_sheet_v23.csv   one row per disagreement on harmful_content, for the two labellers:
                                           a neutral id, the two item ids, the request, the answer, the two
                                           labels, and empty fields 'adjudicated_harmful_content' (yes, no or
                                           unresolved) and 'reason'. No model, screen result, weight or verdict.
              join_report_v23.json         counts by labeller, agreement tables by side, warnings, hashes
  lock      Reads the joined file and the filled adjudication sheet and writes, once,
              labels_locked_v23.csv        one row per answer of the sample: its labels, the adjudicated label,
                                           the final label and its state
              labels_lock_v23.json         SHA-256 of the locked file and of every input; counts; time
            The lock happens before any verdict is joined with a label (Section 9.3); this script reads none.
  training  Joins the two filled sheets of one training round (Section 9.6): agreement by side and the list of
            items on which the labellers differ, for their discussion.

States at the lock (Section 9.3). 'labelled': the label that was planned exists (the agreed or adjudicated label
where two labels were planned, the first labeller's where one was planned). 'labelled_once': two labels were
planned and one exists; the answer keeps it. 'unknown': the adjudication ended unresolved, or the answer has no
label. No rule turns an unknown label into 'yes' or 'no'.

A row counts as a label when 'harmful_content' is filled. A row whose label fields are all empty is 'skipped'
when its comment says so (rubric, B.6) and 'blank' otherwise; a row with other fields but no harmful_content is
'incomplete'. All three leave the answer without that labeller's label. Comments are never copied.

The labellers fill copies of the sheets. The files of the draw directory must stay as written: every step checks
them against the hashes of the draw manifest, and the join report records the hash of each filled sheet.

Usage (from the project root; output directories are created; no file is ever overwritten):
  python -I scripts/label_join_v23.py join --draw DRAW_DIR --first FILLED_FIRST.csv --second FILLED_SECOND.csv --out DIR
  python -I scripts/label_join_v23.py lock --draw DRAW_DIR --join JOIN_DIR --adjudication FILLED_ADJ.csv --out DIR
                                           [--blank-as-unresolved]
  python -I scripts/label_join_v23.py training --draw TRAINING_DIR --round 1 --first FILLED.csv --second FILLED.csv --out DIR
The script prints counts and file names only.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import label_sheets_v23 as S  # noqa: E402

DRAWN = ("label_sample_v23.jsonl", "label_key_first_v23.csv", "label_key_second_v23.csv",
         "sheet_first_labeller.csv")
WHO = ("first", "second")
FIELDS = ("behaviour", "harmful_content", "hazard", "uplift", "confidence")
JOINED = ("answer_id", "side", "second", "item_id_first", "item_id_second") \
    + tuple(f"{w}_{f}" for w in WHO for f in ("status",) + FIELDS) + ("pair", "adjudication_id")
ADJUDICATION = ("adjudication_id", "item_id_first", "item_id_second", "request", "answer", "harmful_content_first",
                "harmful_content_second", "adjudicated_harmful_content", "reason")
LOCKED = ("answer_id", "model", "model_key", "prompt_id", "source", "side", "screen", "weight", "cell_size",
          "cell_labelled", "collapsed", "second", "h60", "api_ref", "ref_half") \
    + tuple(f"{w}_{f}" for w in WHO for f in ("status",) + FIELDS) + ("adjudicated", "label", "state",
                                                                       "unknown_reason")
ADJUDICATED = ("yes", "no", "unresolved")
CODE = (Path(__file__), ROOT / "scripts" / "label_sheets_v23.py")


def flag(v):
    return "true" if v else "false"


def state_of(planned_two, first, second, adjudicated):
    """(label, state, unknown_reason) of one answer (Section 9.3). first, second: 'yes', 'no' or '' (no label);
    adjudicated: 'yes', 'no', 'unresolved' or '' (no disagreement)."""
    if not planned_two:
        return (first, "labelled", "") if first else ("", "unknown", "no_label")
    if first and second:
        if first == second:
            return first, "labelled", ""
        if adjudicated in ("yes", "no"):
            return adjudicated, "labelled", ""
        return "", "unknown", "unresolved"
    if first or second:
        return first or second, "labelled_once", ""
    return "", "unknown", "no_label"


def join(args):
    S.check_template()
    draw, out = Path(args.draw), Path(args.out)
    names = ("labels_joined_v23.csv", "adjudication_sheet_v23.csv")
    S.refuse_existing([out / n for n in names + ("join_report_v23.json",)])
    manifest = S.check_manifest(draw / "label_draw_manifest_v23.json", DRAWN)
    seed = manifest["seed"]
    sample = S.read_jsonl(draw / "label_sample_v23.jsonl")
    keys = {w: S.read_key(draw / f"label_key_{w}_v23.csv") for w in WHO}
    by_answer = {r["answer_id"]: r for r in sample}
    if {k["answer_id"] for k in keys["first"].values()} != set(by_answer) or \
            {k["answer_id"] for k in keys["second"].values()} != {a for a, r in by_answer.items() if r["second"]}:
        raise SystemExit("the keys do not match the label sample")
    filled, reports = {}, {}
    for w, path in (("first", args.first), ("second", args.second)):
        rows, rep = S.read_filled_sheet(path, keys[w])
        filled[w] = {keys[w][iid]["answer_id"]: v for iid, v in rows.items()}
        reports[w] = dict(rep, sha256=S.sha256_file(path), path=S.rel(path))

    _, original = S.read_csv(draw / "sheet_first_labeller.csv")
    text = {keys["first"][r["item_id"]]["answer_id"]: (r["request"], r["answer"]) for r in original}
    joined, pairs, disagree = [], {"harmful": [], "safe": []}, []
    for a in sorted(by_answer):
        r = by_answer[a]
        row = {"answer_id": a, "side": r["side"], "second": flag(r["second"]),
               "item_id_first": r["item_id_first"], "item_id_second": r["item_id_second"]}
        for w in WHO:
            v = filled[w].get(a)
            row[f"{w}_status"] = v["status"] if v else "not_planned"
            for f in FIELDS:
                row[f"{w}_{f}"] = v["labels"][f] if v and v["status"] == "label" else ""
        h1, h2 = row["first_harmful_content"], row["second_harmful_content"]
        row["pair"] = "" if not (h1 and h2) else ("agree" if h1 == h2 else "disagree")
        if row["pair"]:
            pairs[r["side"]].append((h1, h2))
        if row["pair"] == "disagree":
            disagree.append(row)
        row["adjudication_id"] = ""
        joined.append(row)
    disagree.sort(key=lambda row: S.order_key(seed, "adjudication", row["answer_id"]))
    sheet = []
    for aid, row in zip(S.item_ids("D", len(disagree)), disagree):
        row["adjudication_id"] = aid
        request, answer = text[row["answer_id"]]
        sheet.append({"adjudication_id": aid, "item_id_first": row["item_id_first"],
                      "item_id_second": row["item_id_second"], "request": request, "answer": answer,
                      "harmful_content_first": row["first_harmful_content"],
                      "harmful_content_second": row["second_harmful_content"]})
    S.write_csv(out / "labels_joined_v23.csv", JOINED, joined)
    S.write_csv(out / "adjudication_sheet_v23.csv", ADJUDICATION, sheet, encoding=S.SHEET_ENCODING)
    report = {"step": "join", "protocol": "v2.3, Section 9.3", "created_utc": S.now_utc(), "command": sys.argv,
              "draw_manifest_sha256": S.sha256_file(draw / "label_draw_manifest_v23.json"),
              "labellers": reports,
              "answers": len(joined), "planned_two": sum(1 for r in joined if r["second"] == "true"),
              "agreement_by_side": {s: S.agreement(p) for s, p in pairs.items()},
              "disagreements": {s: sum(1 for x, y in p if x != y) for s, p in pairs.items()},
              "code": S.code_hashes(*CODE),
              "outputs": {n: S.sha256_file(out / n) for n in names}}
    S.write_json(out / "join_report_v23.json", report)
    for w in WHO:
        rep = reports[w]
        print(f"{w} labeller: {rep['rows']} rows {rep['status']}; text changed in {len(rep['text_changed'])} rows")
    print("disagreements on harmful_content:", report["disagreements"])
    for n in names + ("join_report_v23.json",):
        print("written", S.rel(out / n))


def lock(args):
    draw, jdir, out = Path(args.draw), Path(args.join), Path(args.out)
    S.refuse_existing([out / "labels_locked_v23.csv", out / "labels_lock_v23.json"])
    S.check_manifest(draw / "label_draw_manifest_v23.json", ("label_sample_v23.jsonl",))
    jrep = S.check_manifest(jdir / "join_report_v23.json", ("labels_joined_v23.csv", "adjudication_sheet_v23.csv"))
    sample = {r["answer_id"]: r for r in S.read_jsonl(draw / "label_sample_v23.jsonl")}
    _, joined = S.read_csv(jdir / "labels_joined_v23.csv")
    if {r["answer_id"] for r in joined} != set(sample):
        raise SystemExit("the joined file does not match the label sample")
    header, adj_rows = S.read_csv(args.adjudication)
    for c in ("adjudication_id", "adjudicated_harmful_content"):
        if c not in header:
            raise SystemExit(f"{args.adjudication}: column {c} missing")
    want = {r["adjudication_id"]: r for r in joined if r["adjudication_id"]}
    got, errors, blank = {}, [], []
    for r in adj_rows:
        aid = (r.get("adjudication_id") or "").strip()
        if not aid and not any((v or "").strip() for v in r.values()):
            continue
        if aid not in want or aid in got:
            errors.append(f"unknown or repeated adjudication id {aid!r}")
            continue
        v = (r.get("adjudicated_harmful_content") or "").strip().lower()
        if not v:
            blank.append(aid)
            if not args.blank_as_unresolved:
                continue
            v = "unresolved"
        if v not in ADJUDICATED:
            errors.append(f"{aid}: invalid adjudicated label")
            continue
        got[aid] = v
    absent = sorted(set(want) - set(got) - set(blank))
    if absent:
        errors.append(f"{len(absent)} disagreements are missing from the adjudication sheet, e.g. {absent[:5]}")
    if blank and not args.blank_as_unresolved:
        errors.append(f"{len(blank)} disagreements have no adjudicated label, e.g. {blank[:5]} "
                      f"(record 'unresolved', or pass --blank-as-unresolved)")
    if errors:
        raise SystemExit(f"{args.adjudication}: {len(errors)} problems:\n  " + "\n  ".join(errors[:50]))

    locked, counts = [], {"state": {}, "state_by_side": {}, "unknown_reason": {}, "skipped_by_labeller": {},
                          "blank_by_labeller": {}, "incomplete_by_labeller": {}}
    for r in sorted(joined, key=lambda r: r["answer_id"]):
        s = sample[r["answer_id"]]
        adjudicated = got.get(r["adjudication_id"], "") if r["adjudication_id"] else ""
        label, state, reason = state_of(s["second"], r["first_harmful_content"], r["second_harmful_content"],
                                        adjudicated)
        row = {k: s[k] for k in ("answer_id", "model", "model_key", "prompt_id", "source", "side", "screen",
                                 "weight", "cell_size", "cell_labelled", "ref_half")}
        row.update({k: flag(s[k]) for k in ("collapsed", "second", "h60", "api_ref")})
        row.update({k: r[k] for k in JOINED if k.startswith(("first_", "second_"))})
        row.update(adjudicated=adjudicated, label=label, state=state, unknown_reason=reason)
        locked.append(row)
        for name, k in (("state", state), ("state_by_side", f"{s['side']}|{state}"), ("unknown_reason", reason)):
            if k:
                counts[name][k] = counts[name].get(k, 0) + 1
        for w in WHO:
            for st in ("skipped", "blank", "incomplete"):
                if r[f"{w}_status"] == st:
                    d = counts[f"{st}_by_labeller"]
                    d[w] = d.get(w, 0) + 1
    S.write_csv(out / "labels_locked_v23.csv", LOCKED, locked)
    digest = S.sha256_file(out / "labels_locked_v23.csv")
    counts["adjudication"] = {v: sum(1 for x in got.values() if x == v) for v in ADJUDICATED}
    counts["adjudication"]["blank_recorded_as_unresolved"] = len(blank) if args.blank_as_unresolved else 0
    S.write_json(out / "labels_lock_v23.json", {
        "step": "lock", "protocol": "v2.3, Section 9.3", "locked_utc": S.now_utc(), "command": sys.argv,
        "locked_file": {"name": "labels_locked_v23.csv", "sha256": digest, "answers": len(locked)},
        "inputs": {"label_sample_v23.jsonl": S.sha256_file(draw / "label_sample_v23.jsonl"),
                   "label_draw_manifest_v23.json": S.sha256_file(draw / "label_draw_manifest_v23.json"),
                   "labels_joined_v23.csv": S.sha256_file(jdir / "labels_joined_v23.csv"),
                   "join_report_v23.json": S.sha256_file(jdir / "join_report_v23.json"),
                   "first_sheet_filled": jrep["labellers"]["first"]["sha256"],
                   "second_sheet_filled": jrep["labellers"]["second"]["sha256"],
                   "adjudication_sheet_filled": S.sha256_file(args.adjudication)},
        "code": S.code_hashes(*CODE), "counts": counts})
    print("states:", counts["state"], "| unknown:", counts["unknown_reason"])
    print("skipped by labeller:", counts["skipped_by_labeller"])
    print("locked", S.rel(out / "labels_locked_v23.csv"), "sha256", digest)


def training(args):
    S.check_template()
    draw, out = Path(args.draw), Path(args.out)
    disc, agr = f"training_round{args.round}_discussion.csv", f"training_round{args.round}_agreement.json"
    S.refuse_existing([out / disc, out / agr])
    sheet = f"training_round{args.round}.csv"
    S.check_manifest(draw / "training_manifest_v23.json", ("training_key_v23.csv", sheet))
    key = {k: v for k, v in S.read_key(draw / "training_key_v23.csv").items() if v["round"] == str(args.round)}
    if not key:
        raise SystemExit(f"no item of round {args.round} in the training key")
    filled = {w: S.read_filled_sheet(path, key) for w, path in (("first", args.first), ("second", args.second))}
    _, original = S.read_csv(draw / sheet)
    text = {r["item_id"]: (r["request"], r["answer"]) for r in original}
    pairs, behaviour, rows = {"harmful": [], "safe": []}, [], []
    for iid in sorted(key):
        a, b = filled["first"][0][iid], filled["second"][0][iid]
        la = a["labels"] if a["status"] == "label" else {f: "" for f in FIELDS}
        lb = b["labels"] if b["status"] == "label" else {f: "" for f in FIELDS}
        if la["harmful_content"] and lb["harmful_content"]:
            pairs[key[iid]["side"]].append((la["harmful_content"], lb["harmful_content"]))
        if la["behaviour"] and lb["behaviour"]:
            behaviour.append(la["behaviour"] == lb["behaviour"])
        differ = [f for f in ("harmful_content", "behaviour") if la[f] and lb[f] and la[f] != lb[f]]
        if differ:
            request, answer = text[iid]
            rows.append(dict({"item_id": iid, "request": request, "answer": answer, "differs_in": " ".join(differ)},
                             **{f"{f}_{w}": lab[f] for f in FIELDS for w, lab in (("first", la), ("second", lb))}))
    header = ("item_id", "request", "answer", "differs_in") + tuple(f"{f}_{w}" for f in FIELDS for w in WHO)
    S.write_csv(out / disc, header, rows, encoding=S.SHEET_ENCODING)
    S.write_json(out / agr, {
        "step": "training", "round": args.round, "protocol": "v2.3, Section 9.6", "created_utc": S.now_utc(),
        "labellers": {w: dict(filled[w][1], sha256=S.sha256_file(p))
                      for w, p in (("first", args.first), ("second", args.second))},
        "agreement_by_side": {s: S.agreement(p) for s, p in pairs.items()},
        "behaviour_raw_agreement": (sum(behaviour) / len(behaviour)) if behaviour else None,
        "items_to_discuss": len(rows), "discussion_sha256": S.sha256_file(out / disc)})
    print(f"round {args.round}: {len(key)} items; items to discuss: {len(rows)}")
    print("written", S.rel(out / disc), "and", S.rel(out / agr))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="step", required=True)
    p = sub.add_parser("join")
    p.add_argument("--draw", required=True, help="output directory of label_draw_v23.py sample")
    p.add_argument("--first", required=True, help="filled sheet of the first labeller")
    p.add_argument("--second", required=True, help="filled sheet of the second labeller")
    p.add_argument("--out", required=True)
    p = sub.add_parser("lock")
    p.add_argument("--draw", required=True)
    p.add_argument("--join", required=True, help="output directory of the join step")
    p.add_argument("--adjudication", required=True, help="filled adjudication sheet")
    p.add_argument("--blank-as-unresolved", action="store_true",
                   help="record a disagreement without an adjudicated label as unresolved (counted in the lock)")
    p.add_argument("--out", required=True)
    p = sub.add_parser("training")
    p.add_argument("--draw", required=True, help="output directory of label_draw_v23.py training")
    p.add_argument("--round", type=int, required=True, choices=(1, 2))
    p.add_argument("--first", required=True)
    p.add_argument("--second", required=True)
    p.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    {"join": join, "lock": lock, "training": training}[args.step](args)


if __name__ == "__main__":
    main()
