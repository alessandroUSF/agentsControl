"""Rendering checks for local judges (protocol v2.3, Sections 3.3, 11.7 and 19.4). Harmless texts only: no benchmark
prompt and no answer is sent.

For a test model, optionally beside a reference model with the same tokenizer and template:

1. Token counts (as in v2.2). Template and parameter SHA-256 from /api/show, and prompt_eval_count of /api/chat in six
   layouts, with num_predict 1 and keep_alive 0 (the model is loaded afresh, so no cached prefix is skipped):
       U      user
       SU     short system + user
       SLU    long system + user
       SUAU   short system + user + assistant + user   (the in-context layout)
       SLUAU  long system + user + assistant + user
       UAU    user + assistant + user
2. Rendered content (v2.3). The system and user texts carry sentinel strings. /api/generate renders the single-turn
   layouts U, SU and SLU with the model's own template and returns the token sequence of the rendered conversation
   ('context'). It is decoded with the model's vocabulary (from /api/show with verbose, or from the GGUF header of the
   model's blob with --models-dir) and read:
     - the system sentinel appears exactly once in SU and SLU and not in U; the user sentinel exactly once in each;
       the whole system text and the whole user text are there;
     - the built-in prompt of the build (SYSTEM of its Modelfile, from /api/show) is absent from SU and SLU;
     - no other text is left in SU and SLU once the supplied texts, the role names, whitespace and control tokens are
       taken out (a prompt written into the template itself would remain here);
     - /api/chat counts as many prompt tokens as /api/generate for U, SU and SLU (both paths render alike);
     - the multi-turn layouts, which only /api/chat renders, add what the single-turn ones predict:
       SLUAU - SUAU = SLU - SU (the whole system message is rendered there too) and
       SUAU - SU = UAU - U (supplying a system message changes nothing else in the conversation).
   With --ref: equal template and parameter hashes, equal counts in all six layouts and equal decoded renderings of
   U, SU and SLU ('identical_to_ref').
3. Thinking setting (12 November 2026). Every request carries the thinking setting of the judge run: "think": false
   when the build's entry in config/models.json has a "think" key (src/judge_v23.py, judge_cfg), otherwise none
   (--think config, the default; --think off or unset overrides it). Some chat templates write a switch word into
   the last user message for this setting. The only text accepted beyond the supplied texts is that word, "/no_think",
   and only when thinking is off and the template itself contains it; anything else still fails.
'pass_v23' is true when every condition that applies holds. Informational: whether the built-in prompt is used when
no system message is given, and the text the template adds then.

Usage:
  python -I scripts/check_system_override.py --test MODEL [--ref MODEL] [--models-dir E:/ollama/models] [--out PATH]
         [--think config|off|unset] [--models-config config/models.json]
Writes results/logs/render_check_v23_<test>.json (counts, hashes and the decoded renderings of the harmless texts).
Needs the local Ollama server: run it only with the PI's OK. Standard library only.
"""
import argparse
import hashlib
import json
import pathlib
import re
import struct
import sys
import time
import urllib.request

PROJECT = pathlib.Path(__file__).resolve().parents[1]
SYS_ID, USR_ID = "AC23-SYS-7F3Q", "AC23-USR-2K8M"
SYSTEM = f"Sentinel {SYS_ID}. You classify short texts. Answer briefly."
SYSTEM_LONG = (f"Sentinel {SYS_ID}. You classify short texts. Answer briefly. Read the whole text first, then give "
               "one word. Do not add explanations, greetings or punctuation beyond what is asked.")
U1 = f"Sentinel {USR_ID}. Say hello in one word."
A1, U2 = "Hello.", "Now say goodbye in one word."
LAYOUTS = {
    "U": [("user", U1)],
    "SU": [("system", SYSTEM), ("user", U1)],
    "SLU": [("system", SYSTEM_LONG), ("user", U1)],
    "SUAU": [("system", SYSTEM), ("user", U1), ("assistant", A1), ("user", U2)],
    "SLUAU": [("system", SYSTEM_LONG), ("user", U1), ("assistant", A1), ("user", U2)],
    "UAU": [("user", U1), ("assistant", A1), ("user", U2)],
}
SINGLE = {"U": None, "SU": SYSTEM, "SLU": SYSTEM_LONG}
OPTIONS = {"num_predict": 1, "temperature": 0, "seed": 1}
ROLE_WORDS = re.compile(r"\b(system|user|assistant)\b", re.I)
NORMAL, UNKNOWN, CONTROL, USER_DEFINED, UNUSED, BYTE = 1, 2, 3, 4, 5, 6
THINK_OFF_SWITCH = "/no_think"


