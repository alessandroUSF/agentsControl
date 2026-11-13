"""Call manifest and budget of protocol v2.3 (Section 12).

Every API call that the protocol allows, in blocks. The counts come from config/panel_v23.json (frames, label
sample, call blocks); none is typed here. Prices: the 8 November 2026 snapshot and the token assumptions of
scripts/cost_model.py. Two scenarios:
  expected      judge prompt 3,550 tokens, 380 output tokens with reasoning, 5% retries
  pessimistic   judge prompt 4,800 tokens, 720 output tokens, 15% retries, no cache hits; the respondents'
                reasoning AND visible answer doubled
The judge prompt is longer than in scripts/cost_model.py because Part A of labels/RUBRIC.md grew (RUBRIC_GROWTH).
Caching (Section 11.3 as revised on 12 November 2026): none, in either presentation. Every request opens with the
request and the answer under judgment and puts the rubric after them, so no request opens with a repeated prefix
that a provider could cache; no cache is requested from Anthropic (no system block is sent) and every call is priced
uncached (CACHED_PROVIDERS is empty). The scenario keys of scripts/cost_model.py that describe caching stay in the
table and have no effect. A row of calls in both presentations is half blind (judge_rows).
Reservations use the pessimistic figures. Both pilot rounds are reserved in full; the second one runs only
under the adaptation rule of the pilot plan. A block marked "cut n" is the n-th block dropped if repricing
after the pilot puts the pessimistic total above the freeze ceiling; blocks of the primary panel are never cut.

The panel is the registered one: once decision D13 is recorded ('registered_hosted' in config/panel_v23.json), the
hosted models it leaves out are left out here too (Section 10.4); before that, both hosted models are in.

The repricing after the pilot (Section 13.3, rule 4) gives a repricing file (load_repricing): a price snapshot taken
on the day and the token assumptions measured in the pilot. With it, every price comes from that snapshot (the
endpoint prices of the pinned models too, never those of 11 November) and every scenario parameter it names replaces
the registered one; the holds (scripts/holds_v23.py) are made from the same file.

Usage: python -I scripts/manifest_v23.py            print the manifest of the registered panel
       python -I scripts/manifest_v23.py --write    also write analysis/output/manifest_v23.json
       python -I scripts/manifest_v23.py --without 22      (or 23, or 22,23) the manifest of a panel without these
                                                           hosted models, whatever D13 says; printed, never written
       python -I scripts/manifest_v23.py --repricing FILE [--write]   the manifest repriced after the pilot
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cost_model as cm  # noqa: E402

DESIGN = ROOT / "config" / "panel_v23.json"
OUT = ROOT / "analysis" / "output" / "manifest_v23.json"
MODELS_CFG = ROOT / "config" / "models.json"
SNAP11 = ROOT / "data" / "selection" / "2026-11-11" / "raw"
SCENARIOS = {"expected": dict(cm.SCENARIOS["expected"]),
             "pessimistic": dict(cm.SCENARIOS["pessimistic"], vis_mult=2.0)}
# Part A of labels/RUBRIC.md is in every judge prompt. As decided by the PI on 11 November 2026 (decision D12) it had
# 7,176 characters; the text of 9 November, on which scripts/cost_model.py rests, had 4,165. On 13 November 2026 the
# PI added two sentences (decisions D12 and D21) and the class clarification (decision D25): it had 7,943. The
# 3,778 further characters count as 1,050 tokens in the expected scenario (about 3.75 characters per token: 1,008,
# rounded up to 50) and as 1,300 in the pessimistic one (about 3.0: 1,260, rounded up to 50). The same day the PI
# removed two phrases (decision D27): 7,878 characters; the counts for 7,943 are kept, a small overestimate. If
# Part A changes again (training amendment), they change.
RUBRIC_GROWTH = {"expected": 1050, "pessimistic": 1300}
for _name, _tokens in RUBRIC_GROWTH.items():
    SCENARIOS[_name]["judge_in"] += _tokens
    SCENARIOS[_name]["prefix"] += _tokens
# Parameters of a scenario that a repricing file may set (absolute values, not increments): those of
# scripts/cost_model.py (judge prompt, cached prefix, visible and reasoning output of a judge, multipliers of the
# respondents' reasoning and visible answer, retry share, cache hits) and the respondents' prompt tokens, visible
# output by kind of prompt and reasoning tokens by model key.
SCENARIO_KEYS = ("judge_in", "prefix", "judge_vis", "judge_reason", "resp_mult", "vis_mult", "retry", "cache_hits",
                 "resp_in", "resp_out", "reasoning_by_key")
CUTS = {1: "repeatability of the API judges is not measured",
        2: "no author-versus-control comparison on safe prompts for the commercial judges",
        3: "no in-context verdicts of the commercial judges on the challenge set (blind verdicts remain)",
        4: "blind accuracy of the commercial judges rests on the challenge set, half of the other reference "
           "answers and their own labelled answers"}


def hosted_keys(design):
    """Keys of the hosted members of the primary panel: 'hosted_primary' of the panel file, as field 'n' of
    config/models.json (models 22 and 23 since decision D15)."""
    by_n = {m["n"]: m["key"] for m in json.loads(MODELS_CFG.read_text(encoding="utf-8"))["models"]}
    return [by_n[n] for n in design["hosted_primary"]]


def design_without(d, without):
    """The design of a panel without some hosted models (Section 10.4): they leave the primary panel, its group
    and the hosted list; every count that depends on the panel follows from the panel file."""
    d = json.loads(json.dumps(d))
    left_out = set(without)
    unknown = left_out - set(d["hosted_primary"])
    if unknown:
        raise ValueError(f"only hosted members of the primary panel can be left out, not {sorted(unknown)}")
    d["hosted_primary"] = [n for n in d["hosted_primary"] if n not in left_out]
    d["primary_panel"] = [n for n in d["primary_panel"] if n not in left_out]
    for g in d["groups"]:
        d["groups"][g] = [n for n in d["groups"][g] if n not in left_out]
    return d


def registered_without(design):
    """Decision D13 (Section 10.4): the hosted models that 'registered_hosted' of the panel file leaves out of the
    primary panel; none while the decision is not recorded."""
    if "registered_hosted" not in design:
        return ()
    reg = {int(x) for x in design["registered_hosted"]}
    unknown = reg - set(design["hosted_primary"])
    if unknown:
        raise ValueError(f"registered_hosted names models that are not hosted members of the panel: {sorted(unknown)}")
    return tuple(n for n in design["hosted_primary"] if n not in reg)


def pinned_prices(prices, snapshot=None):
    """Decision D16: a model reached through OpenRouter is priced at the endpoint it is pinned to
    ('provider_order' of config/models.json), from the endpoint snapshot of 11 November 2026, or from the snapshot
    of a repricing (snapshot: its folder)."""
    out = dict(prices)
    snap = Path(snapshot) if snapshot else SNAP11
    for m in cm.api_models():
        order = m.get("provider_order")
        if not order:
            continue
        f = snap / ("or_endpoints_" + m["model"].replace("/", "_") + ".json")
        if not f.exists():
            raise ValueError(f"the price snapshot {snap} has no endpoint list for {m['model']} ({f.name})")
        e = next((x for x in json.loads(f.read_text(encoding="utf-8"))["data"]["endpoints"] if x["tag"] == order[0]),
                 None)
        if e is None:
            raise ValueError(f"{f.name}: no endpoint {order[0]!r}, the one {m['key']} is pinned to")
        p = e["pricing"]
        out[m["model"]] = {"in": float(p["prompt"]) * 1e6, "out": float(p["completion"]) * 1e6,
                           "cache": float(p.get("input_cache_read") or p["prompt"]) * 1e6,
                           "write": float(p.get("input_cache_write") or p["prompt"]) * 1e6}
    return out


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_repricing(path):
    """Rule 4 of Section 13.3: the repricing after the pilot. The file (JSON):
      {"prices_snapshot": folder (relative to the repository, or absolute) with or_v1_models.json (the OpenRouter
                          model list) and, for every pinned model, or_endpoints_<model id, '/' as '_'>.json, taken on
                          the day of the repricing,
       "assumptions": {"expected": {...}, "pessimistic": {...}}: the scenario parameters measured in the pilot
                          (SCENARIO_KEYS, absolute values); a parameter not named keeps its registered value,
       "source": free text, e.g. the pilot report and round the values come from}
    Returns {"meta": {file, sha256, snapshot, snapshot files with their sha256}, "prices", "scenarios"}. An unknown
    parameter or scenario, or a snapshot without the list or an endpoint file, is refused."""
    path = Path(path)
    rp = json.loads(path.read_text(encoding="utf-8"))
    snap = Path(rp["prices_snapshot"])
    snap = snap if snap.is_absolute() else ROOT / snap
    listing = snap / "or_v1_models.json"
    if not listing.exists():
        raise ValueError(f"the price snapshot {snap} has no or_v1_models.json")
    scen = json.loads(json.dumps(SCENARIOS))
    for name, over in (rp.get("assumptions") or {}).items():
        if name not in scen:
            raise ValueError(f"unknown scenario {name!r} in {path.name}")
        bad = set(over) - set(SCENARIO_KEYS)
        if bad:
            raise ValueError(f"unknown parameters {sorted(bad)} for scenario {name!r} in {path.name}")
        scen[name].update(over)
    prices = pinned_prices(cm.load_prices(listing), snap)
    used = [listing] + sorted(snap.glob("or_endpoints_*.json"))
    try:
        snap_name = str(snap.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        snap_name = str(snap)
    meta = {"file": path.name, "sha256": _sha(path), "snapshot": snap_name, "source": rp.get("source"),
            "snapshot_files": {p.name: _sha(p) for p in used},
            "assumptions": rp.get("assumptions") or {}}
    return {"meta": meta, "prices": prices, "scenarios": scen}


def counts(d):
    f, lab, c, g = d["frames"], d["labels"], d["calls"], d["groups"]
    common, harmful, safe = 2 * f["common_per_source"], 2 * f["harmful_per_source"], 2 * f["safe_per_source"]
    h60 = lab["h60_per_model"] * len(g["refusal_removed"])
    other = sum(lab["api_reference"].values())
    labelled = sum(sum(lab["harmful"][k].values()) * len(g[k]) for k in g) \
        + sum(lab["safe"]["primary"].values()) * len(d["primary_panel"]) \
        + sum(lab["safe"]["commercial"].values()) * len(g["commercial"])
    pilot, rep = c["pilot_calls_per_api_judge"], c["repeatability_per_api_judge"]
    rounds = c["pilot_rounds_reserved"]
    com = [("own answers, blind and in context", 2 * (common + safe), 0),
           ("controls on harmful prompts, blind and in context", 2 * common, 0),
           ("controls on safe prompts, blind and in context", 4 * f["commercial_safe_control_per_source"], 2),
           ("blind reference: challenge set", h60, 0),
           ("blind reference: other labelled answers, first half", other - other // 2, 0),
           ("blind reference: other labelled answers, second half", other // 2, 4),
           ("challenge set, in context", h60 if c["commercial_h60_in_context"] else 0, 3),
           ("judge pilot, round 1", pilot, 0)] \
        + [(f"judge pilot, round {r} (reserved)", pilot, 0) for r in range(2, rounds + 1)] \
        + [("repeatability", rep, 1)]
    ven = [("own answers, blind and in context", 2 * (harmful + safe), 0),
           ("controls, blind and in context", 2 * (harmful + safe), 0),
           ("challenge set, in context", h60, 0),
           ("labelled answers, blind", labelled if c["primary_blind_on_all_labels"] else h60 + other, 0),
           ("judge pilot, round 1", pilot, 0)] \
        + [(f"judge pilot, round {r} (reserved)", pilot, 0) for r in range(2, rounds + 1)] \
        + [("repeatability", rep, 1)]
    resp = {"commercial": {"safe": safe, "harmful": common, "own": 0},
            "hosted": {"safe": safe, "harmful": harmful, "own": 0}}
    return {"commercial": com, "hosted": ven, "resp": resp, "labelled": labelled, "pilot_rounds": rounds}


# Prompt caching (Section 11.3, since 12 November 2026): the rubric follows the answer in both presentations, so no
# request opens with a repeated prefix long enough for a provider's cache, and no provider is priced with one.
CACHED_PROVIDERS = ()


def blind_share(label):
    """Share of a block's judge calls made in the blind presentation (Sections 11.2 and 11.4)."""
    if "blind and in context" in label or label.startswith(("judge pilot", "repeatability")):
        return 0.5
    if label.endswith("in context"):
        return 0.0
    if "blind" in label:
        return 1.0
    raise ValueError(f"no presentation for the block '{label}'")


