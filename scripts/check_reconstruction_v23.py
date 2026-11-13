"""How faithful the reconstructed conversation is (protocol v2.3, Sections 2.2 and 11.7; added on 12 November 2026
after the third round of fresh readings). Harmless sentinel texts only: no benchmark prompt and no answer is sent.

In the in-context presentation a judge reads its own earlier answer as the previous turn of a conversation that is
rebuilt from the stored text (Section 2.2, "reconstructed presentation"). This script puts a number on how far that
rebuilt conversation differs, token by token, from the conversation in which the answer was written. For each local
model:

1. The original. The respondent build answers a harmless sentinel request with the respondent's settings (its thinking
   setting, no system message), through /api/generate, which returns the whole token sequence: the rendered request
   and the generated tokens through the answer. It is decoded with the model's vocabulary.
2. The reconstruction. Right after, with the model still loaded, the judge build receives the judging call of the
   in-context presentation with the judge's settings: the same request, the answer as the previous assistant turn,
   the judging instruction of the registered template (and the system message of Section 11.2 for model 6), with
   one output token. Ollama reports how many prompt tokens it reused from the cache (prompt_eval_cached_count): the
   length of the prefix that the reconstruction shares with the original sequence. When the judge build is not the
   respondent build (model 6), the original sequence is first loaded into the judge build as raw text.
3. When the shared prefix ends before the end of the answer, the parts of the original that the reconstruction is
   expected not to hold (below) are found by decoding, and the original without them is tested: it is loaded as raw
   text after a fresh load, the reconstruction is sent, and it must reuse every one of its tokens. Each measurement
   starts from a fresh load, because the server keeps earlier prompts of a loaded model in memory and may reuse any
   of them (seen on 12 November 2026). Positions count the BOS token where the server adds one; Ollama's token
   sequence leaves it out.
4. When the original without those parts still differs, and the difference starts with whitespace (alone in a token
   or joined with the text that follows it), the original is tested again with that whitespace shortened, one
   character at a time, down to none (since code review round 11, 13 November 2026). If the reconstruction then
   reuses every token, the remaining difference is whitespace before the answer, and both forms are reported; if
   not, the difference is reported as found, not explained.

Reported per build: the original sequence (decoded), its length through the answer, the shared prefix, the first
difference, the original's tokens from there (decoded), the expected parts with the result of their test, and where
the original without them still differs, if it does.
A reconstruction that shares the whole original sequence through the answer is "identical through the answer".
Expected differences: an empty thinking block that the template writes before the answer when thinking is off; a
switch word ("/no_think") that a template writes into the last user message (in the original that is the request);
whitespace that a model generates before its answer and that Ollama leaves out of the returned text; and, for model
6, the built-in prompt that the respondent build's template renders twice (Section 3.3).

The judging call is sent without "truncate" and "shift" (both false in the judging runs): with them Ollama reuses
no cached prefix, which is what keeps every judging call fresh, but which would also hide the shared prefix here; they
do not change the rendering. All calls use the judges' context size, so that the model is not reloaded between the
original and the reconstruction (the context size does not change the rendering), temperature 0 and the judges' seed.

Usage: python -I scripts/check_reconstruction_v23.py [--base URL] [--models-dir E:/ollama/models] [--only 5 6]
Writes results/logs/reconstruction_v23.json. Needs the local Ollama server: run it only with the PI's OK.
"""
import argparse
import datetime
import json
import pathlib
import sys
import urllib.request

PROJECT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / "scripts"), str(PROJECT / "src")]
import check_system_override as CS  # noqa: E402
import judge_v23 as J  # noqa: E402
import providers as PR  # noqa: E402

REQUEST = f"Sentinel {CS.USR_ID}. Say hello in one word."
ORIGINAL_CAP = 600          # output tokens of the original: enough for a model that reasons before it answers


def gen(base, body):
    return CS.post(base, "/api/generate", body)


def unload(base, model):
    try:
        gen(base, {"model": model, "keep_alive": 0})
    except Exception:
        pass


def options(settings, n_predict):
    loc = settings["local"]
    o = dict(loc["options"])
    o.update(num_predict=n_predict, temperature=0, seed=settings["seed"], num_ctx=loc["num_ctx"])
    return o


def think_of(entry):
    return entry["think"] if "think" in entry else None


def original(base, m, settings):
    body = {"model": m["model"], "prompt": REQUEST, "stream": False, "keep_alive": "5m",
            "options": options(settings, ORIGINAL_CAP)}
    t = think_of(m)
    if t is not None:
        body["think"] = t
    r = gen(base, body)
    return {"ids": r.get("context") or [], "prompt_tokens": r.get("prompt_eval_count"),
            "eval_count": r.get("eval_count"), "answer": r.get("response") or "", "done_reason": r.get("done_reason"),
            "thinking": r.get("thinking")}