def post(base, path, body, timeout=600):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def hashes(d):
    sha = lambda s: hashlib.sha256((s or "").encode("utf-8")).hexdigest()
    return {"template_sha256": sha(d.get("template")), "parameters_sha256": sha(d.get("parameters")),
            "system_sha256": sha(d.get("system")) if d.get("system") else None,
            "system_chars": len(d.get("system") or ""),
            "quantization": (d.get("details") or {}).get("quantization_level"),
            "template_has_cr": "\r" in (d.get("template") or "")}


def think_setting(build, cfg_path):
    """The thinking setting a judge run sends for this build: False when its config entry has a 'think' key
    (as src/judge_v23.py judge_cfg does), None otherwise."""
    try:
        models = json.loads(pathlib.Path(cfg_path).read_text(encoding="utf-8"))["models"]
    except (OSError, ValueError, KeyError):
        return None
    for m in models:
        builds = {m.get("judge_model") or m.get("model"), m.get("judge_model_sensitivity")}
        if build in builds and "think" in m:
            return False
    return None


def with_think(body, think):
    if think is not None:
        body["think"] = think
    return body


def counts(base, model, think=None):
    out = {}
    for name, msgs in LAYOUTS.items():
        body = {"model": model, "messages": [{"role": r, "content": c} for r, c in msgs], "stream": False,
                "keep_alive": 0, "options": OPTIONS}
        out[name] = post(base, "/api/chat", with_think(body, think))["prompt_eval_count"]
    return out


# ---------------------------------------------------------------- vocabulary and decoding

def _byte_decoder():
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {chr(c): b for b, c in zip(bs, cs)}


BYTE_OF = _byte_decoder()


class Vocab:
    """Decoder for byte-level BPE ('gpt2' in GGUF) and SentencePiece ('llama') vocabularies."""

    def __init__(self, kind, tokens, types=None):
        if kind not in ("gpt2", "llama"):
            raise ValueError(f"tokenizer model {kind!r} has no decoder here")
        self.kind, self.tokens = kind, tokens
        self.types = list(types) if types else [NORMAL] * len(tokens)

    def piece(self, i):
        """(bytes, is_text): control and user-defined tokens come back verbatim and are not counted as text."""
        t, ty = self.tokens[i], self.types[i]
        if ty in (CONTROL, USER_DEFINED, UNKNOWN, UNUSED):
            return t.encode("utf-8"), False
        if self.kind == "gpt2":
            return b"".join(bytes([BYTE_OF[c]]) if c in BYTE_OF else c.encode("utf-8") for c in t), True
        if ty == BYTE and re.fullmatch(r"<0x[0-9A-Fa-f]{2}>", t):
            return bytes([int(t[3:5], 16)]), True
        return t.replace("\u2581", " ").encode("utf-8"), True

    def decode(self, ids, text_only=False):
        parts = [self.piece(i) for i in ids]
        return b"".join(p for p, is_text in parts if is_text or not text_only).decode("utf-8", errors="replace")


GGUF_SCALAR = {0: "B", 1: "b", 2: "H", 3: "h", 4: "I", 5: "i", 6: "f", 7: "?", 10: "Q", 11: "q", 12: "d"}
GGUF_WANT = ("tokenizer.ggml.model", "tokenizer.ggml.tokens", "tokenizer.ggml.token_type")


def gguf_tokenizer(path):
    """The tokenizer keys of a GGUF file (versions 2 and 3), read from its header."""
    out = {}
    with open(path, "rb") as f:
        rd = f.read

        def string():
            n, = struct.unpack("<Q", rd(8))
            return rd(n).decode("utf-8", errors="replace")

        def value(t):
            if t == 8:
                return string()
            if t == 9:
                et, n = struct.unpack("<IQ", rd(12))
                if et in GGUF_SCALAR:
                    fmt = f"<{n}{GGUF_SCALAR[et]}"
                    return list(struct.unpack(fmt, rd(struct.calcsize(fmt))))
                return [value(et) for _ in range(n)]
            fmt = "<" + GGUF_SCALAR[t]
            return struct.unpack(fmt, rd(struct.calcsize(fmt)))[0]

        if rd(4) != b"GGUF":
            raise ValueError(f"{path}: not a GGUF file")
        version, = struct.unpack("<I", rd(4))
        if version < 2:
            raise ValueError(f"{path}: GGUF version {version} is not read here")
        _, n_kv = struct.unpack("<QQ", rd(16))
        for _ in range(n_kv):
            k = string()
            t, = struct.unpack("<I", rd(4))
            v = value(t)
            if k in GGUF_WANT:
                out[k] = v
                if len(out) == len(GGUF_WANT):
                    break
    return out