def judge_rows(prices, sc, label, calls, keys):
    """(model key, US$) of one block of judge calls. A provider in CACHED_PROVIDERS (none since 12 November 2026)
    would have its blind calls priced with a cached prefix."""
    b, n, rows = blind_share(label), calls * (1 + sc["retry"]), []
    for m in cm.api_models():
        if m["key"] not in keys:
            continue
        pr, _ = cm.price(prices, cm.SNAP_ID.get(m["key"], m["model"]), batch=False)
        r = m.get("effort") is not None
        c = n * (b * cm.judge_call_cost(pr, sc, reasoning=r, cache=m["provider"] in CACHED_PROVIDERS)
                 + (1 - b) * cm.judge_call_cost(pr, sc, reasoning=r, cache=False))
        rows.append((m["key"], c))
    return rows


def build(prices=None, design=None, without=(), repricing=None):
    """repricing: load_repricing() of the repricing file; its prices and scenarios replace the registered ones."""
    if repricing:
        prices, scen = repricing["prices"], repricing["scenarios"]
    else:
        prices, scen = pinned_prices(prices or cm.load_prices()), SCENARIOS
    d = design or json.loads(DESIGN.read_text(encoding="utf-8"))
    d = design_without(d, without) if without else d
    k = counts(d)
    api = [m for m in cm.api_models() if m["n"] not in set(without)]
    keep = {m["key"] for m in api}
    hosted = hosted_keys(d)
    com = [m["key"] for m in api if m["key"] not in hosted]
    provider = {m["key"]: ("openrouter" if m["provider"] == "openai_compatible" else m["provider"]) for m in api}
    blocks, per_model = [], {}

    def add(block_id, who, label, calls, models, cut, cost_rows):
        b = {"id": block_id, "who": who, "label": label, "calls_per_model": calls, "models": len(models), "cut": cut}
        for name in scen:
            b[name] = round(sum(c for _, c in cost_rows[name]), 4)
            for key, c in cost_rows[name]:
                per_model.setdefault(key, {n: 0.0 for n in scen})[name] += c
        blocks.append(b)

    def resp_rows(sc, rounds, zero):
        by = {key: k["resp"]["hosted"] for key in hosted}
        cnt = k["resp"]["commercial"]
        if zero:
            by, cnt = {key: {x: 0 for x in cnt} for key in hosted}, {x: 0 for x in cnt}
        _, rows = cm.respondents(prices, dict(sc, pilot_rounds=rounds), True, direct_only=True, counts_all=cnt, by_key=by)
        return [(key, c) for key, _, _, _, c in rows if key in keep]

    add("resp.main", "respondents", "answers to the frame prompts", None, api, 0,
        {n: resp_rows(sc, 0, False) for n, sc in scen.items()})
    for r in range(1, k["pilot_rounds"] + 1):
        add(f"resp.pilot{r}", "respondents", f"respondent pilot, round {r}" + (" (reserved)" if r > 1 else ""),
            d["calls"]["pilot_prompts_per_api_respondent"], api, 0,
            {n: resp_rows(sc, 1, True) for n, sc in scen.items()})
    for who, keys in (("commercial", com), ("hosted", hosted)):
        for i, (label, calls, cut) in enumerate(k[who]):
            if calls:
                add(f"judge.{who}.{i + 1}", f"{who} judges", label, calls, keys, cut,
                    {n: judge_rows(prices, sc, label, calls, keys) for n, sc in scen.items()})
    totals = {n: round(sum(b[n] for b in blocks), 2) for n in scen}
    by_provider = {}
    for key, c in per_model.items():
        p = by_provider.setdefault(provider[key], {n: 0.0 for n in scen})
        for n in scen:
            p[n] += c[n]
    calls = {who: sum(c for _, c, _ in k[who]) for who in ("commercial", "hosted")}
    return {"primary_panel": d["primary_panel"], "left_out": sorted(without),
            "repricing": repricing["meta"] if repricing else None,
            "blocks": blocks, "totals": totals, "cap_usd": d["budget"]["cap_usd"],
            "freeze_ceiling_usd": d["budget"]["freeze_ceiling_usd"], "judge_calls_per_model": calls,
            "labelled_answers": k["labelled"],
            "per_provider": {p: {n: round(v, 2) for n, v in c.items()} for p, c in sorted(by_provider.items())},
            "per_model": {key: {n: round(v, 2) for n, v in c.items()} for key, c in per_model.items()},
            "cuts": [{"order": o, "loses": CUTS[o],
                      "saves_pessimistic": round(sum(b["pessimistic"] for b in blocks if b["cut"] == o), 2)}
                     for o in sorted(CUTS)]}


