"""Decision D13 (protocol v2.3, Section 10.4): the registered panel drives the manifest, the holds, the label sample,
the control assignment of the judging plan and the runners' choice of hosted models.

Panel files with 'registered_hosted' are written to a temp folder; the real config files are only read. The
expected numbers are those of the table of Section 10.4. Synthetic screen results on the real frames (identifiers
and sources only).

Usage: python -I -X utf8 tests/test_panel_d13_v23.py
"""
import json
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

TMP = pathlib.Path("E:/claude/agentsControl_work/tmp/test_panel_d13_v23")
REAL_PATH = ROOT / "config" / "panel_v23.json"
REAL = json.loads(REAL_PATH.read_text(encoding="utf-8"))
MODELS = json.loads((ROOT / "config" / "models.json").read_text(encoding="utf-8"))["models"]
KEY = {m["n"]: m["key"] for m in MODELS}
F = frames_v23.frames()
TABLE = {(): {"labelled": 583, "harmful": 330, "safe": 253, "second": 388, "h60": 70, "api_ref": 130,
              "commercial_calls": 820, "control": "refusal_removed", "title": 12},
         (22,): {"labelled": 547, "harmful": 305, "safe": 242, "second": 360, "h60": 60, "api_ref": 120,
                 "commercial_calls": 800, "control": "refusal_removed_without_22", "title": 11},
         (23,): {"labelled": 547, "harmful": 305, "safe": 242, "second": 360, "h60": 60, "api_ref": 120,
                 "commercial_calls": 800, "control": "refusal_removed_without_23", "title": 11},
         (22, 23): {"labelled": 511, "harmful": 280, "safe": 231, "second": 332, "h60": 50, "api_ref": 110,
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


TESTS = [t_variants, t_before_the_decision, t_wrong_records_refused]


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