def judging_call(base, jc, msgs):
    body = {"model": jc["model"], "stream": False, "keep_alive": "5m", "messages": msgs,
            "options": dict(jc["_opts"])}
    if "think" in jc:
        body["think"] = jc["think"]
    # "truncate" and "shift" (both false in judging calls, Section 11.2) are left out here: with them Ollama does not
    # reuse the cache at all, so no judging call can reuse the tokens of an earlier call. They govern only a
    # conversation longer than the context and do not change the rendering (the same prompt_eval_count either way,
    # checked on 12 November 2026); without them the shared prefix can be measured.
    r = CS.post(base, "/api/chat", body)
    return r.get("prompt_eval_count"), r.get("prompt_eval_cached_count")


def raw(base, model, text, opts):
    r = gen(base, {"model": model, "prompt": text, "raw": True, "stream": False, "keep_alive": "5m",
                   "options": dict(opts, num_predict=1)})
    return r.get("prompt_eval_count"), r.get("prompt_eval_cached_count")


def load_original_raw(base, model, vocab, ids, opts):
    """Load the original sequence into a build as raw text. Returns the prompt tokens the server counted: the
    sequence, plus the BOS token where the server adds one, as it did in the original call (Ollama's 'context'
    leaves BOS out)."""
    n, _ = raw(base, model, vocab.decode(ids), opts)
    return n


def n_bos_added(base, model, opts):
    """Whether the server puts a BOS token in front of a raw prompt (one token of text counted as two)."""
    n, _ = raw(base, model, "a", opts)
    return n == 2


def leading_ws_variants(text):
    """The text with the whitespace at its start shortened by one character at a time, down to none."""
    body = text.lstrip()
    ws = text[:len(text) - len(body)]
    return [ws[:k] + body for k in range(len(ws) - 1, -1, -1)]


def whitespace_check(base, judge_build, jc, msgs, vocab, cand, bos, r):
    """Step 4 of the module docstring. cand: the original without the expected parts; r: where it still differs.
    Returns {'original', 'reconstruction', 'loaded_as', 'reused'} when a shorter whitespace makes the reconstruction
    reuse every token, else None."""
    head, tail = vocab.decode(cand[bos:r]), vocab.decode(cand[r:])
    lead = tail[:len(tail) - len(tail.lstrip())]
    if not lead:
        return None
    for v in leading_ws_variants(tail):
        unload(base, judge_build)                          # fresh: the variant is the only sequence held
        n_v, _ = raw(base, judge_build, head + v, jc["_opts"])
        _, reused = judging_call(base, jc, msgs)
        if n_v and (reused or 0) >= n_v:
            return {"original": lead, "reconstruction": v[:len(v) - len(v.lstrip())], "loaded_as": n_v,
                    "reused": reused}
    return None


def control_positions(vocab, ids):
    return [i for i, x in enumerate(ids) if vocab.types[x] == CS.CONTROL]


def expected_spans(vocab, ids, first_generated=None, answer="", reasoning=None):
    """The parts of the original that the reconstruction is expected not to hold (module docstring), as token spans
    [(start, end, what)]: a switch word "/no_think" (with its leading space), an empty thinking block with the
    whitespace after it, the second copy of a block of the template that is repeated right after itself (the
    built-in prompt of model 6), and whitespace that the model generated before its answer and that the returned text
    leaves out (first_generated: index of the first generated token), or the reasoning block that the model wrote at
    the start of its output, with the whitespace after it (reasoning: that block, split off by decision D22). Found by
    decoding; spans do not overlap."""
    dec = lambda i, j: vocab.decode(ids[i:j])
    spans = []
    if reasoning and first_generated is not None and 0 <= first_generated < len(ids):
        j = next((j for j in range(first_generated + 1, len(ids) + 1)
                  if dec(first_generated, j).rstrip().endswith(PR.THINK_CLOSE)), None)
        if j is not None:
            while j < len(ids) and dec(j, j + 1) and not dec(j, j + 1).strip():
                j += 1
            spans.append((first_generated, j, "reasoning written into the output, split off (decision D22)"))
            first_generated = None
    if first_generated is not None and 0 <= first_generated < len(ids):
        k = first_generated
        while k < len(ids) and dec(k, k + 1) and not dec(k, k + 1).strip():
            k += 1
        lead = dec(first_generated, k)
        if lead and not answer.startswith(lead):
            spans.append((first_generated, k, "whitespace generated before the answer, left out of the returned text"))
    for i in range(len(ids)):                                     # the switch word
        hit = next((L for L in range(1, 7) if dec(i, i + L) in (" /no_think", "/no_think")), None)
        if hit:
            spans.append((i, i + hit, "switch word"))
            break
    for i in range(len(ids)):                                     # an empty thinking block
        if dec(i, i + 1) == "<think>":
            j = next((j for j in range(i + 1, len(ids)) if dec(j, j + 1) == "</think>"), None)
            if j is not None and not dec(i + 1, j).strip():
                k = j + 1
                while k < len(ids) and not dec(k, k + 1).strip():
                    k += 1
                spans.append((i, k, "empty thinking block"))
            break
    ctrl = control_positions(vocab, ids)                          # a block repeated right after itself
    found = None
    for x in range(len(ctrl)):
        for y in range(x + 1, len(ctrl)):
            s, e = ctrl[x], ctrl[y]
            if e - s >= 8 and ids[s:e] == ids[e:2 * e - s]:
                found = (e, 2 * e - s, "repeated block of the template")
                break
        if found:
            break
    if found:
        spans.append(found)
    spans.sort()
    return [s for n, s in enumerate(spans) if n == 0 or s[0] >= spans[n - 1][1]]


