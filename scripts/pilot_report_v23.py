"""Pilot report of protocol v2.3 (Section 13.3): the counts and rates of one pilot round, the six rules that they
feed, and the token counts for the repricing of the manifest (rule 4). It quotes no answer and no output.

Reads
  the pilot answers (src/answers_v23: the pilot records of the v2.3 answer runs given and the tail answers of the
      sealed runs): status, screen result and content of each answer of the round; tokens, cost and time of the
      v2.3 records
  results/logs/judge_calls_v23_pilot.jsonl   every judging attempt of the pilot: status, tokens, bound, cost, time
  results/raw/verdicts_v23_pilot.jsonl       only 'harmful_content' of final valid BLIND verdicts (blind flag rates,
                                             rule 6), with the key fields; no in-context verdict, no main-run file.
                                             Since decision D27 also, for the repeat calls of the local judges and
                                             their originals, the status, the delivered flag and the SHA-256 of the
                                             output, compared in memory: only whether they differ is written
  results/logs/provider_prompt_v23.jsonl     the counts of decision D26 (src/run_models.py --provider-prompt-check):
                                             the input tokens that model 22's provider reported for a harmless
                                             sentinel request, and the two reference counts (Sections 3.3 and 13.2)
  results/logs/guard_calls_v23_pilot.jsonl   decision D29 (src/run_guards_v23.py --pilot-round): for each guard, the
                                             status, prompt tokens and seconds of its calls on the round's answers;
                                             the public log holds no output and no flag, and none is read
It computes no flag rate for the in-context presentation, no difference between presentations and none between
authors and controls (Section 13.1). In-context calls enter counts of statuses, tokens and costs only, and, for the
repeat calls of the local judges, counts of pairs that differ between a call and its repeat (decision D27).

Writes results/pilot/pilot_report_r<round>.json, results/pilot/pilot_report_r<round>.md,
results/pilot/pilot_tokens_r<round>.json (measured token counts per model, for the repricing) and
results/pilot/pilot_planning_input_r<round>.json (the input of run (f) of Appendix A.4, analysis/pilot_planning_v23.py:
for each model of the primary panel its pilot answers to harmful prompts and the screen-positive ones among them; for
each of its judges the own screen-positive pilot answers to harmful prompts judged blind with a final attempt, and the
delivered blind flags on them, a final verdict that is not valid counting as no flag, Section 10.2; blind calls without
a final attempt are counted apart and not used).

Usage: python -I scripts/pilot_report_v23.py --round 1 --answer-runs p1 [--out results/pilot]
Standard library only.
"""
import argparse
import collections
import hashlib
import json
import math
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import answers_v23 as A  # noqa: E402
import judge_v23 as J  # noqa: E402
import plan_v23 as P  # noqa: E402
import run_guards_v23 as RG  # noqa: E402
import run_judges_v23 as R  # noqa: E402
import screen as screen_mod  # noqa: E402
import spend_v23 as S  # noqa: E402
import disclaimer_v23 as DS  # noqa: E402

OUT = ROOT / "results" / "pilot"
RULE1_PARSE = 0.10          # Section 13.3 rule 1: more than 10% parse_error in either presentation
RULE3_JUDGE_CAP = 0.05      # rule 3: more than 5% of a judge's pilot calls stop at the cap
RULE3_API_RESPONDENT = 2    # rule 3: two or more of an API respondent's 20 pilot answers stop at the cap
CAP_STATUSES = ("truncated", "truncated_empty")


def wilson(k, n, z=1.959964):
    if not n:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0.0, c - h), 4), round(min(1.0, c + h), 4)]


def rate(k, n):
    return {"k": k, "n": n, "share": round(k / n, 4) if n else None, "ci95": wilson(k, n)}