def vocab_of(show_verbose, models_dir=None, model=None):
    mi = show_verbose.get("model_info") or {}
    if mi.get("tokenizer.ggml.tokens"):
        return Vocab(mi.get("tokenizer.ggml.model"), mi["tokenizer.ggml.tokens"], mi.get("tokenizer.ggml.token_type")), \
            "api/show"
    if models_dir:
        sys.path.insert(0, str(PROJECT / "scripts"))
        import make_judge_alias_m6 as MK
        d = pathlib.Path(models_dir)
        w = MK.layer(MK.manifest(d, model), "model")[0]["digest"]
        g = gguf_tokenizer(MK.blob(d, w))
        return Vocab(g.get("tokenizer.ggml.model"), g["tokenizer.ggml.tokens"], g.get("tokenizer.ggml.token_type")), \
            f"gguf {w[:19]}"
    return None, "no vocabulary: /api/show gave no tokens and no --models-dir was given"


# ---------------------------------------------------------------- rendered content

def norm(s):
    return " ".join(s.split())


def builtin_probes(builtin):
    b = norm(builtin or "")
    return sorted({b[:48], b[-48:]}) if b else []


def residual(text, contents):
    """Text left once the supplied contents, the role names and whitespace are taken out."""
    t = norm(text)
    for c in sorted({norm(x) for x in contents if x}, key=len, reverse=True):
        t = t.replace(c, " ")
    return re.sub(r"\s+", "", ROLE_WORDS.sub(" ", t))


def rendered(base, model, vocab, think=None):
    out = {}
    for name, system in SINGLE.items():
        body = {"model": model, "prompt": U1, "stream": False, "keep_alive": 0, "options": OPTIONS}
        if system is not None:
            body["system"] = system
        r = post(base, "/api/generate", with_think(body, think))
        ctx = r.get("context")
        if not ctx:
            return None
        resp = r.get("response") or ""
        full, text = vocab.decode(ctx), vocab.decode(ctx, text_only=True)
        if resp.strip():
            full = full[:len(full.rstrip()) - len(resp.strip())] if full.rstrip().endswith(resp.strip()) else full
            text = text[:len(text.rstrip()) - len(resp.strip())] if text.rstrip().endswith(resp.strip()) else text
        out[name] = {"generate_prompt_eval_count": r.get("prompt_eval_count"), "context_tokens": len(ctx),
                     "eval_count": r.get("eval_count"), "rendered": full, "text": text}
    return out


def content_checks(rend, show_d, think=None):
    pr = builtin_probes(show_d.get("system"))
    switch = THINK_OFF_SWITCH if think is False and THINK_OFF_SWITCH in (show_d.get("template") or "") else None
    explained = {"", switch} if switch else {""}
    has_builtin = lambda s: any(p in norm(s) for p in pr)
    c = {
        "system_sentinel_once": (all(rend[k]["text"].count(SYS_ID) == 1 for k in ("SU", "SLU"))
                                 and rend["U"]["text"].count(SYS_ID) == 0),
        "user_sentinel_once": all(rend[k]["text"].count(USR_ID) == 1 for k in SINGLE),
        "system_text_whole": norm(SYSTEM) in norm(rend["SU"]["text"]) and norm(SYSTEM_LONG) in norm(rend["SLU"]["text"]),
        "user_text_whole": all(norm(U1) in norm(rend[k]["text"]) for k in SINGLE),
        "builtin_absent_with_system": not any(has_builtin(rend[k]["text"]) for k in ("SU", "SLU")),
        "no_unexplained_text": all(residual(rend[k]["text"], (SINGLE[k], U1)) in explained for k in ("SU", "SLU")),
    }
    info = {"builtin_prompt": bool(pr), "think": think, "thinking_switch_accepted": switch,
            "builtin_used_without_system": bool(pr) and has_builtin(rend["U"]["text"]),
            "residual_by_layout": {k: residual(rend[k]["text"], (SINGLE[k], U1)) for k in SINGLE}}
    return c, info


