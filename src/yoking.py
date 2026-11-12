"""Type-matched yoking of control judges (protocol v2.3, Section 6).

For every prompt and every group of judges, one permutation sends each answer's author to the judge that
classifies that answer as a control. A judge never controls its own answer, an answer of a model from the
same developer, or an answer of a model with close lineage (config/panel_v23.json). Within a group every
judge therefore controls exactly one answer per prompt.

The assignment depends only on the ordered prompt identifiers, their strata, the panel file and the seed.
It uses SHA-256 ordering and no random number generator, so it is identical on every machine. It is made
before any answer is screened or judged.

Standard library only.
"""
import hashlib
import itertools
import json
from pathlib import Path

PANEL_FILE = Path(__file__).resolve().parents[1] / "config" / "panel_v23.json"
ENUMERATE_UP_TO = 7        # groups up to this size: every valid permutation is a candidate
SAMPLED_CANDIDATES = 200   # larger groups: this many hash-ordered valid permutations per prompt


def load_panel(path=PANEL_FILE):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"seed": d["yoking_seed"],
            "groups": {g: sorted(int(x) for x in m) for g, m in d["groups"].items()},
            "primary_panel": sorted(int(x) for x in d["primary_panel"]),
            "hosted_primary": sorted(int(x) for x in d.get("hosted_primary", [])),
            "developer": {int(k): v for k, v in d["developer"].items()},
            "close": {frozenset(int(x) for x in p) for p in d["close_lineage"]}}


def related(a, k, panel):
    return a == k or panel["developer"][a] == panel["developer"][k] or frozenset((a, k)) in panel["close"]


def allowed_controls(members, panel):
    """author -> admissible control judges inside the group."""
    return {a: [k for k in sorted(members) if not related(a, k, panel)] for a in sorted(members)}


def _h(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def candidates(members, allowed, seed, label, prompt_id, limit=SAMPLED_CANDIDATES):
    """Valid permutations for one prompt, as tuples aligned with sorted(members): position i holds the
    control of author sorted(members)[i]. Small groups: all of them. Larger groups: a hash-ordered sample."""
    members = sorted(members)

    def ok(perm):
        return all(k in allowed[a] for a, k in zip(members, perm))

    if len(members) <= ENUMERATE_UP_TO:
        return [perm for perm in itertools.permutations(members) if ok(perm)]
    out, seen, t = [], set(), 0
    while len(out) < limit:
        perm = tuple(sorted(members, key=lambda m: _h(seed, label, prompt_id, t, m)))
        t += 1
        if perm not in seen and ok(perm):
            seen.add(perm)
            out.append(perm)
        if t > 400 * limit:
            raise RuntimeError(f"too few valid permutations for group {label}")
    return out


def assign_controls(prompt_ids, strata, members, allowed, seed, label):
    """Greedy balanced assignment. prompt_ids: frame order. strata: prompt_id -> stratum name.
    Returns prompt_id -> {author: control}. Each step takes the valid permutation whose author-control pairs
    have been used least so far, first inside the prompt's stratum and then overall; SHA-256 breaks ties."""
    members = sorted(members)
    in_stratum, overall, out = {}, {}, {}
    fixed = candidates(members, allowed, seed, label, None) if len(members) <= ENUMERATE_UP_TO else None
    if fixed is not None and not fixed:
        raise RuntimeError(f"no valid permutation for group {label}")
    for pid in prompt_ids:
        s = strata[pid]
        cands = fixed if fixed is not None else candidates(members, allowed, seed, label, pid)

        def cost(perm):
            pairs = list(zip(members, perm))
            return (sum(in_stratum.get((s, a, k), 0) for a, k in pairs),
                    sum(overall.get((a, k), 0) for a, k in pairs),
                    _h(seed, label, pid, "tie", perm))

        best = min(cands, key=cost)
        out[pid] = dict(zip(members, best))
        for a, k in zip(members, best):
            in_stratum[(s, a, k)] = in_stratum.get((s, a, k), 0) + 1
            overall[(a, k)] = overall.get((a, k), 0) + 1
    return out


def pair_counts(assignment, strata=None):
    """(author, control) -> number of prompts, optionally per stratum: (stratum, author, control) -> n."""
    c = {}
    for pid, m in assignment.items():
        for a, k in m.items():
            key = (a, k) if strata is None else (strata[pid], a, k)
            c[key] = c.get(key, 0) + 1
    return c


def check(assignment, members, allowed):
    """Raise if any prompt lacks a valid one-to-one assignment."""
    members = sorted(members)
    for pid, m in assignment.items():
        if sorted(m) != members or sorted(m.values()) != members:
            raise ValueError(f"{pid}: not a permutation of the group")
        for a, k in m.items():
            if k not in allowed[a]:
                raise ValueError(f"{pid}: judge {k} may not control an answer of model {a}")
    return True
