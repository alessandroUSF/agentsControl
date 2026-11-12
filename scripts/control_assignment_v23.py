"""Control judges of protocol v2.3 (Section 6): the assignment on the real frames, with its diagnostics.

For every group of judges and every frame on which the group acts as control, src/yoking.py sends each answer's
author to the judge that classifies that answer as a control. This script reads prompt identifiers and sources
only: no prompt text, no answer. The assignment exists before any answer is screened or judged.

  group             frames
  instruct_open     harmful frame, safe frame
  refusal_removed   harmful frame, safe frame
  commercial        common set, commercial safe controls
  refusal_removed_local   harmful frame, safe frame: the refusal-removed group without its hosted models (22
                          and 23), for the ten-local-model analysis (Sections 8.5 and 10.4)
  refusal_removed_without_22, refusal_removed_without_23
                          the same group without one of the two hosted models: the panel registered if only
                          the other one meets the conditions of Section 10.4 (decision D15)

Usage: python -I scripts/control_assignment_v23.py            print the diagnostics
       python -I scripts/control_assignment_v23.py --write    also write analysis/output/control_assignment_v23.json
"""
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import frames_v23  # noqa: E402
import yoking  # noqa: E402

OUT = ROOT / "analysis" / "output" / "control_assignment_v23.json"
PLAN = {"instruct_open": ("harmful", "safe"), "refusal_removed": ("harmful", "safe"),
        "commercial": ("common", "safe_commercial_controls")}
SAFE_FRAMES = {"safe", "safe_commercial_controls"}


def blocks(panel):
    """(name, members, frames) of every assignment: the full groups, then the refusal-removed group without each
    non-empty set of its hosted models. Without all of them the block is 'refusal_removed_local'."""
    out = [(group, panel["groups"][group], names) for group, names in PLAN.items()]
    hosted = sorted(panel["hosted_primary"])
    for r in range(1, len(hosted) + 1):
        for drop in itertools.combinations(hosted, r):
            name = ("refusal_removed_local" if r == len(hosted)
                    else "refusal_removed_without_" + "_".join(str(x) for x in drop))
            out.append((name, [m for m in panel["groups"]["refusal_removed"] if m not in drop], ("harmful", "safe")))
    return out


def label(group, frame):
    """Hash label of one assignment. Harmful-side frames use the group name alone (as in the simulations)."""
    return f"{group}|safe" if frame in SAFE_FRAMES else group


def build():
    panel, frames = yoking.load_panel(), frames_v23.frames()
    out = {"seed": panel["seed"], "blocks": []}
    for group, members, names in blocks(panel):
        allowed = yoking.allowed_controls(members, panel)
        for name in names:
            ids, source = frames[name]
            asg = yoking.assign_controls(ids, source, members, allowed, panel["seed"], label(group, name))
            yoking.check(asg, members, allowed)
            pairs, by_source = yoking.pair_counts(asg), yoking.pair_counts(asg, source)
            admissible = [(a, k) for a in members for k in allowed[a]]
            counts = [pairs.get(p, 0) for p in admissible]
            used = [c for c in counts if c]
            out["blocks"].append({
                "group": group, "frame": name, "prompts": len(ids), "judges": members,
                "allowed": {str(a): allowed[a] for a in members},
                "pairs_admissible": len(admissible), "pairs_never_used": len(counts) - len(used),
                "pair_count_min_used": min(used), "pair_count_max": max(counts),
                "pair_count_max_in_one_source": max(by_source.values()),
                "pair_counts": {f"{a}>{k}": pairs.get((a, k), 0) for a, k in admissible},
                "assignment": {p: {str(a): k for a, k in sorted(asg[p].items())} for p in ids}})
    canon = json.dumps([[b["group"], b["frame"], b["assignment"]] for b in out["blocks"]],
                       sort_keys=True, separators=(",", ":"))
    out["assignment_sha256"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    return out


def show(out):
    print(f"seed {out['seed']}; assignment SHA-256 {out['assignment_sha256']}")
    for b in out["blocks"]:
        print(f"== {b['group']} on {b['frame']}: {b['prompts']} prompts, judges {b['judges']}")
        print(f"   admissible pairs {b['pairs_admissible']}, never used {b['pairs_never_used']}; prompts per used "
              f"pair: min {b['pair_count_min_used']}, max {b['pair_count_max']}; "
              f"max inside one source {b['pair_count_max_in_one_source']}")
        if len(b["judges"]) <= yoking.ENUMERATE_UP_TO:
            for a in b["judges"]:
                row = ", ".join(f"{k}: {b['pair_counts'][f'{a}>{k}']}" for k in b["allowed"][str(a)])
                print(f"   answers of {a} controlled by {{{row}}}")


if __name__ == "__main__":
    result = build()
    show(result)
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(result, indent=1), encoding="utf-8", newline="\n")
        print("written", OUT)
