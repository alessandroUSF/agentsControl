"""Label sample of protocol v2.3 (Section 9): which answers receive human labels.

Input: one record per answer inside the frames, with its model, prompt, source, side ("harmful" or "safe")
and screen result ("positive", "negative" or "none", from src/screen.py). The sample depends only on these
fields, the design file and the seed. No answer text, verdict or label is read, so the sample can be drawn and
its hash recorded before anybody opens an answer.

Cells. A cell is (model, side, screen result). Answers without content ("none") are never sampled: they hold
nothing to label and count as not harmful. Inside a cell the answers of each source are put in SHA-256 order
and the two sources are interleaved, so every prefix is balanced over sources. A cell supplies its quota
(config/panel_v23.json, "labels"); when it is too small, the shortfall goes to the other cell of the same model
and side. Inside (cell, source) the selected answers are a simple random sample, so the weight of a labelled
answer is (answers in the cell and source) / (labelled answers in the cell and source).

Expected cells (Section 9.2). The cells come from the design file, not from the answers: every model of the
panel file, both sides and both screen results. The report lists each of them in 'cells', also a cell without
any answer, with what it cannot fill ('short') and what of that the other cell of the same model and side cannot
take either ('unfilled'). 'shortages' keeps one entry per model and side with a shortfall, so a model or side
without any answer appears there too. An answer of a model or side outside the design stops the draw.

Every answer with content therefore has a positive, known chance of being labelled, unless its whole cell
stays without a label (reported as 'uncovered_answers'; zero with the registered quotas).

Derived sets, all subsets of the label sample:
  h60         the first answers of each refusal-removed model's screen-positive harmful cell (challenge set)
  api_ref     h60 plus a fixed number of other labelled answers of the primary panel (blind reference of the
              commercial judges)
  second      answers that receive an independent second label: every harmful-side answer and a fixed number
              of safe-side answers per model

Standard library only.
"""
import hashlib
import json
from pathlib import Path

DESIGN = Path(__file__).resolve().parents[1] / "config" / "panel_v23.json"
POSITIVE, NEGATIVE = "positive", "negative"
SIDES = ("harmful", "safe")


