"""Decision D13 (protocol v2.3, Section 10.4): the registered panel drives the manifest, the holds, the label sample,
the control assignment of the judging plan and the runners' choice of hosted models.

Panel files with 'registered_hosted' are written to a temp folder; the real config files are only read. The
expected numbers are those of the table of Section 10.4. Synthetic screen results on the real frames (identifiers
and sources only).

Usage: python -I -X utf8 tests/test_panel_d13_v23.py
"""
import json
import os
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import frames_v23  # noqa: E402
import holds_v23 as hv  # noqa: E402
import label_sample as LS  # noqa: E402
import manifest_v23 as mv  # noqa: E402
import plan_v23 as P  # noqa: E402
import run_judges_v23 as R  # noqa: E402

TMP = pathlib.Path(os.environ.get("AC_TEST_TMP", "E:/claude/agentsControl_tests")) / "test_panel_d13_v23"
REAL_PATH = ROOT / "config" / "panel_v23.json"
REAL = json.loads(REAL_PATH.read_text(encoding="utf-8"))
MODELS = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]
KEY = {m["n"]: m["key"] for m in MODELS}
F = frames_v23.frames()
TABLE = {(): {"labelled": 567, "harmful": 325, "safe": 242, "second": 381, "h60": 70, "api_ref": 130,
              "commercial_calls": 820, "control": "refusal_removed", "title": 12},
         (22,): {"labelled": 531, "harmful": 300, "safe": 231, "second": 353, "h60": 60, "api_ref": 120,
                 "commercial_calls": 800, "control": "refusal_removed_without_22", "title": 11},
         (23,): {"labelled": 531, "harmful": 300, "safe": 231, "second": 353, "h60": 60, "api_ref": 120,
                 "commercial_calls": 800, "control": "refusal_removed_without_23", "title": 11},
         (22, 23): {"labelled": 495, "harmful": 275, "safe": 220, "second": 325, "h60": 50, "api_ref": 110,
                    "commercial_calls": 780, "control": "refusal_removed_local", "title": 10}}
RATES = {("commercial", "harmful"): 0.25, ("instruct_open", "harmful"): 0.30, ("refusal_removed", "harmful"): 0.70,
         ("commercial", "safe"): 0.88, ("instruct_open", "safe"): 0.84, ("refusal_removed", "safe"): 0.90}


def panel_file(left_out, pilot_hosted=None):
    d = json.loads(json.dumps(REAL))
    d["registered_hosted"] = [n for n in d["hosted_primary"] if n not in left_out]
    if pilot_hosted is not None:
        d["pilot_hosted"] = pilot_hosted
    p = TMP / f"panel_without_{'_'.join(map(str, left_out)) or 'none'}.json"
    p.write_text(json.dumps(d, indent=1), encoding="utf-8")
    return p, d


def answers(design, seed=1):
    rng, out, primary = random.Random(seed), [], set(design["primary"])
    for m in sorted(design["group_of"]):
        g = design["group_of"][m]
        for side, frame in (("harmful", "harmful" if m in primary else "common"), ("safe", "safe")):
            ids, src = F[frame]
            for p in ids:
                out.append({"model": m, "prompt": p, "source": src[p], "side": side,
                            "screen": "positive" if rng.random() < RATES[(g, side)] else "negative"})
    return out


def t_variants():
    ok = True
    for left, want in TABLE.items():
        path, d = panel_file(left)
        design = LS.load_design(path)
        rows, rep = LS.select(answers(design), design)
        got = {k: rep[k] for k in ("labelled", "harmful", "safe", "second", "h60", "api_ref")}
        ok_v = got == {k: want[k] for k in got} and rep["shortages"] == [] and design["left_out"] == list(left)
        ok_v &= not any(r["model"] in left for r in rows) and len(design["primary"]) == want["title"]
        ok_v &= mv.registered_without(d) == left
        man = mv.build(design=d, without=mv.registered_without(d))
        ok_v &= man["labelled_answers"] == want["labelled"] and man["left_out"] == list(left)
        ok_v &= man["judge_calls_per_model"]["commercial"] == want["commercial_calls"]
        items, dd = hv.build(design=d, without=mv.registered_without(d))
        hok, chk = hv.check(items, dd, mv.registered_without(d))
        ok_v &= hok and not any(it["model_key"] == KEY[n] for it in items for n in left)
        ok_v &= abs(chk["items_total"] - man["totals"]["pessimistic"]) <= 0.02
        panel = P.Panel(MODELS, d, registered_hosted=d["registered_hosted"])
        ok_v &= panel.removed_block == want["control"] and sorted(panel.left_out) == sorted(left)
        ok_v &= R.registered_hosted(d, "1") == d["registered_hosted"] == R.registered_hosted(d, "3")
        if not ok_v:
            print(f"  without {left}: label counts {got}, manifest {man['labelled_answers']} "
                  f"{man['judge_calls_per_model']}, holds {chk}, control {panel.removed_block}")
        ok &= ok_v
    return ok