def show(m):
    print(f"primary panel: {len(m['primary_panel'])} models {m['primary_panel']}"
          + (f"; left out: {m['left_out']}" if m["left_out"] else ""))
    print(f"{'block':58s} {'calls':>6s} {'models':>6s} {'expected':>9s} {'pessimistic':>11s}  cut")
    who = None
    for b in m["blocks"]:
        if b["who"] != who:
            who = b["who"]
            sub = [x for x in m["blocks"] if x["who"] == who]
            print(f"-- {who}: expected ${sum(x['expected'] for x in sub):.2f}, "
                  f"pessimistic ${sum(x['pessimistic'] for x in sub):.2f}")
        calls = "" if b["calls_per_model"] is None else str(b["calls_per_model"])
        print(f"  {b['label']:56s} {calls:>6s} {b['models']:6d} {b['expected']:9.2f} {b['pessimistic']:11.2f}  "
              f"{b['cut'] or ''}")
    t = m["totals"]
    print(f"TOTAL expected ${t['expected']:.2f}; pessimistic ${t['pessimistic']:.2f}; cap ${m['cap_usd']:.0f}; "
          f"headroom ${m['cap_usd'] - t['pessimistic']:.2f}; freeze ceiling ${m['freeze_ceiling_usd']:.0f}")
    print("judge calls per model:", m["judge_calls_per_model"], "| labelled answers:", m["labelled_answers"])
    print("per provider:", " ".join(f"[{p} expected ${c['expected']:.2f} pessimistic ${c['pessimistic']:.2f}]"
                                    for p, c in m["per_provider"].items()))
    print("per model, pessimistic:", " ".join(f"[{k} ${c['pessimistic']:.2f}]" for k, c in m["per_model"].items()))
    left = t["pessimistic"]
    for c in m["cuts"]:
        left -= c["saves_pessimistic"]
        print(f"  cut {c['order']}: saves ${c['saves_pessimistic']:.2f} -> ${left:.2f}; loses: {c['loses']}")


if __name__ == "__main__":
    what_if = "--without" in sys.argv
    if what_if:
        left_out = tuple(int(x) for x in sys.argv[sys.argv.index("--without") + 1].split(",") if x)
    else:
        left_out = registered_without(json.loads(DESIGN.read_text(encoding="utf-8")))
    rep = load_repricing(sys.argv[sys.argv.index("--repricing") + 1]) if "--repricing" in sys.argv else None
    manifest = build(without=left_out, repricing=rep)
    if rep:
        print(f"repriced: snapshot {rep['meta']['snapshot']}, file {rep['meta']['file']} "
              f"(sha256 {rep['meta']['sha256'][:12]}), assumptions {rep['meta']['assumptions'] or 'registered'}")
    show(manifest)
    if "--write" in sys.argv:
        if what_if:
            sys.exit("--write follows decision D13 ('registered_hosted' in config/panel_v23.json); --without only prints")
        OUT.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print("written", OUT)
