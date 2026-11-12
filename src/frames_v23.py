"""Prompt frames of protocol v2.3 (Section 5). This module reads identifiers and strata only, never prompt text.

Within each (source, expected) stratum the prompts follow the seeded order of subsets.ordered(). A frame is a
prefix of that order in every source stratum, so frames are nested and every model answers the same prompts.

  harmful prompts (expected "refuse"): rank < common_per_source   common set
                                       rank < harmful_per_source  harmful frame
                                       the rest                   harmful tail (pilot material)
  safe prompts (expected "comply"):    rank < commercial_safe_control_per_source  commercial safe controls
                                       rank < safe_per_source     safe frame
                                       the rest                   safe tail (pilot material)

Frame order is (rank, source): a smaller frame is always a prefix of a larger one.

Standard library only.
"""
import json
from pathlib import Path

import subsets

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "processed" / "sample.jsonl"
DESIGN = ROOT / "config" / "panel_v23.json"
HARMFUL, SAFE = "refuse", "comply"


def sizes(path=DESIGN):
    return json.loads(Path(path).read_text(encoding="utf-8"))["frames"]


def sample_index(path=SAMPLE):
    """prompt id -> (source, expected, rank inside the stratum's seeded order)."""
    strata = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                strata.setdefault((r["source"], r["expected"]), []).append(
                    {"id": r["id"], "category": r["category"]})
    out = {}
    for key in sorted(strata):
        for i, r in enumerate(subsets.ordered(strata[key], f"{key[0]}|{key[1]}")):
            out[r["id"]] = (key[0], key[1], i)
    return out


def frame(index, expected, per_source, start=0):
    """(ids in frame order, id -> source) for ranks start <= rank < per_source (None = to the end)."""
    ids = [p for p, (_, e, i) in index.items() if e == expected and i >= start
           and (per_source is None or i < per_source)]
    ids.sort(key=lambda p: (index[p][2], index[p][0]))
    return ids, {p: index[p][0] for p in ids}


def frames(index=None, n=None):
    """All frames of the protocol: name -> (ids, id -> source)."""
    index = index or sample_index()
    n = n or sizes()
    return {"common": frame(index, HARMFUL, n["common_per_source"]),
            "harmful": frame(index, HARMFUL, n["harmful_per_source"]),
            "harmful_tail": frame(index, HARMFUL, None, n["harmful_per_source"]),
            "safe": frame(index, SAFE, n["safe_per_source"]),
            "safe_commercial_controls": frame(index, SAFE, n["commercial_safe_control_per_source"]),
            "safe_tail": frame(index, SAFE, None, n["safe_per_source"])}


def pilot_plan(path=DESIGN):
    return json.loads(Path(path).read_text(encoding="utf-8"))["pilot"]


def pilot_rounds(index, excluded, plan=None, n=None):
    """Pilot prompts (Section 13.2): one dict per round with "harmful", "safe" and "api" identifier lists.

    Tail prompts in frame order, without `excluded`. Round r takes the next plan[side][source] free prompts of
    each source; "api" holds the first plan["api_per_source"] of each source and side (what API models answer)."""
    plan, n = plan or pilot_plan(), n or sizes()
    tails = {"harmful": frame(index, HARMFUL, None, n["harmful_per_source"]),
             "safe": frame(index, SAFE, None, n["safe_per_source"])}
    out = []
    for r in range(plan["rounds"]):
        rnd = {"harmful": [], "safe": [], "api": []}
        for side, (ids, src) in tails.items():
            for source, k in sorted(plan[side].items()):
                free = [p for p in ids if src[p] == source and p not in excluded]
                take = free[r * k:(r + 1) * k]
                if len(take) < k:
                    raise ValueError(f"pilot round {r + 1}: {len(take)} free {side} prompts of {source}, {k} needed")
                rnd[side] += take
                rnd["api"] += take[:plan["api_per_source"]]
        out.append(rnd)
    return out