def t_before_the_decision():
    ok = mv.registered_without(REAL) == () and LS.load_design(REAL_PATH)["left_out"] == []
    ok &= R.registered_hosted(REAL, "1") == REAL["hosted_primary"]
    try:
        R.registered_hosted(REAL, "3")
        ok = False
    except SystemExit as e:
        ok &= "decision D13 is not recorded" in str(e)
    path, d = panel_file((22,), pilot_hosted=[22, 23])        # an explicit pilot list wins for block 1 only
    ok &= R.registered_hosted(d, "1") == [22, 23] and R.registered_hosted(d, "5") == [23]
    return ok


def t_wrong_records_refused():
    ok = True
    for bad in (lambda: LS.load_design(REAL_PATH, without=[5]),
                lambda: mv.registered_without(dict(REAL, registered_hosted=[7])),
                lambda: mv.design_without(REAL, (4,))):
        try:
            bad()
            ok = False
        except ValueError:
            pass
    what_if = LS.load_design(REAL_PATH, without=[23])          # a what-if beside an unrecorded decision
    ok &= what_if["left_out"] == [23] and 23 not in what_if["primary"] and 23 not in what_if["group_of"]
    return ok


def _snapshot(name, factor=1.0, bump=None):
    """A price snapshot folder in TMP: the list of 8 November and the endpoint lists of 11 November (the registered
    prices), every price times factor; bump: (model id, factor) for one pinned endpoint only."""
    import shutil
    snap = TMP / name
    shutil.rmtree(snap, ignore_errors=True)
    snap.mkdir(parents=True)

    def scale(pr, f):
        for k, v in list(pr.items()):
            try:
                pr[k] = repr(float(v) * f)
            except (TypeError, ValueError):
                pass

    lst = json.loads((ROOT / "data" / "selection" / "2026-11-08" / "or_v1_models.json").read_text(encoding="utf-8"))
    for m in lst["data"]:
        scale(m["pricing"], factor)
    (snap / "or_v1_models.json").write_text(json.dumps(lst), encoding="utf-8")
    for f in (ROOT / "data" / "selection" / "2026-11-11" / "raw").glob("or_endpoints_*.json"):
        e = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(e.get("data"), dict):
            for x in e["data"].get("endpoints", []):
                f2 = factor * (bump[1] if bump and f.name == "or_endpoints_" + bump[0].replace("/", "_") + ".json"
                               else 1.0)
                scale(x["pricing"], f2)
        (snap / f.name).write_text(json.dumps(e), encoding="utf-8")
    return snap


def _repricing(name, snap, assumptions=None):
    path = TMP / f"{name}.json"
    path.write_text(json.dumps({"prices_snapshot": str(snap), "assumptions": assumptions or {},
                                "source": "synthetic test"}), encoding="utf-8")
    return mv.load_repricing(path)


