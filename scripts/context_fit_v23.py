"""Context fit of the local judges in the pilot (protocol v2.3, Sections 11.3 and 13.3; added on 12 November 2026
after the third round of fresh readings). No verdict is produced.

The context of the local judges (12,288 tokens) is chosen so that every answer is expected to fit every local judge in
both presentations (Section 11.3). That rests on a planning assumption about tokenizers, and the pilot never shows an
answer of models 22 and 23 to a local judge. This step measures the fit where it is tight. For every local judge build
(the primary builds, and the sensitivity build of model 6), it sends the judging conversation of both presentations
with the production code and settings (src/judge_v23.py, src/providers.py: the registered template, the system slot
of Section 11.2, "truncate" and "shift" false) and one output token, and records the prompt tokens that the judge
counts, or "context_overflow". Answers measured:
  - every pilot answer with content of models 22 and 23 (the longest answers of the panel, up to 4,000 tokens in
    another tokenizer); and
  - the TOP longest pilot answers with content (in characters) of each local model.
The output token is not read and is not a verdict; the calls are not part of the pilot's judging calls and enter no
count of Section 13.3.

Reported, by judge build and presentation: the number of conversations, the largest prompt token count with the answer
that gives it, the overflows, the other failures (a call that failed, or returned no prompt token count), and the
margin left by the largest count for the doubled output cap of the judge (1,200 tokens; for models 16 and 17
twice their own cap, decision D24). fits_with_doubled_cap is
False with any overflow, None (not established) with any other failure or no count, and otherwise
largest + the doubled cap <= context; every judge fits only when every value is True. A conversation that does not fit is
handled in the study by Section 10.2 (the longer context); here it is reported. Only answers to the prompts of the
chosen pilot round are measured (config/pilot_prompts_v23.json).

Usage: python -I scripts/context_fit_v23.py --answer-runs RUN[,RUN] [--round 1] [--top 3] [--base URL] [--out DIR]
Reads the answer files only after the pilot registration is recorded (answers_v23.guard). Local calls only; harmful
pilot answers are sent to the local judges only. Needs the local Ollama server: run it only with the PI's OK.
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import answers_v23 as A  # noqa: E402
import judge_v23 as J  # noqa: E402
import plan_v23 as P  # noqa: E402
import providers as PR  # noqa: E402
import run_judges_v23 as R  # noqa: E402
import spend_v23 as S  # noqa: E402

OUT = ROOT / "results" / "pilot"
TOP = 3
API_AUTHORS = (22, 23)


def round_prompts(rnd):
    """The prompt ids of one pilot round (config/pilot_prompts_v23.json)."""
    return set(rnd["harmful"]) | set(rnd["safe"]) | set(rnd["api"])


def select(table, panel, top=TOP, prompt_ids=None):
    """Answer ids to measure: every answer with content of models 22 and 23, and the `top` longest answers with
    content (characters) of each local model; only answers to prompt_ids when given (the round's prompts)."""
    rows = [r for r in table.values() if r.get("has_content")
            and (prompt_ids is None or r.get("prompt_id") in prompt_ids)]
    chosen = [r["answer_id"] for r in rows if r.get("model") in API_AUTHORS]
    for n in sorted(panel.local):
        mine = sorted((r for r in rows if r.get("model") == n), key=lambda r: (-len(r["text"]), r["answer_id"]))
        chosen += [r["answer_id"] for r in mine[:top]]
    return list(dict.fromkeys(chosen))


def judge_builds(models, panel, settings):
    out = []
    for m in models:
        if m.get("n") in panel.local:
            out.append((m, "primary"))
            if m.get("judge_model_sensitivity"):
                out.append((m, "sensitivity"))
    return out


def measure(provider, msgs):
    """(prompt tokens, None) or (None, 'context_overflow' or another failure)."""
    try:
        r = provider.call(msgs)
    except Exception as e:                                   # the production reading of a failure (Sections 10.1-10.3)
        if S.failure_kind(e, PR, J.is_context_overflow) == "overflow":
            return None, "context_overflow"
        return None, f"{type(e).__name__}: {PR.error_text(e)[:200]}"
    n = r.get("input_tokens")
    if not isinstance(n, int) or n <= 0:
        return None, "no prompt token count returned"
    return n, None


def run(table, prompts, models, panel, settings, template, ids, base=None, provider_of=None):
    """Measure every chosen answer under every local judge build in both presentations. provider_of(cfg) returns
    a provider (tests pass a fake); by default the production adapter."""
    provider_of = provider_of or PR.make
    rows, summary = [], {}
    for m, build in judge_builds(models, panel, settings):
        jc = J.judge_cfg(m, settings, build)
        cap2 = J.local_output_cap(m, settings, doubled=True)        # the judge's own cap, doubled (D24)
        ctx = jc["num_ctx"]
        cfg = dict(jc, max_output_tokens=1)
        if base:
            cfg["base_url"] = base
        prov = provider_of(cfg)
        system = J.judge_system(m)
        for pres in J.PRESENTATIONS:
            key = f"{m['n']}|{build}|{pres}"
            s = summary.setdefault(key, {"judge": m["n"], "build": jc["model"], "presentation": pres, "context": ctx,
                                         "conversations": 0, "largest": None, "largest_answer": None,
                                         "overflows": 0, "failures": 0})
            for aid in ids:
                a = table[aid]
                msgs = J.messages(template, prompts[a["prompt_id"]], a["text"], pres, system=system)
                n, err = measure(prov, msgs)
                rows.append({"judge": m["n"], "build": jc["model"], "presentation": pres, "answer_id": aid,
                             "author": a.get("model"), "prompt_tokens": n, "failure": err})
                s["conversations"] += 1
                if err == "context_overflow":
                    s["overflows"] += 1
                elif err:
                    s["failures"] += 1
                elif s["largest"] is None or n > s["largest"]:
                    s["largest"], s["largest_answer"] = n, aid
            s["margin_for_doubled_cap"] = None if s["largest"] is None else ctx - s["largest"] - cap2
            if s["overflows"]:
                s["fits_with_doubled_cap"] = False
            elif s["failures"] or s["largest"] is None:
                s["fits_with_doubled_cap"] = None                  # not established: a measurement is missing
            else:
                s["fits_with_doubled_cap"] = s["largest"] + cap2 <= ctx
    return rows, summary


def markdown(rep):
    lines = [f"# Context fit of the local judges, pilot round {rep['round']}", "",
             f"Answers measured: {rep['answers']} ({rep['answers_api']} of models 22 and 23, the {rep['top']} longest "
             f"of each local model). One output token per call; no verdict.", "",
             "| Judge | Build | Presentation | Conversations | Largest prompt | Overflows | Other failures | "
             "Margin for the doubled cap | Fits |", "|---|---|---|---|---|---|---|---|---|"]
    for s in rep["summary"].values():
        fits = {True: "yes", False: "no", None: "not established"}[s["fits_with_doubled_cap"]]
        lines.append(f"| {s['judge']} | {s['build']} | {s['presentation']} | {s['conversations']} | {s['largest']} | "
                     f"{s['overflows']} | {s['failures']} | {s['margin_for_doubled_cap']} | {fits} |")
    lines += ["", f"Every judge fits with the doubled output cap: {rep['all_fit']}."]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Context fit of the local judges (pilot, Section 13.3)")
    ap.add_argument("--answer-runs", required=True)
    ap.add_argument("--round", type=int, default=1, choices=[1, 2])
    ap.add_argument("--top", type=int, default=TOP)
    ap.add_argument("--base", default="")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    models = json.loads(R.MODELS.read_text(encoding="utf-8"))["models"]
    design = json.loads(R.DESIGN.read_text(encoding="utf-8"))
    panel = P.Panel(models, design, registered_hosted=R.registered_hosted(design, "1"))
    runs = [x for x in a.answer_runs.split(",") if x]
    table = A.load_table(runs, raw=R.RAW, pilot=True, number_of=panel.n_of)
    prompts = R.load_prompts()
    settings, template = J.load_settings(), J.load_template()
    rnd = P.load_pilot()["rounds"][a.round - 1]
    ids = select(table, panel, a.top, round_prompts(rnd))
    rows, summary = run(table, prompts, models, panel, settings, template, ids, a.base or None)
    rep = {"protocol": "2.3", "round": a.round, "answer_runs": runs, "top": a.top, "answers": len(ids),
           "answers_api": sum(1 for i in ids if table[i].get("model") in API_AUTHORS),
           "template_sha256": template["sha256"], "summary": summary,
           "all_fit": bool(summary) and all(s["fits_with_doubled_cap"] is True for s in summary.values()),
           "calls": rows}
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"context_fit_r{a.round}.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")
    (out / f"context_fit_r{a.round}.md").write_text(markdown(rep), encoding="utf-8")
    print(f"written {out / f'context_fit_r{a.round}.md'}; every judge fits with the doubled cap: {rep['all_fit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