def count_checks(rend, cnt):
    return {"chat_equals_generate": all(cnt[k] == rend[k]["generate_prompt_eval_count"] for k in SINGLE),
            "multi_turn_system_whole": cnt["SLUAU"] - cnt["SUAU"] == cnt["SLU"] - cnt["SU"],
            "multi_turn_nothing_else": cnt["SUAU"] - cnt["SU"] == cnt["UAU"] - cnt["U"]}


def examine(base, model, models_dir, think=None):
    show = post(base, "/api/show", {"model": model})
    vocab, source = vocab_of(post(base, "/api/show", {"model": model, "verbose": True}), models_dir, model)
    t = {"hashes": hashes(show), "counts": counts(base, model, think), "vocabulary": source, "think": think}
    t["rendered"] = rendered(base, model, vocab, think) if vocab else None
    if t["rendered"] is None:
        t["content_note"] = (source if not vocab else "/api/generate returned no token sequence ('context'): this "
                             "Ollama version cannot show the rendered conversation")
    return t, show


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rendering checks of a local judge build (harmless texts only)")
    ap.add_argument("--test", required=True)
    ap.add_argument("--ref")
    ap.add_argument("--base", default="http://127.0.0.1:11434")
    ap.add_argument("--models-dir", default="", help="Ollama models folder, to read the vocabulary from the GGUF blob")
    ap.add_argument("--out", default="")
    ap.add_argument("--think", choices=["config", "off", "unset"], default="config",
                    help="thinking setting sent with every request; 'config' follows config/models.json as a judge run")
    ap.add_argument("--models-config", default=str(PROJECT / "config" / "models.json"))
    a = ap.parse_args(argv)
    pick = lambda b: {"off": False, "unset": None}.get(a.think) if a.think != "config" else think_setting(b, a.models_config)
    think, ref_think = pick(a.test), (pick(a.ref) if a.ref else None)
    res = {"protocol": "2.3", "checked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "test": a.test,
           "ref": a.ref, "texts": {"system": SYSTEM, "system_long": SYSTEM_LONG, "user": U1, "assistant": A1,
                                   "user2": U2}, "think_mode": a.think, "think": think}
    t, show = examine(a.base, a.test, a.models_dir, think)
    res["test_model"] = t
    c = t["counts"]
    res["system_rendered"] = c["SLU"] > c["SU"] and c["SLUAU"] > c["SUAU"]
    res["builtin_system_replaced"] = bool(t["hashes"]["system_sha256"]) and c["SU"] != c["U"]
    checks = {}
    if t["rendered"]:
        cc, info = content_checks(t["rendered"], show, think)
        checks.update(cc)
        checks.update(count_checks(t["rendered"], c))
        res["informational"] = info
    else:
        checks["content_checked"] = False
    if a.ref:
        r, _ = examine(a.base, a.ref, a.models_dir, ref_think)
        res["ref_model"] = r
        res["builtin_tokens_when_no_system"] = c["U"] - r["counts"]["U"]
        res["count_diff_by_layout"] = {k: c[k] - r["counts"][k] for k in LAYOUTS}
        res["template_equal"] = t["hashes"]["template_sha256"] == r["hashes"]["template_sha256"]
        res["parameters_equal"] = t["hashes"]["parameters_sha256"] == r["hashes"]["parameters_sha256"]
        same_render = bool(t["rendered"] and r["rendered"]) and all(
            t["rendered"][k]["rendered"] == r["rendered"][k]["rendered"] for k in SINGLE)
        res["rendering_equal"] = same_render
        res["identical_to_ref"] = (res["template_equal"] and res["parameters_equal"] and same_render
                                   and all(v == 0 for v in res["count_diff_by_layout"].values()))
        checks["identical_to_ref"] = res["identical_to_ref"]
    res["checks"] = checks
    res["pass_v23"] = bool(checks) and all(checks.values())
    name = a.test.replace("/", "_").replace(":", "_")
    p = pathlib.Path(a.out) if a.out else PROJECT / "results" / "logs" / f"render_check_v23_{name}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"test": a.test, "ref": a.ref, "pass_v23": res["pass_v23"],
                      "failed": sorted(k for k, v in checks.items() if not v),
                      "builtin_used_without_system": (res.get("informational") or {}).get("builtin_used_without_system"),
                      "quant": t["hashes"]["quantization"], "log": p.as_posix()}))
    return 0 if res["pass_v23"] else 1


if __name__ == "__main__":
    sys.exit(main())