def load_design(path=DESIGN, without=None):
    """The design of the panel file. The hosted models that decision D13 leaves out ('registered_hosted') leave the
    primary panel and their group (Section 10.4); 'without' names hosted models to leave out instead (a what-if)."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    hosted = [int(x) for x in d.get("hosted_primary", [])]
    if without is None:
        reg = d.get("registered_hosted")
        without = [] if reg is None else [n for n in hosted if n not in {int(x) for x in reg}]
    left = {int(x) for x in without}
    if left - set(hosted):
        raise ValueError(f"only hosted members of the primary panel can be left out, not {sorted(left - set(hosted))}")
    groups = {g: sorted(int(x) for x in m if int(x) not in left) for g, m in d["groups"].items()}
    return {"labels": d["labels"], "groups": groups,
            "primary": sorted(int(x) for x in d["primary_panel"] if int(x) not in left),
            "group_of": {m: g for g, members in groups.items() for m in members}, "left_out": sorted(left)}


def quota(design, model, side):
    """Planned labels of one model and side: {"positive": n, "negative": n} (config/panel_v23.json, "labels")."""
    lab = design["labels"]
    if side == "harmful":
        return lab["harmful"][design["group_of"][model]]
    return lab["safe"]["primary" if model in design["primary"] else "commercial"]


def expected_cells(design):
    """Every cell that the design expects (Section 9.2): (model, side, screen) for every model of the panel file,
    both sides and both screen results, whether or not an answer exists for it."""
    return [(m, side, s) for m in sorted(design["group_of"]) for side in SIDES for s in (POSITIVE, NEGATIVE)]


def _h(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def cell_order(rows, seed):
    """Selection order of one cell: SHA-256 order inside each source, sources interleaved."""
    by_source = {}
    for r in rows:
        by_source.setdefault(r["source"], []).append(r)
    keyed = []
    for s, items in by_source.items():
        items.sort(key=lambda r: _h(seed, "answer", r["model"], r["prompt"]))
        keyed += [((i, _h(seed, "source", r["model"], r["side"], r["screen"], i, s)), r)
                  for i, r in enumerate(items)]
    return [r for _, r in sorted(keyed, key=lambda t: t[0])]


def _round_robin(pools, models, seed, tag, n):
    """n answers taken one per model in turn; models in SHA-256 order; pools: model -> ordered answers."""
    order = sorted(models, key=lambda m: _h(seed, tag, m))
    out, depth = [], 0
    while len(out) < n and any(len(pools.get(m, [])) > depth for m in order):
        for m in order:
            if len(out) < n and len(pools.get(m, [])) > depth:
                out.append(pools[m][depth])
        depth += 1
    return out


def select(answers, design=None):
    """Returns (rows, report). rows: the labelled answers, each a copy of its input record with 'weight',
    'cell_size', 'cell_labelled', 'h60', 'api_ref', 'second'. report: counts, 'shortages' (by model and side)
    and 'cells' (every expected cell of model, side and screen, with its shortage by screen)."""
    design = design or load_design()
    lab, seed = design["labels"], design["labels"]["seed"]
    primary = set(design["primary"])
    cells = {}
    for a in answers:
        if a["model"] not in design["group_of"] or a["side"] not in SIDES:
            raise ValueError(f"an answer lies outside the design: model {a['model']!r}, side {a['side']!r}")
        if a["screen"] in (POSITIVE, NEGATIVE):
            cells.setdefault((a["model"], a["side"], a["screen"]), []).append(a)
    ordered = {k: cell_order(v, seed) for k, v in cells.items()}
    chosen, shortages, listed = {}, [], []
    # Every expected (model, side) of the design, also one without any answer (Section 9.2): its two cells are
    # empty, so its whole quota is reported as a shortage instead of being skipped.
    for model, side in sorted({(m, s) for m, s, _ in expected_cells(design)}):
        q = quota(design, model, side)
        pos, neg = ordered.get((model, side, POSITIVE), []), ordered.get((model, side, NEGATIVE), [])
        own_pos, own_neg = min(q["positive"], len(pos)), min(q["negative"], len(neg))
        short_pos, short_neg = q["positive"] - own_pos, q["negative"] - own_neg
        n_pos, n_neg = min(len(pos), own_pos + short_neg), min(len(neg), own_neg + short_pos)
        if short_pos or short_neg:
            shortages.append({"model": model, "side": side, "short_positive": short_pos,
                              "short_negative": short_neg,
                              "unfilled": q["positive"] + q["negative"] - n_pos - n_neg})
        chosen[(model, side, POSITIVE)], chosen[(model, side, NEGATIVE)] = pos[:n_pos], neg[:n_neg]
        # by screen: what the cell cannot fill, and what of it the other cell of the same model and side
        # cannot take either (the other cell took n_other - own_other of it)
        by_screen = ((POSITIVE, len(pos), q["positive"], n_pos, short_pos, n_neg - own_neg),
                     (NEGATIVE, len(neg), q["negative"], n_neg, short_neg, n_pos - own_pos))
        for scr, size, want, n, short, taken in by_screen:
            listed.append({"model": model, "side": side, "screen": scr, "answers": size, "quota": want,
                           "labelled": n, "short": short, "unfilled": short - taken})

    rows = []
    for key in sorted(chosen):
        size, got = {}, {}
        for r in ordered.get(key, []):
            size[r["source"]] = size.get(r["source"], 0) + 1
        for r in chosen[key]:
            got[r["source"]] = got.get(r["source"], 0) + 1
        collapse = any(size[s] and not got.get(s) for s in size)     # a source without a labelled answer
        for i, r in enumerate(chosen[key]):
            n_cell, n_lab = (len(ordered[key]), len(chosen[key])) if collapse else \
                (size[r["source"]], got[r["source"]])
            rows.append(dict(r, rank=i, weight=n_cell / n_lab, cell_size=n_cell, cell_labelled=n_lab,
                             collapsed=collapse, h60=False, api_ref=False, second=r["side"] == "harmful"))
    by_cell = {}
    for r in rows:
        by_cell.setdefault((r["model"], r["side"], r["screen"]), []).append(r)

    for m in design["groups"]["refusal_removed"]:
        for r in by_cell.get((m, "harmful", POSITIVE), [])[: lab["h60_per_model"]]:
            r["h60"] = r["api_ref"] = True
    ref = lab["api_reference"]
    plan = (("harmful", POSITIVE, design["groups"]["instruct_open"], ref["harmful_positive"]),
            ("harmful", NEGATIVE, design["primary"], ref["harmful_negative"]),
            ("safe", POSITIVE, design["primary"], ref["safe_positive"]),
            ("safe", NEGATIVE, design["primary"], ref["safe_negative"]))
    missing = {}
    for side, scr, models, n in plan:
        pools = {m: [r for r in by_cell.get((m, side, scr), []) if not r["api_ref"]] for m in models}
        picked = _round_robin(pools, models, seed, f"api_ref|{side}|{scr}", n)
        for r in picked:
            r["api_ref"] = True
        if len(picked) < n:
            missing[side] = missing.get(side, 0) + n - len(picked)
    for side, n in missing.items():                       # shortfall: any other labelled primary answer, same side
        pools = {m: [r for s in (POSITIVE, NEGATIVE) for r in by_cell.get((m, side, s), []) if not r["api_ref"]]
                 for m in design["primary"]}
        for r in _round_robin(pools, design["primary"], seed, f"api_ref|{side}|fill", n):
            r["api_ref"] = True

    for (model, side) in sorted({(r["model"], r["side"]) for r in rows if r["side"] == "safe"}):
        k = lab["second_label_safe"]["primary" if model in primary else "commercial"]
        neg, pos = by_cell.get((model, side, NEGATIVE), []), by_cell.get((model, side, POSITIVE), [])
        mixed = [r for pair in zip(neg, pos) for r in pair] + neg[len(pos):] + pos[len(neg):]
        for r in mixed[:k]:
            r["second"] = True

    report = {"labelled": len(rows), "harmful": sum(r["side"] == "harmful" for r in rows),
              "safe": sum(r["side"] == "safe" for r in rows), "second": sum(r["second"] for r in rows),
              "h60": sum(r["h60"] for r in rows), "api_ref": sum(r["api_ref"] for r in rows),
              "collapsed_cells": sum(1 for k in chosen if chosen[k] and by_cell[k][0]["collapsed"]),
              "uncovered_answers": sum(len(v) for k, v in ordered.items() if not chosen.get(k)),
              "shortages": shortages, "cells": listed}
    return rows, report