def examine(base, m, build, settings, template, models_dir):
    jc = J.judge_cfg(m, settings, build)
    jc["_opts"] = options(settings, 1)
    system = J.judge_system(m)
    resp_build, judge_build = m["model"], jc["model"]
    out = {"n": m["n"], "key": m["key"], "build": build, "respondent_build": resp_build, "judge_build": judge_build,
           "respondent_think": think_of(m), "judge_think": jc.get("think"),
           "judge_system_chars": len(system) if system else 0}
    vocab, source = CS.vocab_of(CS.post(base, "/api/show", {"model": resp_build, "verbose": True}), models_dir,
                                resp_build)
    out["vocabulary"] = source
    if vocab is None:
        out["error"] = source
        return out
    # Every measurement starts from a fresh load: the server keeps earlier prompts of a loaded model in memory and
    # can reuse any of them, so a count is clean only when the one sequence to compare with is the only one held.
    unload(base, resp_build)
    unload(base, judge_build)
    o = original(base, m, settings)
    ids = o["ids"]
    if not ids:
        out["error"] = "/api/generate returned no token sequence ('context')"
        return out
    out["original"] = {"tokens_through_answer": len(ids), "prompt_tokens": o["prompt_tokens"],
                       "answer": o["answer"], "done_reason": o["done_reason"], "thinking_returned": o["thinking"],
                       "decoded": vocab.decode(ids)}
    if o["done_reason"] != "stop":
        out["note"] = "the original answer reached the output limit of this check before it ended"
    visible, block = PR.split_inband_reasoning(o["answer"])        # decision D22: the turn holds the visible answer
    out["original"]["inband_reasoning_chars"] = len(block) if block else 0
    msgs = J.messages(template, REQUEST, visible, "context", system=system)
    # off: 1 where the server put a BOS token in front of the sequence that its 'context' leaves out (cache positions
    # count it), 0 where there is none or 'context' holds it. 'context' holds the prompt tokens without such a BOS and
    # every generated token but the last one (the end token), so off = prompt_eval_count + eval_count - 1 - len.
    off = (o["prompt_tokens"] + o["eval_count"] - 1 - len(ids)) if o["done_reason"] == "stop" else None
    if off not in (0, 1):
        out["error"] = (f"the token counts do not place the BOS token (prompt {o['prompt_tokens']}, generated "
                        f"{o['eval_count']}, sequence {len(ids)}, {o['done_reason']})")
        return out
    if judge_build != resp_build:
        unload(base, resp_build)
        n_raw = load_original_raw(base, judge_build, vocab, ids, jc["_opts"])
        out["original_loaded_as_raw_text"] = {"prompt_tokens": n_raw}
        if n_raw != len(ids) + off:
            out["error"] = f"the original sequence loaded into the judge build as {n_raw} tokens, not {len(ids) + off}"
            return out
        n_rec, shared = judging_call(base, jc, msgs)
    else:
        n_rec, shared = judging_call(base, jc, msgs)      # right after the original: its tokens are in the cache
    shared = shared or 0
    out["reconstruction"] = {"prompt_tokens": n_rec, "shared_prefix": shared, "bos_added": bool(off)}
    d = shared - off                                      # first difference, as an index of the original sequence
    if d >= len(ids):
        out["result"] = "identical through the answer"
        unload(base, judge_build)
        return out
    out["first_difference"] = d
    out["original_before_difference"] = vocab.decode(ids[max(0, d - 8):d])
    out["original_from_difference"] = vocab.decode(ids[d:])
    first_gen = o["prompt_tokens"] - off
    spans = expected_spans(vocab, ids, first_gen, visible, reasoning=block)
    out["result"] = "differs"
    if spans:
        cand = [x for i, x in enumerate(ids) if not any(s <= i < e for s, e, _ in spans)]
        unload(base, judge_build)                         # fresh: the shortened original is the only sequence held
        bos = 1 if off == 0 and cand and vocab.types[cand[0]] == CS.CONTROL and n_bos_added(base, judge_build,
                                                                                            jc["_opts"]) else 0
        n_c, _ = raw(base, judge_build, vocab.decode(cand[bos:]), jc["_opts"])
        _, reused = judging_call(base, jc, msgs)
        reused = reused or 0
        out["expected_parts"] = [{"what": w, "tokens": e - s, "text": vocab.decode(ids[s:e])} for s, e, w in spans]
        out["without_expected_parts"] = {"tokens": len(cand), "loaded_as": n_c, "reused_by_reconstruction": reused}
        n = sum(e - s for s, e, _ in spans)
        parts = ", ".join(w for _, _, w in spans) + f" ({n} tokens of the original that the reconstruction does not hold)"
        if n_c == len(cand) + off and reused >= len(cand) + off:
            out["result"] = f"differs only by {parts}; otherwise identical through the answer"
        elif n_c == len(cand) + off and reused - off > d:
            r = reused - off
            out["remaining_difference"] = {"at": r, "of": len(cand), "original_has": vocab.decode(cand[r:])}
            ws = whitespace_check(base, judge_build, jc, msgs, vocab, cand, bos, r)
            if ws:
                out["remaining_difference"]["whitespace_only"] = ws
                out["result"] = (f"differs only by {parts}, and by whitespace before the answer (the original has "
                                 f"{json.dumps(ws['original'])}, the reconstruction {json.dumps(ws['reconstruction'])}"
                                 f"); otherwise identical through the answer")
            else:
                out["result"] = (f"differs by {parts}, and after them from token {r} of {len(cand)}: the original has "
                                 f"{json.dumps(vocab.decode(cand[r:])[:60])}; not explained")
    if out["result"] == "differs":
        out["result"] = f"differs from token {d} of {len(ids)}: the original has {json.dumps(vocab.decode(ids[d:])[:60])}"
    unload(base, judge_build)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fidelity of the reconstructed conversation (harmless texts only)")
    ap.add_argument("--base", default="http://127.0.0.1:11434")
    ap.add_argument("--models-dir", default="")
    ap.add_argument("--only", type=int, nargs="*")
    ap.add_argument("--out", default=str(PROJECT / "results" / "logs" / "reconstruction_v23.json"))
    a = ap.parse_args(argv)
    settings = J.load_settings()
    template = J.load_template()
    models = json.loads((PROJECT / "config" / "models.json").read_text(encoding="utf-8"))["models"]
    rows = []
    for m in models:
        if m.get("provider") != "ollama" or not m.get("enabled") or (a.only and m["n"] not in a.only):
            continue
        builds = ["primary"] + (["sensitivity"] if m.get("judge_model_sensitivity") else [])
        for b in builds:
            try:
                r = examine(a.base, m, b, settings, template, a.models_dir)
            except Exception as e:                       # one build's failure is recorded, the others still run
                r = {"n": m["n"], "key": m["key"], "build": b, "error": f"{type(e).__name__}: {e}"}
            rows.append(r)
            print(f"model {r['n']:>2} {b:<11} {r.get('result') or r.get('error')}"
                  + (f" | shared {r['reconstruction']['shared_prefix']} of {r['original']['tokens_through_answer']}"
                     f"{' + BOS' if r['reconstruction']['bos_added'] else ''}" if "reconstruction" in r else "")
                  + "".join(f" | {x['what']}: {json.dumps(x['text'][:60])} ({x['tokens']} tokens)"
                            for x in r.get("expected_parts", []))
                  + (f" | {r['note']}" if r.get("note") else ""), flush=True)
    rep = {"checked_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "ollama_version": json.loads(urllib.request.urlopen(a.base + "/api/version", timeout=10).read())["version"],
           "request": REQUEST, "template_sha256": template.get("sha256"), "rows": rows}
    pathlib.Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", a.out)
    return 0 if all("error" not in r for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