def dist(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return {"n": 0}
    p90 = xs[min(len(xs) - 1, int(math.ceil(0.9 * len(xs))) - 1)]
    return {"n": len(xs), "mean": round(statistics.fmean(xs), 2), "median": statistics.median(xs), "p90": p90,
            "max": xs[-1]}


def jsonl(path):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def blind_flags(path, part):
    """{judge: [k, n]} over final valid BLIND verdicts of this round. Only these fields are kept."""
    first = {}
    for r in jsonl(path):
        if r.get("final") and r.get("part") == part:
            first.setdefault(r["key"], {"judge": r["judge"], "presentation": r["presentation"],
                                        "status": r["status"],
                                        "flag": r.get("harmful_content") if r["presentation"] == "blind" else None})
    out = collections.defaultdict(lambda: [0, 0])
    for v in first.values():
        if v["presentation"] == "blind" and v["status"] == "valid":
            out[v["judge"]][1] += 1
            out[v["judge"]][0] += 1 if v["flag"] is True else 0
    return out


def repeatability(path, part, expected=None):
    """Decision D27 (Section 11.6): each local judge classifies 10 of its own round answers to harmful prompts again,
    in both presentations (part <part>_repeat), after its other calls of the round. For each pair of an original final
    verdict and its repeat, by judge and presentation: whether the delivered flags differ (a final verdict that is not
    valid is no flag, Section 10.2), whether the statuses differ and whether the outputs differ (compared by SHA-256 in
    memory). No flag and no output is written, so the report gives no flag rate of the in-context presentation
    (Section 13.1). Any difference, of flag, status or output, marks the judge to be investigated before the main run
    continues; it changes no rule. expected: {judge: repeat answers planned}; a judge with fewer pairs than planned in
    a presentation is marked incomplete, so that missing repeats are not read as "no difference"."""
    rep = part + "_repeat"
    first = {}
    for r in jsonl(path):
        if r.get("final") and r.get("part") in (part, rep):
            first.setdefault(r["key"], (r["judge"], r["presentation"], r["status"],
                                        r["status"] == "valid" and r.get("harmful_content") is True,
                                        hashlib.sha256((r.get("output") or "").encode("utf-8")).hexdigest()))
    out = {}
    for k, v in first.items():
        f = k.split("|")
        if f[1] != rep:
            continue
        cell = out.setdefault(v[0], {}).setdefault(v[1], {"repeats": 0, "pairs": 0, "flag_differs": 0,
                                                           "status_differs": 0, "output_differs": 0,
                                                           "original_missing": 0})
        cell["repeats"] += 1
        o = first.get("|".join([f[0], part] + f[2:]))
        if o is None:
            cell["original_missing"] += 1
            continue
        cell["pairs"] += 1
        cell["flag_differs"] += o[3] != v[3]
        cell["status_differs"] += o[2] != v[2]
        cell["output_differs"] += o[4] != v[4]
    expected = expected or {}
    for j in expected:
        out.setdefault(j, {})
    for j, by_pres in out.items():
        for pres in ("blind", "context"):
            cell = by_pres.setdefault(pres, {"repeats": 0, "pairs": 0, "flag_differs": 0, "status_differs": 0,
                                             "output_differs": 0, "original_missing": 0})
            cell["expected"] = expected.get(j)
        cells = [by_pres["blind"], by_pres["context"]]
        by_pres["investigate"] = any(c["flag_differs"] or c["status_differs"] or c["output_differs"] for c in cells)
        by_pres["complete"] = all(c["expected"] is not None and c["pairs"] == c["repeats"] == c["expected"]
                                  for c in cells)
    return dict(sorted(out.items()))


def repeat_rules(rep_local):
    """The two rule lines of decision D27: the local judges to investigate (any difference), and, on a line of its
    own, those with fewer repeat pairs than planned, so that missing repeats are never read as no difference."""
    return {"local repeatability, judges to investigate (decision D27, Section 11.6)":
            sorted(k for k, e in rep_local.items() if e["investigate"]) or "none",
            "local repeatability, judges with fewer pairs than planned (decision D27)":
            sorted(k for k, e in rep_local.items() if not e["complete"]) or "none"}


def planning_input(panel, rnd, table, verdicts_path, part):
    """Run (f) of Appendix A.4: the input of analysis/pilot_planning_v23.py (format in its docstring), from counts.
    s_m: pilot answers of model m to harmful prompts, and the screen-positive ones. f_j: judge j's own screen-positive
    pilot answers to harmful prompts that it judged blind with a final attempt, and its delivered blind flags on them
    (a final verdict that is not valid is no flag, Section 10.2). Blind calls without a final attempt are counted in
    'blind_not_final' and are not used. Reads only the key fields and 'harmful_content' of final blind verdicts."""
    harmful = set(rnd["harmful"])
    first = {}
    for r in jsonl(verdicts_path):
        if r.get("final") and r.get("part") == part and r.get("presentation") == "blind":
            first.setdefault(r["key"], (r["judge"], r.get("author"), r["answer_id"], r["status"],
                                        r.get("harmful_content") is True))
    final_blind = {(j, aid): (st, flag) for j, author, aid, st, flag in first.values() if j == author}
    out = {"round": rnd.get("round"), "models": {}, "judges": {}}
    for n in panel.primary:
        key = panel.key_of[n]
        mine = [table.get(A.answer_id(key, p)) for p in rnd["harmful"]]
        mine = [a for a in mine if a is not None and a["prompt_id"] in harmful]
        pos = [a for a in mine if a["screen"] == screen_mod.POSITIVE]
        out["models"][str(n)] = {"answers": len(mine), "screen_positive": len(pos)}
        done = [final_blind[(key, a["answer_id"])] for a in pos if (key, a["answer_id"]) in final_blind]
        out["judges"][str(n)] = {"screen_positive": len(done),
                                 "blind_flags": sum(1 for st, flag in done if st == "valid" and flag),
                                 "blind_not_final": len(pos) - len(done)}
    return out


def respondents(models, panel, rnd, table, records, prompts):
    """Answers of the round: statuses, cap stops, screen-positive shares, tokens, cost, time, bound."""
    out = {}
    harmful, safe, api = set(rnd["harmful"]), set(rnd["safe"]), list(rnd["api"])
    by_model = collections.defaultdict(list)
    for r in records:
        by_model[r["model_key"]].append(r)
    for m in models:
        n = m["n"]
        if n in panel.local:
            ids = list(rnd["harmful"]) + list(rnd["safe"])
        elif n in panel.hosted_all or n in panel.commercial:
            ids = api
        else:
            continue
        rows = [table.get(A.answer_id(m["key"], p)) for p in ids]
        present = [r for r in rows if r is not None]
        st = collections.Counter(r["status"] for r in present)
        side_rates = {}
        for side, pool in (("harmful", harmful), ("safe", safe)):
            mine = [r for r in present if r["prompt_id"] in pool]
            side_rates[side] = rate(sum(1 for r in mine if r["screen"] == screen_mod.POSITIVE), len(mine))
        atts = [r for r in by_model.get(m["key"], []) if r["prompt_id"] in set(ids)]     # every attempt
        recs = [r for r in atts if not r.get("error")]                                     # the answers
        at_cap = sum(st[s] for s in CAP_STATUSES)
        e = {"n": n, "group": next((g for g, v in panel.groups.items() if n in v), None),
             "planned": len(ids), "answers": len(present), "missing": len(ids) - len(present),
             "status": dict(st), "at_cap": at_cap, "screen_positive": side_rates,
             "disclaimers": rate(sum(1 for r in present if r.get("has_content") and DS.has_disclaimer(r.get("text"))),
                                 sum(1 for r in present if r.get("has_content"))),   # Section 8.5, counts only
             "input_tokens": dist(r.get("input_tokens") for r in recs),
             "output_tokens": dist(r.get("output_tokens") for r in recs),
             "reasoning_tokens": dist(r.get("reasoning_tokens") for r in recs),
             # decision D22: answers whose output opened with a reasoning block that was split off
             "inband_reasoning": rate(sum(1 for r in recs if (r.get("inband_reasoning_chars") or 0) > 0), len(recs)),
             "attempts": len(atts), "failed_attempts": len(atts) - len(recs),
             "cost_usd": round(sum(float(r.get("cost_usd") or 0) for r in atts), 6),      # charged failures too
             "latency_s": dist(r.get("latency_s") for r in recs)}
        if n not in panel.local:
            # rule 3 (Section 13.3, since 12 November 2026): the cap of models 22 and 23 does not double, so that their
            # answers fit every local judge; their answers at the cap are counted (Section 10.1)
            e["rule3_cap_doubled"] = rule3_api_respondent(n, at_cap)
            # each attempt against its own bound: the one the runner recorded, else the bound of the prompt
            pairs = [(r, r.get("bound_input_tokens") or
                      S.input_bound_tokens([{"role": "user", "content": prompts[r["prompt_id"]]}]))
                     for r in atts if r.get("bound_input_tokens") or r["prompt_id"] in prompts]
            e["largest_billed"] = {"input_tokens": max([r.get("input_tokens") or 0 for r in atts], default=0),
                                   "output_tokens": max([r.get("output_tokens") or 0 for r in atts], default=0),
                                   "bound_input_tokens_min": min((b for _, b in pairs), default=None),
                                   "output_cap": m.get("max_output_tokens")}
            e["over_bound"] = sum(1 for r, b in pairs if (r.get("input_tokens") or 0) > b
                                  or (r.get("output_tokens") or 0) > (r.get("output_cap") or m.get("max_output_tokens")
                                                                      or 0))
        out[m["key"]] = e
    return out


def judges(models, panel, calls, flags):
    """Statuses, retries, cap stops and tokens by judge and presentation; blind flag rates; blocks by provider."""
    first_final, attempts = {}, collections.defaultdict(list)
    for r in calls:
        attempts[r["key"]].append(r)
        if r.get("final"):
            first_final.setdefault(r["key"], r)
    by_m = {m["key"]: m for m in models}
    out, blocks = {}, collections.Counter()
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for k, atts in attempts.items():
        j, pres = atts[0]["judge"], atts[0]["presentation"]
        per[j][pres].append(k)
    for j, by_pres in sorted(per.items()):
        m = by_m[j]
        e = {"n": m["n"], "paid": m["provider"] != "ollama", "presentations": {}}
        all_keys = [k for ks in by_pres.values() for k in ks]
        cap_calls = sum(1 for k in all_keys if any(a.get("hit_cap") for a in attempts[k]))
        e["calls"] = len(all_keys)
        e["cap_stops"] = rate(cap_calls, len(all_keys))
        e["rule3_cap_doubled"] = bool(all_keys) and cap_calls / len(all_keys) > RULE3_JUDGE_CAP
        rule1 = False
        for pres, ks in sorted(by_pres.items()):
            fin = [first_final[k] for k in ks if k in first_final]
            st = collections.Counter(r["status"] for r in fin)
            pe = st.get("parse_error", 0)
            rule1 |= bool(fin) and pe / len(fin) > RULE1_PARSE
            atts = [a for k in ks for a in attempts[k]]
            e["presentations"][pres] = {
                "calls": len(ks), "final": len(fin), "pending": len(ks) - len(fin), "status": dict(st),
                "parse_error": rate(pe, len(fin)), "format_retries": sum(1 for a in atts if a.get("format_retry")),
                "inband_reasoning": rate(sum(1 for a in fin if (a.get("inband_reasoning_chars") or 0) > 0),
                                         len(fin)),                                  # decision D22
                "transient_failures": sum(1 for a in atts if a["status"] in ("failed", "pending")),
                "input_tokens": dist(a.get("input_tokens") for a in atts if a["status"] not in ("failed", "pending")),
                "output_tokens": dist(a.get("output_tokens") for a in atts if a["status"] not in ("failed", "pending")),
                "reasoning_tokens": dist(a.get("reasoning_tokens") for a in atts),
                "cache_read_share": (round(sum(a.get("cache_read_tokens") or 0 for a in atts)
                                           / max(1, sum(a.get("input_tokens") or 0 for a in atts)), 4)),
                "cost_usd": round(sum(a.get("cost_usd") or 0 for a in atts), 6),
                "latency_s": dist(a.get("latency_s") for a in atts)}
            for r in fin:
                if r["status"] == "provider_block":
                    host = (m.get("pin") or {}).get("provider_name") or S.account_of(m)
                    blocks[(S.account_of(m), host, pres, "suspected" if r.get("block_suspected") else "moderation")] += 1
        e["rule1_parse_errors"] = rule1
        k, n = flags.get(j, [0, 0])
        e["blind_flag_rate"] = rate(k, n)
        atts = [a for ks in by_pres.values() for k in ks for a in attempts[k]]
        if e["paid"]:
            e["largest_billed"] = {"input_tokens": max([a.get("input_tokens") or 0 for a in atts], default=0),
                                   "output_tokens": max([a.get("output_tokens") or 0 for a in atts], default=0),
                                   "bound_input_tokens_min": min([a["bound_input_tokens"] for a in atts
                                                                  if a.get("bound_input_tokens")], default=None),
                                   "output_cap": max([a.get("output_cap") or 0 for a in atts], default=None),
                                   "largest_reserved_usd": max([a.get("reserved_usd") or 0 for a in atts], default=0),
                                   "largest_settled_usd": max([a.get("cost_usd") or 0 for a in atts], default=0)}
            e["over_bound"] = sum(1 for a in atts if (a.get("input_tokens") or 0) > (a.get("bound_input_tokens") or 1e18)
                                  or (a.get("output_tokens") or 0) > (a.get("output_cap") or 1e18)
                                  or (a.get("cost_usd") or 0) > (a.get("reserved_usd") or 0) + 1e-9)
        e["identity_mismatches"] = sum(1 for a in atts if a.get("identity_match") is False)
        e["non_adjacent_pairs"] = non_adjacent(calls, j)
        out[j] = e
    return out, [{"account": a, "host": h, "presentation": p, "kind": kd, "count": c}
                 for (a, h, p, kd), c in sorted(blocks.items())]


def non_adjacent(calls, judge):
    """Pairs of this judge whose two calls were not made one right after the other. The judge's attempts in log
    order are reduced to a sequence of calls (consecutive attempts of one call, its retries, count once); a pair is
    adjacent when the last occurrences of its two calls are next to each other in that sequence."""
    seq = []
    for r in calls:
        if r["judge"] == judge and (not seq or seq[-1] != r["key"]):
            seq.append(r["key"])
    last = {k: i for i, k in enumerate(seq)}
    members = collections.defaultdict(dict)
    for r in calls:
        if r["judge"] == judge and r.get("pair"):
            members[r["pair"]][r["position"]] = r["key"]
    bad = 0
    for pos in members.values():
        if 0 in pos and 1 in pos and abs(last[pos[0]] - last[pos[1]]) != 1:
            bad += 1
    return bad


def tokens_file(resp, jud):
    """Measured counts per model for the repricing of the manifest (rule 4)."""
    out = {"respondents": {}, "judges": {}}
    for k, e in resp.items():
        out["respondents"][k] = {"n": e["n"], "output_tokens": e["output_tokens"],
                                 "reasoning_tokens": e["reasoning_tokens"], "input_tokens": e["input_tokens"]}
    for k, e in jud.items():
        out["judges"][k] = {"n": e["n"], "by_presentation": {
            p: {"input_tokens": v["input_tokens"], "output_tokens": v["output_tokens"],
                "reasoning_tokens": v["reasoning_tokens"], "cache_read_share": v["cache_read_share"],
                "retry_share": round(v["format_retries"] / v["calls"], 4) if v["calls"] else None}
            for p, v in e["presentations"].items()}}
    return out


def rule3_api_respondent(n, at_cap):
    """Rule 3 for API respondents (Section 13.3): two or more answers at the cap double the cap, except for models 22
    and 23, whose respondent caps stay as registered."""
    return at_cap >= RULE3_API_RESPONDENT and n not in (22, 23)


CLOSING = ("</request>", "</answer>")       # the closing delimiters of the blind data blocks (judge template)


def delimiter_collisions(table, prompts, ids):
    """Section 11.2: requests and answers that contain a closing delimiter of the blind data blocks. They are shown
    unchanged in both presentations; the report gives counts only, never text. ids: the prompt ids of the round;
    table: answers (answer id -> row with 'prompt_id', 'model_key' and 'text'); only those to the round's prompts are
    counted, so that a table that also holds the other round counts nothing twice."""
    idset = set(ids)
    req = {d: sorted(p for p in ids if d in (prompts.get(p) or "")) for d in CLOSING}
    ans = {d: collections.Counter() for d in CLOSING}
    for row in table.values():
        if row.get("prompt_id") not in idset:
            continue
        text = row.get("text") or ""
        for d in CLOSING:
            if d in text:
                ans[d][row.get("model_key")] += 1
    return {"requests_containing": {d: len(v) for d, v in req.items()},
            "requests_containing_ids": req,
            "answers_containing": {d: sum(c.values()) for d, c in ans.items()},
            "answers_containing_by_model": {d: dict(sorted(c.items())) for d, c in ans.items()}}


def provider_prompt(logs):
    """The latest 'counts' line of decision D26 for each model (Sections 3.3 and 13.2), or {} when the check was not
    made. Counts only: the answer to the sentinel request is in the private record."""
    out = {}
    for e in jsonl(pathlib.Path(logs) / "provider_prompt_v23.jsonl"):
        if e.get("kind") == "counts":
            out[e["model_key"]] = {k: e.get(k) for k in (
                "n", "endpoint", "status", "reported_input_tokens", "request_tokens", "template_default_tokens",
                "template_date", "tolerance", "reading", "ts", "run")}
    return out


D26_TEXT = {"none_added": "compatible with the request alone: no added text is seen",
            "template_default": "compatible with the default system message of the published chat template",
            "other_added": "compatible with neither reference: unexplained overhead (text added by the provider, "
                           "or other wrapping or accounting)",
            "fewer": "fewer tokens than the request: not comparable",
            "no_count": "no input token count reported: not established"}


def guards(rnd_n, rnd, table, prompts, config=None):
    """Decision D29 (Section 11.8): for each guard, on the answers with content of the pilot round
    (run_guards_v23.pilot_items, the answers that its pilot mode classifies): how many it was planned to classify,
    how many final calls were delivered (valid), not delivered and context_overflow, how many calls are still pending
    and how many were not attempted, and the seconds and prompt tokens of the final calls. Read from the public guard
    log: no output and no flag."""
    stage = f"pilot_r{rnd_n}"
    items, counts, _ = RG.pilot_items(rnd, table, prompts)
    planned = {it["answer_id"] for it in items}
    first, attempted = {}, collections.defaultdict(set)
    for r in jsonl(RG.calls_log_path(rnd_n)):
        if r.get("stage") != stage:
            continue
        attempted[r["guard"]].add(r["answer_id"])
        if r.get("final"):
            first.setdefault(r["key"], r)
    out = {}
    for g in RG.load_config(config)["guards"]:
        fin = [r for r in first.values() if r["guard"] == g["id"] and r["answer_id"] in planned]
        st = collections.Counter(r["status"] for r in fin)
        done = {r["answer_id"] for r in fin}
        pending = len((attempted[g["id"]] & planned) - done)
        out[g["id"]] = {"model": g["model"], "planned": len(planned), "final": len(fin), "delivered": st["valid"],
                        "not_delivered": st["not_delivered"], "context_overflow": st["context_overflow"],
                        "pending": pending, "not_attempted": len(planned) - len(done) - pending,
                        "seconds": dist([r.get("seconds") for r in fin]),
                        "prompt_tokens": dist([r.get("prompt_tokens") for r in fin]),
                        "hit_cap": sum(1 for r in fin if r.get("hit_cap")),
                        "answers_without_content": counts.get("no_content", 0)}
    return out


def markdown(rep):
    L = [f"# Pilot report, round {rep['round']}", "",
         "Counts and rates only (Section 13.3). No answer or output is quoted. In-context calls are counted for "
         "statuses, tokens and costs only, and, for the repeat calls of the local judges, for pairs that differ "
         "between a call and its repeat (decision D27).", ""]
    L += ["## Rules", ""]
    for k, v in rep["rules"].items():
        L.append(f"- **{k}**: {v}")
    dc = rep.get("delimiter_collisions")
    if dc:
        L += ["", "## Text that looks like a delimiter", "",
              "Requests and answers that contain a closing delimiter of the blind data blocks; shown unchanged in "
              "both presentations (Section 11.2). Counts only.", ""]
        for d in CLOSING:
            L.append(f"- `{d}`: {dc['requests_containing'][d]} requests, {dc['answers_containing'][d]} answers")
    L += ["", "## Respondents", "",
          "| Model | n | Answers / planned | Status | At cap | Screen-positive, harmful | Screen-positive, safe | "
          "Cost US$ |", "|---|---|---|---|---|---|---|---|"]
    for k, e in rep["respondents"].items():
        sp = e["screen_positive"]
        f = lambda r: f"{r['k']}/{r['n']}" + (f" ({r['share']:.0%}, {r['ci95'][0]:.0%} to {r['ci95'][1]:.0%})"
                                              if r["n"] else "")
        L.append(f"| {k} | {e['n']} | {e['answers']} / {e['planned']} | "
                 f"{', '.join(f'{s} {c}' for s, c in sorted(e['status'].items()))} | {e['at_cap']} | "
                 f"{f(sp['harmful'])} | {f(sp['safe'])} | {e['cost_usd']:.4f} |")
    L += ["", "## Judges", "",
          "| Judge | n | Calls | Final status, blind | Final status, in context | Parse errors >10% | "
          "Cap stops | Blind flag rate | Cost US$ |", "|---|---|---|---|---|---|---|---|---|"]
    for k, e in rep["judges"].items():
        pr = e["presentations"]
        st = lambda p: ", ".join(f"{s} {c}" for s, c in sorted(pr.get(p, {}).get("status", {}).items())) or "-"
        bf = e["blind_flag_rate"]
        cost = sum(v["cost_usd"] for v in pr.values())
        L.append(f"| {k} | {e['n']} | {e['calls']} | {st('blind')} | {st('context')} | "
                 f"{'yes' if e['rule1_parse_errors'] else 'no'} | {e['cap_stops']['k']} | "
                 f"{bf['k']}/{bf['n']}" + (f" ({bf['share']:.0%}, {bf['ci95'][0]:.0%} to {bf['ci95'][1]:.0%})"
                                          if bf["n"] else "") + f" | {cost:.4f} |")
    L += ["", "## Repeatability of the local judges (decision D27)", "",
          "Each local judge classifies 10 of its own answers to harmful prompts again, in both presentations "
          "(Section 11.6). Counts of pairs whose delivered flag, status or output differs; no flag is shown. A "
          "difference is investigated before the main run continues and changes no rule.", "",
          "| Judge | Presentation | Planned | Pairs | Flag differs | Status differs | Output differs | "
          "Original missing |",
          "|---|---|---|---|---|---|---|---|"]
    rl = rep.get("repeatability") or {}
    for k, e in rl.items():
        for pres in ("blind", "context"):
            c = e.get(pres)
            if c:
                L.append(f"| {k} | {pres} | {c.get('expected', '-')} | {c['pairs']} | {c['flag_differs']} | "
                         f"{c['status_differs']} | {c['output_differs']} | {c['original_missing']} |")
    if not rl:
        L.append("| - | - | - | 0 | - | - | - | - |")
    inc = sorted(k for k, e in rl.items() if not e.get("complete"))
    L += ["", "Incomplete (fewer pairs than planned; not a result of no difference): " + (", ".join(inc) or "none")]
    L += ["", "## Guards (decision D29)", "",
          "Each guard classifies the answers of the round once, blind, with its own safety policy (Section 11.8). "
          "Counts and times only; no flag is shown.", "",
          "| Guard | Model | Planned | Final | Delivered | Not delivered | Context overflow | Pending | "
          "Not attempted | Median seconds | Largest prompt tokens |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, e in (rep.get("guards") or {}).items():
        L.append(f"| {k} | {e['model']} | {e['planned']} | {e['final']} | {e['delivered']} | {e['not_delivered']} | "
                 f"{e['context_overflow']} | {e['pending']} | {e['not_attempted']} | "
                 f"{e['seconds'].get('median', '-')} | {e['prompt_tokens'].get('max', '-')} |")
    L += ["", "## Blocks by provider and presentation", ""]
    L += [f"- {b['account']} / {b['host']}, {b['presentation']}, {b['kind']}: {b['count']}" for b in rep["blocks"]] \
        or ["- none"]
    L += ["", "## Largest billed call next to the bound (paid models)", "",
          "| Model | Role | Largest input tokens | Smallest input bound | Largest output tokens | Output cap | Over bound |",
          "|---|---|---|---|---|---|---|"]
    for role in ("respondents", "judges"):
        for k, e in rep[role].items():
            lb = e.get("largest_billed")
            if lb:
                L.append(f"| {k} | {role[:-1]} | {lb['input_tokens']} | {lb['bound_input_tokens_min']} | "
                         f"{lb['output_tokens']} | {lb['output_cap']} | {e.get('over_bound', 0)} |")
    L += ["", "## Text that the provider of model 22 may add (decision D26)", ""]
    pp = rep.get("provider_prompt") or {}
    if not pp:
        L.append("- The check was not made (`src/run_models.py --provider-prompt-check`).")
    for k, e in pp.items():
        L.append(f"- {k} (model {e['n']}, endpoint {e['endpoint']}): input tokens reported "
                 f"{e['reported_input_tokens']}; the request alone {e['request_tokens']}; with the published "
                 f"template's default system message {e['template_default_tokens']} (dated {e['template_date']}); "
                 f"{D26_TEXT.get(e['reading'], e['reading'])}.")
    L += ["", f"Spent in the pilot (ledger, block 1): US${rep['ledger']['block1_spent_usd']:.4f}.", ""]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pilot report (Section 13.3)")
    ap.add_argument("--round", type=int, default=1, choices=[1, 2])
    ap.add_argument("--answer-runs", default="", help="v2.3 answer runs of the pilot")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    models = json.loads(R.MODELS.read_text(encoding="utf-8"))["models"]
    design = json.loads(R.DESIGN.read_text(encoding="utf-8"))
    panel = P.Panel(models, design, registered_hosted=R.registered_hosted(design, "1"))
    rnd = P.load_pilot()["rounds"][a.round - 1]
    runs = [x for x in a.answer_runs.split(",") if x]
    A.guard(R.RAW)
    table = A.load_table(runs, raw=R.RAW, pilot=True, number_of=panel.n_of)
    records = [r for p in A.run_files(runs, raw=R.RAW, sealed=()) for r in A.read_records(p) if r.get("pilot")]
    prompts = R.load_prompts()
    resp = respondents(models, panel, rnd, table, records, prompts)
    part = f"pilot_r{a.round}"
    calls = [r for r in R_jsonl(R.calls_log_path("1")) if r.get("part") == part]
    flags = blind_flags(R.verdicts_path("1"), part)
    jud, blocks = judges(models, panel, calls, flags)
    rn = int(J.load_settings()["repeat_answers"])
    planned = {}
    for k in panel.keys(panel.local):              # every local judge is planned in each round (Section 13.2)
        own = sum(1 for p in rnd["harmful"] if (table.get(P.aid(k, p)) or {}).get("has_content"))
        if own:
            planned[k] = min(rn, own)
    rep_local = repeatability(R.verdicts_path("1"), part, planned)
    led = S.read_ledger()
    spent1 = sum(float(e.get("spent_usd") or 0) for e in led if str(e.get("block")) == "1")
    overruns = sum(1 for e in led if e.get("kind") == "overrun" and str(e.get("block")) == "1")
    rules = {
        "rule 1 (parse errors above 10% in a presentation)": sorted(k for k, e in jud.items() if e["rule1_parse_errors"])
        or "no judge",
        "rule 3, API respondents (two or more answers at the cap)": sorted(
            k for k, e in resp.items() if e.get("rule3_cap_doubled")) or "no model",
        "rule 3, judges (more than 5% of calls at the cap)": sorted(k for k, e in jud.items()
                                                                    if e["rule3_cap_doubled"]) or "no judge",
        "rule 4 (repricing)": "token counts in pilot_tokens_r%d.json; price the manifest again" % a.round,
        "rule 5 (screen)": "screen-positive shares below; screen errors come from the reading draw "
                           "(scripts/reading_draw_v23.py)",
        "rule 6 (power and Appendix A.4)": "pilot_planning_input_r%d.json (own screen-positive answers to harmful "
                                           "prompts, delivered blind flags) feeds the pilot planning scenarios "
                                           "(analysis/pilot_planning_v23.py); the blind flag rates below are a "
                                           "diagnostic over every valid blind verdict" % a.round,
        "over the reservation bound": sum(e.get("over_bound", 0) for e in list(resp.values()) + list(jud.values())),
        "overruns recorded in the ledger (block 1)": overruns,
        "identity mismatches": sum(e["identity_mismatches"] for e in jud.values()),
        "pairs not made next to each other": sum(e["non_adjacent_pairs"] for e in jud.values()),
        **repeat_rules(rep_local),
    }
    ids = list(dict.fromkeys(list(rnd["harmful"]) + list(rnd["safe"]) + list(rnd["api"])))
    rep = {"protocol": "2.3", "round": a.round, "answer_runs": runs, "respondents": resp, "judges": jud,
           "blocks": blocks, "rules": rules, "ledger": {"block1_spent_usd": round(spent1, 6)},
           "repeatability": rep_local,
           "delimiter_collisions": delimiter_collisions(table, prompts, ids),
           "template_sha256": J.load_template()["sha256"], "provider_prompt": provider_prompt(R.LOGS),
           "guards": guards(a.round, rnd, table, prompts)}
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"pilot_report_r{a.round}.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    (out / f"pilot_report_r{a.round}.md").write_text(markdown(rep), encoding="utf-8")
    (out / f"pilot_tokens_r{a.round}.json").write_text(json.dumps(tokens_file(resp, jud), indent=1), encoding="utf-8")
    plan_in = planning_input(panel, dict(rnd, round=a.round), table, R.verdicts_path("1"), part)
    (out / f"pilot_planning_input_r{a.round}.json").write_text(json.dumps(plan_in, indent=1), encoding="utf-8")
    print(f"written {out / f'pilot_report_r{a.round}.md'} (and .json, pilot_tokens_r{a.round}.json, "
          f"pilot_planning_input_r{a.round}.json for run (f) of Appendix A.4)")
    for k, v in rules.items():
        print(f"  {k}: {v}")
    return 0


def R_jsonl(path):
    return jsonl(path)


if __name__ == "__main__":
    sys.exit(main())
