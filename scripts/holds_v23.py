"""Holds file of protocol v2.3 (Section 12.5): config/stage_holds.json, written again for the blocks of Section 12.3.

For every block, model and part, the paid calls that the plan allows and the pessimistic cost of one call, from
scripts/manifest_v23.py (same prices, same token assumptions, same counts from config/panel_v23.json). The runners
(src/spend_v23.py) hold, before every call, the pessimistic cost of the calls that remain in every unfinished block
of higher priority. Local models cost nothing and have no item.

Blocks (Section 12.3) and parts:
  1 pilot          respondents pilot_r1, pilot_r2 (20 answers each); judges pilot_r1, pilot_r2 (60 calls each)
  2 hosted answers frame_harmful (300), frame_safe (90)                         models 22 and 23
  3 hosted judges  own_harmful (600), control_harmful (600)                     models 22 and 23
  4 commercial     frame_harmful (60, the common set), frame_safe (90)          the ten commercial models
  5 hosted judges  own_safe (180), control_safe (180), label_blind (labelled answers), challenge_context, repeat
  6 commercial     own (300), control_harmful (120), reference_h1, reference_h2 (cut 4), control_safe (cut 2),
                   repeat (cut 1)
  7 commercial     challenge_blind, challenge_context (cut 3)
The sum of the items equals the pessimistic total of the manifest (checked here, block by block).

Usage: python -I scripts/holds_v23.py            print the items and the check
       python -I scripts/holds_v23.py --write    also write config/stage_holds.json
       python -I scripts/holds_v23.py --without 22,23   the same for a panel without hosted models, printed only
       python -I scripts/holds_v23.py --repricing FILE [--write]   after the pilot (Section 13.3, rule 4): the same
                                                 repricing file as the manifest (scripts/manifest_v23.py); with
                                                 --write the stored manifest must have been written with that file
The panel is the registered one: the hosted models that decision D13 leaves out ('registered_hosted' in
config/panel_v23.json) have no item (Section 10.4); before the decision both hosted models are in.
"""
import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cost_model as cm  # noqa: E402
import manifest_v23 as mv  # noqa: E402

OUT = ROOT / "config" / "stage_holds.json"
SC = "pessimistic"


def per_call_costs(prices, sc, keys):
    """US$ of one judging call, of one main-run answer (harmful, safe) and of one pilot answer, per model."""
    out = {}
    zero = {"safe": 0, "harmful": 0, "own": 0}
    for key in keys:
        judge = cm.judges(prices, sc, {"one call": 1}, batch=False, only=[key])[1][0][1]
        resp = {}
        for kind in ("harmful", "safe"):
            one = dict(zero, **{kind: 1})
            rows = cm.respondents(prices, dict(sc, pilot_rounds=0), True, direct_only=True, counts_all=zero,
                                  by_key={key: one})[1]
            resp[kind] = next(c for k, _, _, _, c in rows if k == key)
        rows = cm.respondents(prices, dict(sc, pilot_rounds=1), True, direct_only=True, counts_all=zero,
                              by_key={key: zero})[1]
        pilot = next(c for k, _, _, _, c in rows if k == key) / cm.RESP_PILOT
        out[key] = {"judge": judge, "harmful": resp["harmful"], "safe": resp["safe"], "pilot": pilot}
    return out