def t_repricing():
    """Rule 4 of Section 13.3: the repricing file drives the manifest, the holds and the cuts together. The registered
    prices again give the registered manifest; a price rise of half moves every total and the holds with it, and the
    cuts that the books apply at the freeze are those that the manifest's cut savings call for; a fresh endpoint price
    of a pinned model is used, not the snapshot of 11 November; measured assumptions replace the registered ones; an
    unknown parameter or a snapshot without an endpoint list is refused."""
    import spend_v23 as S
    reg = mv.build(design=REAL)
    same = _repricing("rp_same", _snapshot("snap_same"))
    m0 = mv.build(design=REAL, repricing=same)
    ok = m0["totals"] == reg["totals"] and m0["repricing"]["sha256"] == same["meta"]["sha256"]
    rise = _repricing("rp_rise", _snapshot("snap_rise", 1.5))
    m1 = mv.build(design=REAL, repricing=rise)
    for n in ("expected", "pessimistic"):
        ok &= abs(m1["totals"][n] - 1.5 * reg["totals"][n]) <= 0.02 + 1e-9
    items, d = hv.build(design=REAL, repricing=rise)
    hok, chk = hv.check(items, d, (), rise)
    stored = json.loads(json.dumps(m1))                       # as written by manifest_v23.py --write
    ok &= hv.stored_manifest_problem(stored, rise, items) is None
    ok &= "repricing" in (hv.stored_manifest_problem(json.loads(json.dumps(reg)), rise, items) or "")
    ok &= "no stored manifest" in (hv.stored_manifest_problem(None, rise, items) or "")
    off = json.loads(json.dumps(m1))
    off["totals"]["pessimistic"] += 1.0
    ok &= "total" in (hv.stored_manifest_problem(off, rise, items) or "")
    off = json.loads(json.dumps(m1))
    off["cuts"][0]["saves_pessimistic"] += 1.0
    ok &= "cut 1" in (hv.stored_manifest_problem(off, rise, items) or "")
    snap = _snapshot("snap_moved", 1.5)                       # a snapshot file changed after the manifest was written
    before = _repricing("rp_moved", snap)
    m_before = json.loads(json.dumps(mv.build(design=REAL, repricing=before)))
    with open(snap / "or_v1_models.json", "a", encoding="utf-8") as f:
        f.write("\n")
    after = mv.load_repricing(TMP / "rp_moved.json")
    items_after = hv.build(design=REAL, repricing=after)[0]
    ok &= after["meta"]["sha256"] == before["meta"]["sha256"]
    ok &= "repricing" in (hv.stored_manifest_problem(m_before, after, items_after) or "")
    ok &= hok and abs(chk["items_total"] - m1["totals"]["pessimistic"]) <= 0.02
    ceiling, total = REAL["budget"]["freeze_ceiling_usd"], m1["totals"]["pessimistic"]
    ok &= total > ceiling
    want, left = [], total
    for c in m1["cuts"]:
        if left <= ceiling:
            break
        want.append(c["order"])
        left -= c["saves_pessimistic"]
    for it in items:
        it["id"] = f"{it['block']}|{it['role']}|{it['model_key']}|{it['part']}"
    books = S.Books("repricing", holds={"items": items}, study_cap=REAL["budget"]["cap_usd"],
                    ledger=TMP / "ledger_repricing.jsonl", write=False)
    fits, msg = books.cut_check("freeze", apply_cuts=False, limit=ceiling)
    ok &= fits == (left <= ceiling + 0.02) and sorted(books.cuts) == want
    if not ok:
        print("  cuts:", want, sorted(books.cuts), msg, total, left)
    pinned = next(m for m in MODELS if m.get("provider_order"))
    bump = _repricing("rp_bump", _snapshot("snap_bump", 1.0, (pinned["model"], 2.0)))
    m2 = mv.build(design=REAL, repricing=bump)
    k = pinned["key"]
    ok &= abs(m2["per_model"][k]["pessimistic"] - 2 * reg["per_model"][k]["pessimistic"]) <= 0.02
    ok &= all(abs(m2["per_model"][x]["pessimistic"] - reg["per_model"][x]["pessimistic"]) <= 0.01
              for x in reg["per_model"] if x != k)
    meas = _repricing("rp_meas", _snapshot("snap_meas"), {"pessimistic": {"judge_in": 9000, "retry": 0.25}})
    m3 = mv.build(design=REAL, repricing=meas)
    ok &= m3["totals"]["pessimistic"] > reg["totals"]["pessimistic"] and m3["totals"]["expected"] == reg["totals"][
        "expected"]
    items3, d3 = hv.build(design=REAL, repricing=meas)
    ok &= hv.check(items3, d3, (), meas)[0]
    for bad in ({"pessimistic": {"judge_tokens": 1}}, {"optimistic": {"retry": 0.1}}):
        try:
            _repricing("rp_bad", _snapshot("snap_bad"), bad)
            ok = False
        except ValueError:
            pass
    gone = _snapshot("snap_gone")
    (gone / ("or_endpoints_" + pinned["model"].replace("/", "_") + ".json")).unlink()
    try:
        _repricing("rp_gone", gone)
        ok = False
    except ValueError:
        pass
    return ok


TESTS = [t_variants, t_before_the_decision, t_wrong_records_refused, t_repricing]


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    want = set(sys.argv[1:])
    passed = failed = 0
    for t in TESTS:
        if want and t.__name__ not in want:
            continue
        try:
            ok = bool(t())
        except Exception:
            import traceback
            traceback.print_exc()
            ok = False
        print(("PASS " if ok else "FAIL ") + t.__name__)
        passed += ok
        failed += not ok
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
