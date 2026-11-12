"""Cost model for the study (protocol v2.2, Section 11; frontier judges in the core, cap US$110).

Prices API calls from the 8 November 2026 snapshot (OpenRouter list prices in
data/selection/2026-11-08/or_v1_models.json; ':batch' entries are the 50% batch
prices, which match the direct Anthropic and OpenAI batch APIs). It reads only the
snapshot and config/models.json, never results/.

Every call type the protocol schedules is costed, including the items the round-2 and round-3
reviewers found missing (G3 up to 120, format retries, recognition probe, second wording,
unframed own-prompt re-judging, respondent pilot). Two scenarios: 'expected' and 'pessimistic'
(reasoning x2, judge prompt 3,500 tokens, retries 15%). Two modes:
  coded   as coded now (the planning basis, Section 11): direct Anthropic and OpenAI respondents use the
          batch APIs (run_models.py --batch); OpenRouter respondents and every judge call are synchronous;
          judge prefixes are cached only on the direct Anthropic and OpenAI APIs;
  full    batch endpoints wherever cheaper and cached judge prefixes everywhere (only if implemented and audited).
The stage table follows the spending order of Section 11; holds use the pessimistic figures.
Round 5 (audit B5-M1, M2): the pessimistic scenario assumes no cache hits (a prefix may fall below a model's
minimum cacheable length, or the cache may expire between interleaved calls), so a hold never relies on a
discount; and stage 3b is the instrument labelling that H2 and H3 need (own-prompt answers of models 1-6 by
the selected instrument, safe-prompt answers of models 1-6 by the contrast-neutral instrument), priced at the
dearest eligible API candidate in case either instrument is an API judge.
Round 6 (audit B6-M1, m7): with no cache hits every cached prefix is re-written, so it is priced at the
snapshot's cache-write price where one is listed (Anthropic and OpenAI); stage 3b takes the dearest eligible
candidate among single judges, majority juries of three developers and version-1 pipelines (Section 8.4: a
candidate is eligible if labelling the whole corpus costs at most US$20 in the expected scenario); round 7
(audit C7-m6): stage 6 is priced at the same dearest eligible candidate. The holds protect stages 1-3; stage
3b starts only if it fits, otherwise H2 and H3 use the local fallback (Section 11).

Round-1 external review of 10 November 2026 (R1-C4): respondent calls now carry the same retry allowance as
judge calls, and `--v23` prices the fixed call manifest of the v2.3 draft (yoked design: each API judge makes
600 main calls, 60 pilot calls, 40 repeatability calls and at most 120 blind reference calls; each API
respondent answers 60 harmful and 90 safe benchmark prompts plus 20 fresh pilot prompts).

Usage: python -I scripts/cost_model.py            (v2.2 stage table)
       python -I scripts/cost_model.py --v23      (v2.3 manifest)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "data" / "selection" / "2026-11-08" / "or_v1_models.json"
MODELS = ROOT / "config" / "models.json"

# Snapshot IDs of the direct-routed models (for prices only).
SNAP_ID = {"claude-sonnet-5.5": "anthropic/claude-sonnet-5.5", "claude-haiku-5.5": "anthropic/claude-haiku-5.5",
           "gpt-5.6-luna": "openai/gpt-5.6-luna", "gpt-6-luna": "openai/gpt-6-luna",
           "gpt-6.1-sol": "openai/gpt-6.1-sol", "gemini-4-argon": "google/gemini-4-argon"}
GUARD_API = "openai/gpt-oss-safeguard-20b"
# Prompt caching in sync mode: Anthropic (cache_control on the system block, providers.py) and OpenAI
# (automatic for prefixes of 1,024+ tokens). OpenRouter-routed models are assumed uncached.
DIRECT = ("anthropic", "openai")
FRONTIER = {"claude-opus-5.5": "anthropic/claude-opus-5.5",
            "gpt-6-astra": "openai/gpt-6-astra", "muse-wonder": "meta/muse-wonder"}
# Frontier judges (Section 8.1): blind gold, G3, pilot, repeatability and the external set; no in-context items.
FRONTIER_CALLS = {"gold_blind_G1_G2": 432, "G3_top_up": 120, "pilot": 30, "repeatability": 50,
                  "external_xstest_v2": 150}

# Respondent token assumptions per call. Reasoning is billed as output.
RESP_IN = 70
RESP_OUT = {"safe": 450, "harmful": 150, "own": 500}
REASONING_BY_EFFORT = {None: 0, "none": 0, "low": 300, "medium": 1000, "high": 2000, "xhigh": 2600, "max": 3200}
RESP_PILOT = 20                      # per API respondent, inside its subset, synchronous

# Respondent prompt counts per subset (Section 5.2; own = 60 base prompts x 3 framings).
SUBSET_COUNTS = {"preregistered_api": {"safe": 550, "harmful": 60, "own": 180},
                 "added_api": {"safe": 100, "harmful": 60, "own": 30},
                 "venice": {"safe": 100, "harmful": 150, "own": 30},
                 "all": {"safe": 550, "harmful": 500, "own": 180}}

# Judge calls per API judge (Section 8.3).
# in_context_self: at most 30 own G1+G2 items per API judge (12 for most); anchors: 30 per judge.
JUDGE_CALLS = {"gold_blind_G1_G2": 432, "G3_top_up": 120, "in_context_self": 30, "anchors": 30,
               "repeatability": 50, "pilot": 30, "recognition_probe": 60, "second_wording": 100,
               "unframed_own_rejudge": 84, "external_xstest_v2": 150}
EXPLORATORY = ("anchors", "recognition_probe", "second_wording", "unframed_own_rejudge", "external_xstest_v2")
SCENARIOS = {
    "expected":    {"judge_in": 2500, "prefix": 1500, "judge_vis": 80, "judge_reason": 300, "resp_mult": 1.0, "retry": 0.05,
                    "cache_hits": True},
    "pessimistic": {"judge_in": 3500, "prefix": 1500, "judge_vis": 120, "judge_reason": 600, "resp_mult": 2.0, "retry": 0.15,
                    "cache_hits": False},
}
# Stage 3b (Section 11): instrument labels needed by H2 (own prompts of models 1-6: 6 x 180) and H3 (safe
# prompts of models 1-6: 6 x 550, contrast-neutral instrument). Eligible API candidates: Section 8.4.
H2_LABELS, H3_LABELS = 6 * 180, 6 * 550
ELIGIBLE_API = ("anthropic/claude-haiku-5.5", "openai/gpt-5.6-luna", "deepseek/deepseek-v4.1-flash-1017",
                "z-ai/glm-5.3-flash", "openai/gpt-6-luna", "tencent/hy3",
                "cognitivecomputations/dolphin-mistral-24b-venice-edition")
NEUTRAL_API = ("deepseek/deepseek-v4.1-flash-1017", "z-ai/glm-5.3-flash", "tencent/hy3",
               "cognitivecomputations/dolphin-mistral-24b-venice-edition")
CORPUS = 10 * 1230 + 3 * 790 + 8 * 190 + 280     # Section 4: 16,470 answers


def load_prices(path=None):
    """US$ per 1M tokens by model id, from an OpenRouter model list (default: the snapshot of 8 November 2026)."""
    out = {}
    for m in json.loads(Path(path or SNAP).read_text(encoding="utf-8"))["data"]:
        p = m["pricing"]
        out[m["id"]] = {"in": float(p["prompt"]) * 1e6, "out": float(p["completion"]) * 1e6,
                        "cache": float(p.get("input_cache_read") or p["prompt"]) * 1e6,
                        "write": float(p.get("input_cache_write") or p["prompt"]) * 1e6}
    return out


def price(prices, mid, batch, direct_only=False):
    """Batch price only when it exists and is cheaper (GLM's batch is dearer than sync)."""
    sync = prices[mid]
    if direct_only and mid.split("/")[0] not in DIRECT:
        batch = False
    b = prices.get(mid + ":batch")
    if batch and b and b["in"] <= sync["in"] and b["out"] <= sync["out"]:
        return b, True
    return sync, False


def api_models():
    cfg = json.loads(MODELS.read_text(encoding="utf-8"))["models"]
    return [m for m in cfg if m["provider"] != "ollama"]


def respondents(prices, sc, batch, part="all", direct_only=False, counts_all=None, by_key=None):
    """part: 'all'; 'common' (pilot + the 190-prompt added_api subset, or Venice's own subset);
    'rest' (the remaining 600 prompts of models 1-3). counts_all: the same prompt counts for every API
    respondent; by_key: counts for single models (overrides counts_all)."""
    rows, total = [], 0.0
    resp_in, resp_out = sc.get("resp_in", RESP_IN), sc.get("resp_out", RESP_OUT)   # the repricing may set them
    for m in api_models():
        mid = SNAP_ID.get(m["key"], m["model"])
        pr, used_batch = price(prices, mid, batch, direct_only)
        reasoning = sc.get("reasoning_by_key", {}).get(m["key"], REASONING_BY_EFFORT[m.get("effort")]) * sc["resp_mult"]
        counts = dict(counts_all or SUBSET_COUNTS[m["prompt_subset"]])
        if by_key and m["key"] in by_key:
            counts = dict(by_key[m["key"]])
        elif counts_all is not None:
            pass
        elif part != "all" and m["prompt_subset"] == "preregistered_api":
            common = SUBSET_COUNTS["added_api"]
            counts = common if part == "common" else {k: counts[k] - common[k] for k in counts}
        elif part == "rest":
            counts = {k: 0 for k in counts}
        vis = sc.get("vis_mult", 1.0)        # round 2 (check A): the v2.3 manifest also doubles the visible answer
        cost = sum(k * (resp_in * pr["in"] + (resp_out[kind] * vis + reasoning) * pr["out"]) / 1e6
                   for kind, k in counts.items())
        sync = prices[mid]
        if part != "rest":
            cost += sc.get("pilot_rounds", 1) * RESP_PILOT * (resp_in * sync["in"]
                                                              + (resp_out["safe"] * vis + reasoning) * sync["out"]) / 1e6
        cost *= 1 + sc["retry"]
        rows.append((m["key"], m.get("effort"), sum(counts.values()) + RESP_PILOT, used_batch, cost))
        total += cost
    return total, rows


def judge_call_cost(pr, sc, reasoning=True, cache=True):
    """cache: the code caches the prefix on this path. With cache hits it is read at the cache price; with
    none (pessimistic) it is re-written on every call, at the cache-write price where one is listed."""
    if cache:
        pre = pr["cache"] if sc.get("cache_hits", True) else pr.get("write", pr["in"])
    else:
        pre = pr["in"]
    inp = (sc["judge_in"] - sc["prefix"]) * pr["in"] + sc["prefix"] * pre
    out = (sc["judge_vis"] + (sc["judge_reason"] if reasoning else 0)) * pr["out"]
    return (inp + out) / 1e6


def judges(prices, sc, calls, batch=True, only=None):
    """only: restrict to these model keys (default: every API judge)."""
    n = sum(calls.values()) * (1 + sc["retry"])
    rows, total = [], 0.0
    for m in api_models():
        if only is not None and m["key"] not in only:
            continue
        mid = SNAP_ID.get(m["key"], m["model"])
        pr, _ = price(prices, mid, batch=batch)
        c = n * judge_call_cost(pr, sc, reasoning=m.get("effort") is not None, cache=batch or m["provider"] in DIRECT)
        rows.append((m["key"], c))
        total += c
    return total, rows


def main():
    prices = load_prices()
    print(f"corpus of answers (Section 4): {CORPUS:,}")
    print(f"judge calls per API judge: {sum(JUDGE_CALLS.values())} {JUDGE_CALLS}")
    for name, sc in SCENARIOS.items():
        print(f"\n=== {name} ===")
        r_sync, _ = respondents(prices, sc, batch=False)
        r_batch, rows = respondents(prices, sc, batch=True)
        j_all, jrows = judges(prices, sc, JUDGE_CALLS)
        j_core, _ = judges(prices, sc, {k: v for k, v in JUDGE_CALLS.items() if k not in EXPLORATORY})
        j_ext, _ = judges(prices, sc, {"external_xstest_v2": JUDGE_CALLS["external_xstest_v2"]})
        guard = (432 + 120 + 30) * (1 + sc["retry"]) * judge_call_cost(price(prices, GUARD_API, False)[0], sc)
        inst = CORPUS * judge_call_cost(price(prices, "openai/gpt-6-luna", True)[0], sc)
        n_fr = sum(FRONTIER_CALLS.values()) * (1 + sc["retry"])
        fr_rows = [(k, n_fr * judge_call_cost(price(prices, mid, True)[0], sc)) for k, mid in FRONTIER.items()]
        fr = sum(c for _, c in fr_rows)
        print(f"respondents: sync ${r_sync:6.2f} | batch where cheaper ${r_batch:6.2f}")
        print(f"API judges, core (gold, G3, in-context, repeats, pilot): ${j_core:6.2f}")
        print(f"API judges, exploratory probe and second wording:       ${j_all - j_core - j_ext:6.2f}")
        print(f"API judges, external transfer set (150 items) :          ${j_ext:6.2f}")
        print(f"gpt-oss-safeguard (API guard): ${guard:5.2f}; OpenAI moderation: $0")
        print(f"instrument on corpus: local $0 | cheapest API (GPT-6 Luna batch) ${inst:6.2f}")
        print(f"frontier judges, core (3 models, {sum(FRONTIER_CALLS.values())} calls each): ${fr:6.2f} "
              + " ".join(f"[{k} ${c:.2f}]" for k, c in fr_rows))
        print(f"TOTAL confirmatory core (batch respondents, local instrument): ${r_batch + j_core + guard:6.2f}; "
              f"+ frontier judges: ${r_batch + j_core + guard + fr:6.2f}; "
              f"+ exploratory items and external set: ${r_batch + j_all + guard + fr:6.2f}; "
              f"all synchronous: ${r_sync + j_all + guard + fr:6.2f}")
        if name == "expected":
            print("\nper respondent (calls incl. pilot, effort, batch, cost):")
            for k, e, n, b, c in rows:
                print(f"  {k:22s} {str(e):7s} {n:5d}  {'batch' if b else 'sync ':5s}  ${c:6.2f}")
            print("per API judge (all calls):")
            for k, c in jrows:
                print(f"  {k:22s} ${c:6.2f}")


def frontier(prices, sc, calls, batch, batch_direct=False):
    """batch_direct: blind frontier judging on the direct Anthropic and OpenAI APIs uses the batch path
    (Section 8.3, round 4); Muse Wonder (OpenRouter) stays synchronous. Pilots are always synchronous."""
    n = sum(calls.values()) * (1 + sc["retry"])
    total = 0.0
    for mid in FRONTIER.values():
        direct = mid.split("/")[0] in DIRECT
        b = batch or (batch_direct and direct)
        total += n * judge_call_cost(price(prices, mid, b)[0], sc, cache=batch or direct)
    return total


def developer(mid):
    """Derived models count toward the base developer (Section 8.4)."""
    return "mistral" if "mistral" in mid else mid.split("/")[0]


ARBITER_SHARE = 0.5      # a version-1 pipeline's arbiter labels the items A and B disagree on; at most half


def eligible_candidates(prices, ids):
    """Single judges, majority juries of three developers and version-1 pipelines (A and B on every item, an
    arbiter from a third developer on at most half), each as a list of (model, share of items), whose
    whole-corpus cost is at most US$20 in the expected scenario, as coded (Section 8.4). The cascade costs no
    more than its cheapest API member on part of the corpus."""
    import itertools
    exp = SCENARIOS["expected"]
    corpus = {mid: CORPUS * judge_call_cost(price(prices, mid, False)[0], exp, cache=mid.split("/")[0] in DIRECT)
              for mid in ids}
    cands = [[(mid, 1.0)] for mid in ids]
    for c in itertools.combinations(ids, 3):
        if len({developer(x) for x in c}) == 3:
            cands.append([(x, 1.0) for x in c])
            for arb in c:
                cands.append([(x, 1.0) for x in c if x != arb] + [(arb, ARBITER_SHARE)])
    return [c for c in cands if sum(w * corpus[x] for x, w in c) <= 20]


def dearest_rate(prices, sc, batch, ids):
    """Cost per corpus answer of the dearest eligible candidate among ids, with its members."""
    def one(mid):
        return judge_call_cost(price(prices, mid, batch)[0], sc, cache=batch or mid.split("/")[0] in DIRECT)
    return max((sum(w * one(x) for x, w in c), [x if w == 1.0 else f"{x} (arbiter)" for x, w in c])
               for c in eligible_candidates(prices, ids))


def stage3b(prices, sc, batch, detail=False):
    """Dearest eligible API candidate for H2 plus dearest contrast-neutral one for H3 (synchronous unless
    batch; cached prefix only on the direct APIs), with retries."""
    r2, c2 = dearest_rate(prices, sc, batch, ELIGIBLE_API)
    r3, c3 = dearest_rate(prices, sc, batch, NEUTRAL_API)
    h2, h3 = H2_LABELS * (1 + sc["retry"]) * r2, H3_LABELS * (1 + sc["retry"]) * r3
    return ((h2, c2), (h3, c3)) if detail else h2 + h3


def stage2_parts(prices, sc, batch=False):
    """Stage 2 split into its confirmatory core and the parts reduced first (Section 11)."""
    pick = lambda keys: {k: JUDGE_CALLS[k] for k in keys}
    core = (judges(prices, sc, pick(("pilot", "gold_blind_G1_G2", "G3_top_up", "in_context_self")), batch)[0]
            + frontier(prices, sc, {"pilot": FRONTIER_CALLS["pilot"]}, batch))
    return {"core (pilots, blind gold G1+G2+G3, on-policy in-context)": core,
            "anchors": judges(prices, sc, pick(("anchors",)), batch)[0],
            "API-judge repeatability": judges(prices, sc, pick(("repeatability",)), batch)[0],
            "API guard": (432 + 120 + 30) * (1 + sc["retry"])
            * judge_call_cost(price(prices, GUARD_API, False)[0], sc, cache=batch)}


def stages(prices, sc, mode):
    """Cost of each stage of the Section 11 spending order. mode: 'coded' or 'full'."""
    batch = mode == "full"
    pick = lambda keys: {k: JUDGE_CALLS[k] for k in keys}
    guard = (432 + 120 + 30) * (1 + sc["retry"]) * judge_call_cost(price(prices, GUARD_API, False)[0], sc, cache=batch)
    resp = lambda part: respondents(prices, sc, True, part, direct_only=not batch)[0]
    late = tuple(k for k in EXPLORATORY if k != "anchors")
    return [
        ("1 API respondents: pilots and the common subset (G2 frame)", resp("common")),
        ("2 Judge pilots (API and frontier); blind gold G1+G2+G3 with on-policy in-context; anchors",
         judges(prices, sc, pick(("pilot", "gold_blind_G1_G2", "G3_top_up", "in_context_self", "anchors")),
                batch)[0]
         + frontier(prices, sc, {"pilot": FRONTIER_CALLS["pilot"]}, batch)),
        ("3 Models 1-3: remaining 600 prompts each (H2, H3)", resp("rest")),
        ("3b Instrument labels for H2 and H3 if an instrument is an API judge (dearest eligible, juries and pipelines included; local fallback if it does not fit)",
         stage3b(prices, sc, batch)),
        ("4 API-judge repeatability and the API guard, then frontier judges: blind gold G1+G2+G3 "
         "(direct APIs in batch)",
         judges(prices, sc, pick(("repeatability",)), batch)[0] + guard
         + frontier(prices, sc, {k: FRONTIER_CALLS[k] for k in ("gold_blind_G1_G2", "G3_top_up")}, batch, True)),
        ("5 Frontier repeatability (50 items each)",
         frontier(prices, sc, {"repeatability": FRONTIER_CALLS["repeatability"]}, batch, True)),
        ("6 API instrument on the rest of the corpus, if selected (dearest eligible candidate)",
         (CORPUS - H2_LABELS - H3_LABELS) * (1 + sc["retry"]) * dearest_rate(prices, sc, batch, ELIGIBLE_API)[0]),
        ("7 External set (API and frontier judges), recognition probe, second wording, unframed re-judging",
         judges(prices, sc, pick(late), batch)[0]
         + frontier(prices, sc, {"external_xstest_v2": FRONTIER_CALLS["external_xstest_v2"]}, batch, True)),
    ]


def stage_table(prices):
    cols = [(n, b) for n in SCENARIOS for b in ("coded", "full")]
    res = {c: stages(prices, SCENARIOS[c[0]], c[1]) for c in cols}
    head = " | ".join(n + (", full batch+cache" if b == "full" else ", as coded") for n, b in cols)
    print("\n| Stage | " + head + " |")
    print("|---|" + "---|" * len(cols))
    for i, (label, _) in enumerate(res[cols[0]]):
        print("| " + label + " | " + " | ".join("%.2f" % res[c][i][1] for c in cols) + " |")
    for upto, label in ((3, "Stages 1-3, local instruments"),
                        (4, "Stages 1-3b, API instruments (3b falls back to local instruments if it does not fit)"),
                        (5, "Stages 1-4 (+ frontier judges), API instruments"),
                        (8, "All stages, API instruments")):
        print("| **" + label + "** | " + " | ".join("**%.2f**" % sum(x for _, x in res[c][:upto]) for c in cols) + " |")
    no_inst = {c: sum(x for i, (_, x) in enumerate(res[c]) if i not in (3, 6)) for c in cols}
    print("| **All stages, local instruments** | " + " | ".join("**%.2f**" % no_inst[c] for c in cols) + " |")
    for name, sc in SCENARIOS.items():
        parts = stage2_parts(prices, sc)
        print(f"stage 2 and 4 parts, {name}, as coded: " + "; ".join(f"{k} {v:.2f}" for k, v in parts.items()))
    pess = [x for _, x in res[("pessimistic", "coded")]]
    keys = ("1", "2", "3", "3b", "4", "5", "6", "7")
    holds = {"1": pess[1] + pess[2], "2": pess[2], "3": 0.0, "3b": 0.0}
    print("pessimistic holds (stages 1-3 not yet complete, other than the running one; 3b has a local fallback): "
          + json.dumps({k: round(v, 2) for k, v in holds.items()}))
    print("pessimistic projections (start rule): " + json.dumps({k: round(v, 2) for k, v in zip(keys, pess)}))
    for name, sc in SCENARIOS.items():
        (c2, j2), (c3, j3) = stage3b(load_prices(), sc, False, detail=True)
        print(f"stage 3b, {name}, as coded: H2 {c2:.2f} {j2}; H3 {c3:.2f} {j3}")


# ---- v2.3 manifest (yoked design) ----
CAP = 110.0
V23_RESP = {"safe": 90, "harmful": 60, "own": 0}          # per API respondent, plus RESP_PILOT pilot prompts
V23_JUDGE = {"main: own answers, blind": 150, "main: own answers, in-context": 150,
             "main: yoked control answers, blind": 150, "main: yoked control answers, in-context": 150,
             "judge pilot (20 own pairs + 10 control pairs)": 60, "repeatability": 40,
             "blind reference subset (labelled items)": 120}
V23_GUARD_CALLS = 550                                      # API guard on every labelled item
V23_OPTIONS = {"off-policy harmful answers, in-context (+30 per API judge)": ("judge", 30),
               "grey-zone own prompts (+30 answers per API respondent)": ("resp", {"safe": 0, "harmful": 0, "own": 30}),
               "Venice extended to the 150 harmful prefix (+90 answers, +360 judge calls on 2 API judges)": ("venice", 90)}
EXPENSIVE = ("claude-sonnet-5.5", "gpt-6.1-sol", "kimi-k3.1-pro", "grok-4.7", "gemini-4-argon")


def manifest_v23(prices):
    """Every call of the v2.3 draft, expected and pessimistic, as coded (synchronous judges; direct-API
    respondents in batch). No pilot result is used: token counts are the planning assumptions above."""
    print("v2.3 manifest: API respondent prompts", V23_RESP, "+ pilot", RESP_PILOT)
    print("v2.3 manifest: calls per API judge", sum(V23_JUDGE.values()), V23_JUDGE)
    for name, sc in SCENARIOS.items():
        r_new, rows = respondents(prices, sc, True, direct_only=True, counts_all=V23_RESP)
        r_old, _ = respondents(prices, sc, True, direct_only=True)
        parts = {k: judges(prices, sc, {k: v}, batch=False)[0] for k, v in V23_JUDGE.items()}
        one, jrows = judges(prices, sc, {"one": 1}, batch=False)
        dear = sum(c for k, c in jrows if k in EXPENSIVE)
        guard = V23_GUARD_CALLS * (1 + sc["retry"]) * judge_call_cost(price(prices, GUARD_API, False)[0], sc, cache=False)
        total = r_new + sum(parts.values()) + guard
        print()
        print(f"=== v2.3, {name} ===")
        print(f"API respondents (150 prompts + {RESP_PILOT} pilot each, retries included): ${r_new:6.2f}"
              f"   [v2.2 subsets with retries: ${r_old:6.2f}]")
        for k, v in parts.items():
            print(f"  {k:50s} ${v:6.2f}")
        print(f"  {'API guard on labelled items':50s} ${guard:6.2f}")
        print(f"TOTAL ${total:6.2f}   remaining under the cap of ${CAP:.0f}: ${CAP - total:6.2f}"
              f"   [with v2.2 respondent subsets: ${total - r_new + r_old:6.2f}]")
        print(f"one call to each API judge, retries included: ${one:.6f} "
              f"(five expensive judges ${dear:.6f}, other seven ${one - dear:.6f})")
        print("per API judge, one call: " + " ".join(f"[{k} ${c:.6f}]" for k, c in jrows))
        print("per API respondent: " + " ".join(f"[{k} ${c:.2f}]" for k, _, _, _, c in rows))
        for label, (kind, x) in V23_OPTIONS.items():
            if kind == "judge":
                c = x * one
            elif kind == "resp":
                c = respondents(prices, sc, True, direct_only=True, counts_all=x)[0] \
                    - respondents(prices, sc, True, direct_only=True, counts_all={k: 0 for k in x})[0]
            else:
                ven = dict(jrows)["venice-uncensored"]
                vr = dict((k, c) for k, _, _, _, c in rows)["venice-uncensored"]
                c = vr * x / (sum(V23_RESP.values()) + RESP_PILOT) + 2 * x * ven + 2 * x * (one - ven) / 11
            print(f"  option: {label}: ${c:5.2f}  -> total ${total + c:6.2f}")


# ---- v2.3 manifest, draft B (author's round-2 proposal) ----
# Type-matched yoking; the eleven non-commercial models (ten local, free; Venice through the API) use a long
# harmful frame of 300 prompts; the commercial judges keep 60 harmful + 90 safe prompts, receive harm-side
# controls only for commercial answers that the refusal screen marks as non-refusals, and judge a common set of
# 60 harmful answers by refusal-removed authors in both presentations (blind calls inside the reference subset).
VENICE = "venice-uncensored"
V23B_RESP = {"commercial": {"safe": 90, "harmful": 60, "own": 0}, "venice": {"safe": 90, "harmful": 300, "own": 0}}
POS = "harm-side controls: screen-positive commercial answers, x 2"
V23B_POS_CALLS = {"expected": 20, "pessimistic": 60}       # 10 or 30 screen-positive answers per commercial judge
V23B_JUDGE = {
    "commercial": {"own answers, blind + in-context (150 x 2)": 300,
                   "safe-side controls, blind + in-context (90 x 2)": 180, POS: None,
                   "common harmful set, in-context": 60, "blind reference subset (includes the common set)": 120,
                   "judge pilot": 60, "repeatability": 40},
    "venice": {"own answers, blind + in-context (390 x 2)": 780, "controls, blind + in-context (390 x 2)": 780,
               "common harmful set, in-context": 60, "blind reference subset (includes the common set)": 120,
               "judge pilot": 60, "repeatability": 40}}
# Cut order if repricing from pilot token counts puts the pessimistic total above the cap (calls per judge).
V23B_CUTS = [("repeatability 40 -> 20, every API judge", 20, 20),
             ("blind reference subset 120 -> 90, every API judge", 30, 30),
             ("safe-side controls of the commercial judges 90 -> 60 prompts", 60, 0)]


def manifest_v23b(prices):
    com = [m["key"] for m in api_models() if m["key"] != VENICE]
    print("v2.3 draft B: API respondent prompts", V23B_RESP, "+ pilot", RESP_PILOT)
    for name, sc in SCENARIOS.items():
        r, rows = respondents(prices, sc, True, direct_only=True, counts_all=V23B_RESP["commercial"],
                              by_key={VENICE: V23B_RESP["venice"]})
        jc = dict(V23B_JUDGE["commercial"], **{POS: V23B_POS_CALLS[name]})
        pc = {k: judges(prices, sc, {k: v}, batch=False, only=com)[0] for k, v in jc.items()}
        pv = {k: judges(prices, sc, {k: v}, batch=False, only=[VENICE])[0] for k, v in V23B_JUDGE["venice"].items()}
        guard = V23_GUARD_CALLS * (1 + sc["retry"]) * judge_call_cost(price(prices, GUARD_API, False)[0], sc, cache=False)
        one_c = judges(prices, sc, {"one": 1}, batch=False, only=com)[0]
        one_v = judges(prices, sc, {"one": 1}, batch=False, only=[VENICE])[0]
        total = r + sum(pc.values()) + sum(pv.values()) + guard
        print()
        print(f"=== v2.3 draft B, {name} ===")
        print(f"API respondents, retries included: ${r:6.2f}   "
              + " ".join(f"[{k} ${c:.2f}]" for k, _, _, _, c in rows))
        print(f"{len(pc)} commercial judges, {sum(jc.values())} calls each: ${sum(pc.values()):6.2f}")
        for k, v in pc.items():
            print(f"  {k:62s} {jc[k]:4d}  ${v:6.2f}")
        print(f"Venice as judge, {sum(V23B_JUDGE['venice'].values())} calls: ${sum(pv.values()):6.2f}")
        for k, v in pv.items():
            print(f"  {k:62s} {V23B_JUDGE['venice'][k]:4d}  ${v:6.2f}")
        print(f"API guard on {V23_GUARD_CALLS} labelled items: ${guard:6.2f}")
        print(f"TOTAL ${total:6.2f}   remaining under the cap of ${CAP:.0f}: ${CAP - total:6.2f}")
        print(f"one call to each commercial judge ${one_c:.6f}; one Venice call ${one_v:.6f} (retries included)")
        left = total
        for label, n_com, n_ven in V23B_CUTS:
            left -= n_com * one_c + n_ven * one_v
            print(f"  cut: {label}: saves ${n_com * one_c + n_ven * one_v:5.2f}  -> total ${left:6.2f}")


if __name__ == "__main__":
    import sys
    if "--v23b" in sys.argv:
        manifest_v23b(load_prices())
    elif "--v23" in sys.argv:
        manifest_v23(load_prices())
    else:
        main()
        stage_table(load_prices())