def build(design=None, without=(), repricing=None):
    """repricing: manifest_v23.load_repricing() of the repricing file (prices and scenarios of the repricing)."""
    d = design or json.loads(mv.DESIGN.read_text(encoding="utf-8"))
    d = mv.design_without(d, without) if without else d
    prices = repricing["prices"] if repricing else mv.pinned_prices(cm.load_prices())
    sc = (repricing["scenarios"] if repricing else mv.SCENARIOS)[SC]
    k = mv.counts(d)
    hosted = mv.hosted_keys(d)
    api = [m["key"] for m in cm.api_models()]
    com = [x for x in api if x not in mv.hosted_keys(json.loads(mv.DESIGN.read_text(encoding="utf-8")))]
    cost = per_call_costs(prices, sc, hosted + com)
    f = d["frames"]
    harmful, safe, common = 2 * f["harmful_per_source"], 2 * f["safe_per_source"], 2 * f["common_per_source"]
    cl = {label: (calls, cut) for label, calls, cut in k["commercial"]}
    hl = {label: (calls, cut) for label, calls, cut in k["hosted"]}
    items = []

    def add(block, role, key, part, calls, usd, cut=0):
        if calls:
            items.append({"block": block, "role": role, "model_key": key, "part": part, "calls": int(calls),
                          "usd_per_call": round(usd, 8), "cut": int(cut)})

    pilot_prompts = d["calls"]["pilot_prompts_per_api_respondent"]
    for key in hosted + com:
        for r in range(1, k["pilot_rounds"] + 1):
            add("1", "respondent", key, f"pilot_r{r}", pilot_prompts, cost[key]["pilot"])
    for key in com:
        for r in range(1, k["pilot_rounds"] + 1):
            label = "judge pilot, round 1" if r == 1 else f"judge pilot, round {r} (reserved)"
            add("1", "judge", key, f"pilot_r{r}", cl[label][0], cost[key]["judge"])
    for key in hosted:
        for r in range(1, k["pilot_rounds"] + 1):
            label = "judge pilot, round 1" if r == 1 else f"judge pilot, round {r} (reserved)"
            add("1", "judge", key, f"pilot_r{r}", hl[label][0], cost[key]["judge"])
        add("2", "respondent", key, "frame_harmful", harmful, cost[key]["harmful"])
        add("2", "respondent", key, "frame_safe", safe, cost[key]["safe"])
        add("3", "judge", key, "own_harmful", 2 * harmful, cost[key]["judge"])
        add("3", "judge", key, "control_harmful", 2 * harmful, cost[key]["judge"])
        assert hl["own answers, blind and in context"][0] == 2 * (harmful + safe)
        assert hl["controls, blind and in context"][0] == 2 * (harmful + safe)
        add("5", "judge", key, "own_safe", 2 * safe, cost[key]["judge"])
        add("5", "judge", key, "control_safe", 2 * safe, cost[key]["judge"])
        add("5", "judge", key, "label_blind", hl["labelled answers, blind"][0], cost[key]["judge"])
        add("5", "judge", key, "challenge_context", hl["challenge set, in context"][0], cost[key]["judge"])
        add("5", "judge", key, "repeat", hl["repeatability"][0], cost[key]["judge"], hl["repeatability"][1])
    for key in com:
        add("4", "respondent", key, "frame_harmful", common, cost[key]["harmful"])
        add("4", "respondent", key, "frame_safe", safe, cost[key]["safe"])
        c = cost[key]["judge"]
        add("6", "judge", key, "own", *cl["own answers, blind and in context"][:1], c)
        add("6", "judge", key, "control_harmful", cl["controls on harmful prompts, blind and in context"][0], c)
        add("6", "judge", key, "reference_h1", cl["blind reference: other labelled answers, first half"][0], c)
        n, cut = cl["blind reference: other labelled answers, second half"]
        add("6", "judge", key, "reference_h2", n, c, cut)
        n, cut = cl["controls on safe prompts, blind and in context"]
        add("6", "judge", key, "control_safe", n, c, cut)
        n, cut = cl["repeatability"]
        add("6", "judge", key, "repeat", n, c, cut)
        add("7", "judge", key, "challenge_blind", cl["blind reference: challenge set"][0], c)
        n, cut = cl["challenge set, in context"]
        add("7", "judge", key, "challenge_context", n, c, cut)
    for it in items:
        it["id"] = f"{it['block']}|{it['role']}|{it['model_key']}|{it['part']}"
    return items, d


def check(items, design, without=(), repricing=None):
    """The items must add up to the pessimistic manifest (with the same repricing), in total and per cut."""
    m = mv.build(design=json.loads(mv.DESIGN.read_text(encoding="utf-8")) if without else design, without=without,
                 repricing=repricing)
    tot = sum(it["calls"] * it["usd_per_call"] for it in items)
    out = {"items_total": round(tot, 2), "manifest_total": m["totals"][SC]}
    for c in (1, 2, 3, 4):
        out[f"cut_{c}"] = (round(sum(it["calls"] * it["usd_per_call"] for it in items if it["cut"] == c), 2),
                           next(x["saves_pessimistic"] for x in m["cuts"] if x["order"] == c))
    ok = abs(out["items_total"] - out["manifest_total"]) <= 0.02 and all(
        abs(a - b) <= 0.02 for k, (a, b) in ((k, v) for k, v in out.items() if k.startswith("cut_")))
    return ok, out


