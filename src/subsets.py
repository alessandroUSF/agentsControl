"""Frozen prompt subsets per respondent group (protocol v2.1, Section 5.2).

Every subset is a prefix of one seeded ordering per stratum, so the subsets are nested: the
60 harmful prompts of an added API model are also among Venice's 150, and every model that
runs a subset answers the same prompts. That keeps answers comparable across models.

Strata: (source, expected). Within a stratum the order is a seeded shuffle of the sorted ids,
then interleaved by category so that every prefix keeps the category mix.
Own prompts are subset by base prompt (all three framings of a base prompt stay together).
"""
import random

SEED = 20261110

SPECS = {
    # name: {(source, expected): count or None for all}, own base prompts (None = all)
    "all": {"bench": None, "own_base": None},
    "preregistered_api": {"bench": {("xstest", "comply"): None, ("or-bench-hard", "comply"): None,
                                    ("xstest", "refuse"): 30, ("or-bench-toxic", "refuse"): 30},
                          "own_base": None},
    "added_api": {"bench": {("xstest", "comply"): 50, ("or-bench-hard", "comply"): 50,
                            ("xstest", "refuse"): 30, ("or-bench-toxic", "refuse"): 30},
                  "own_base": 10},
    "venice": {"bench": {("xstest", "comply"): 50, ("or-bench-hard", "comply"): 50,
                         ("xstest", "refuse"): 75, ("or-bench-toxic", "refuse"): 75},
               "own_base": 10},
}


def base_prompt_id(row):
    """Base prompt identity (own prompts drop the framing suffix). Also the batching-adjacency
    unit and the own-subset selection unit (Section 5.2)."""
    if row["source"] == "own" and row["id"].endswith("-" + row["framing"]):
        return row["id"][: -(len(row["framing"]) + 1)]
    return row["id"]


def cluster_id(row):
    """Nested-CV outer-fold grouping unit (protocol v2.2, addition 5; RULING A, Section 9.1): all
    variants of a minimal pair / contrast share one cluster, so a near-duplicate pair never straddles
    a train/test fold. Everything else groups by its base prompt. NOTE: this is the CV fold-grouping
    unit only; the confirmatory bootstrap resamples by `base_prompt_id` (RULING A), not by cluster_id.
    The canonical `pair_group` lives in data/own/own_prompts.csv, so cluster_id is derived from it at
    analysis time and records stamped before a pair_group update are re-mapped."""
    pg = row.get("pair_group", "")
    if row["source"] == "own" and pg:
        return f"own-pair-{pg}"
    return base_prompt_id(row)


def ordered(rows, salt):
    """Seeded order that spreads every category evenly, so any prefix keeps the category mix.

    Each category is shuffled; its k-th item (of n) gets the position key (k + u) / n with u
    uniform in [0, 1); the sequence is sorted by that key.
    """
    rng = random.Random(f"{SEED}|{salt}")
    by_cat = {}
    for r in sorted(rows, key=lambda r: r["id"]):
        by_cat.setdefault(r["category"], []).append(r)
    keyed = []
    for c in sorted(by_cat):
        items = by_cat[c]
        rng.shuffle(items)
        n = len(items)
        keyed += [((k + rng.random()) / n, r["id"], r) for k, r in enumerate(items)]
    return [r for _, _, r in sorted(keyed, key=lambda t: (t[0], t[1]))]


def select(rows, name):
    spec = SPECS[name]
    bench = [r for r in rows if r["source"] != "own"]
    own = [r for r in rows if r["source"] == "own"]
    keep = []
    strata = {}
    for r in bench:
        strata.setdefault((r["source"], r["expected"]), []).append(r)
    for key in sorted(strata):
        n = None if spec["bench"] is None else spec["bench"].get(key, 0)
        seq = ordered(strata[key], f"{key[0]}|{key[1]}")
        keep += seq if n is None else seq[:n]
    base_rows = {}
    for r in own:
        base_rows.setdefault(base_prompt_id(r), {"id": base_prompt_id(r), "category": r["category"]})
    bases = [b["id"] for b in ordered(list(base_rows.values()), "own")]
    if spec["own_base"] is not None:
        bases = bases[: spec["own_base"]]
    chosen = set(bases)
    keep += [r for r in own if base_prompt_id(r) in chosen]
    return keep