def stored_manifest_problem(man, rp, items):
    """Why the holds may not be written beside the stored manifest, or None. The stored manifest must carry the same
    repricing as this run (the file and every price snapshot file by its SHA-256, and the assumptions), and its
    pessimistic total and cuts must match the items (Section 12.4)."""
    if man is None:
        return "no stored manifest"
    if (man.get("repricing") or None) != (rp["meta"] if rp else None):
        return ("the stored manifest was not written with this repricing (its file, price snapshot or assumptions "
                "differ)")
    tot = sum(it["calls"] * it["usd_per_call"] for it in items)
    if abs(tot - float(man["totals"][SC])) > 0.02:
        return f"the stored manifest's {SC} total ${float(man['totals'][SC]):.2f} differs from the holds' ${tot:.2f}"
    for x in man["cuts"]:
        got = sum(it["calls"] * it["usd_per_call"] for it in items if it["cut"] == x["order"])
        if abs(got - float(x["saves_pessimistic"])) > 0.02:
            return f"cut {x['order']} of the stored manifest saves ${x['saves_pessimistic']:.2f}, the holds ${got:.2f}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--without", default="", help="hosted models left out of the panel, e.g. 22 or 22,23")
    ap.add_argument("--repricing", default="", help="repricing file after the pilot (scripts/manifest_v23.py)")
    a = ap.parse_args()
    rp = mv.load_repricing(a.repricing) if a.repricing else None
    d0 = json.loads(mv.DESIGN.read_text(encoding="utf-8"))
    what_if = bool(a.without)
    without = tuple(int(x) for x in a.without.split(",") if x) if what_if else mv.registered_without(d0)
    print(f"primary panel without {list(without)}" if without else "primary panel: every hosted model")
    items, d = build(without=without, repricing=rp)
    ok, chk = check(items, d, without, rp)
    by_block = {}
    for it in items:
        by_block[it["block"]] = by_block.get(it["block"], 0.0) + it["calls"] * it["usd_per_call"]
    for b in sorted(by_block):
        print(f"block {b}: pessimistic ${by_block[b]:8.2f}")
    print("check against the manifest:", chk, "OK" if ok else "MISMATCH")
    if not ok:
        sys.exit(1)
    if a.write:
        if what_if:
            sys.exit("--write follows decision D13 ('registered_hosted' in config/panel_v23.json); --without only prints")
        man = mv.OUT.read_bytes() if mv.OUT.exists() else b""
        bad = stored_manifest_problem(json.loads(man) if man else None, rp, items)
        if bad:
            sys.exit(f"{bad}: write the manifest first with scripts/manifest_v23.py "
                     + (f"--repricing {a.repricing} " if rp else "") + "--write")
        doc = {"_what": ("Holds of protocol v2.3 (Section 12.5), per block of Section 12.3: the paid calls planned for "
                         "each model and part, and the pessimistic cost of one call (manifest scenario 'pessimistic', "
                         "prices of scripts/manifest_v23.py). A block starts only if its pessimistic cost fits beside "
                         "that of every unfinished block of higher priority; the runners count the calls that remain "
                         "before every call (src/spend_v23.py). 'cut' names the cut of Section 12.4 that removes an "
                         "item's unsent calls. Written by scripts/holds_v23.py; re-made with the manifest after the "
                         "pilot (rule 4). Every change is a logged commit."),
               "protocol": "2.3", "scenario": SC, "written": dt.date.today().isoformat(),
               "registered_hosted": d0.get("registered_hosted"), "left_out": list(without),
               "repricing": rp["meta"] if rp else None,
               "manifest_sha256": hashlib.sha256(man).hexdigest() if man else None,
               "blocks": {"1": "pilot", "2": "missing answers of the primary panel",
                          "3": "primary panel on the harmful frame", "4": "answers of the commercial models",
                          "5": "primary panel, the rest", "6": "commercial judges",
                          "7": "commercial judges, challenge set"},
               "check": chk, "items": items}
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("written", OUT.relative_to(ROOT), len(items), "items")


if __name__ == "__main__":
    main()
