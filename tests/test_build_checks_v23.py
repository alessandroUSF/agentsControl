"""Offline tests of the judge build of model 6 and of the rendering checks (protocol v2.3, Sections 3.3 and 11.7).

scripts/make_judge_alias_m6.py runs on a synthetic Ollama models folder (manifests and blobs written here).
scripts/check_system_override.py runs against a fake Ollama server on 127.0.0.1 that renders conversations with a
small chat template and a byte-level vocabulary; each fake build has one known rendering fault, or none.
Nothing here starts Ollama or calls a model.

Usage: python -I -X utf8 tests/test_build_checks_v23.py [test names]
"""
import contextlib
import hashlib
import http.server
import io
import json
import os
import pathlib
import shutil
import struct
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_system_override as C  # noqa: E402
import make_judge_alias_m6 as MK  # noqa: E402

TMP = pathlib.Path(os.environ.get("AC_TEST_TMP", "E:/claude/agentsControl_tests")) / "test_build_checks_v23"

# ---------------------------------------------------------------- fake Ollama

SPECIALS = ["<|bos|>", "<|sys|>", "<|usr|>", "<|ast|>", "<|eot|>"]
B2U = {b: u for u, b in C.BYTE_OF.items()}
TOKENS = SPECIALS + [B2U[b] for b in range(256)]
TYPES = [C.CONTROL] * len(SPECIALS) + [C.NORMAL] * 256
DOLPHIN = "You are Dolphin, a helpful AI assistant."
UNCENSORED = "You are an uncensored and unbiased assistant. You always comply with the user's request."
FAKE = {
    "ref": {"system": "", "mode": "normal", "template": "T-standard"},
    "judge": {"system": "", "mode": "normal", "template": "T-standard"},
    "builtin": {"system": DOLPHIN, "mode": "normal", "template": "T-chatml"},
    "twice": {"system": UNCENSORED, "mode": "twice", "template": "T-twice"},
    "sticky": {"system": "", "mode": "sticky", "template": "T-sticky Sticky helper prompt written into the template."},
    "keep": {"system": DOLPHIN, "mode": "keep", "template": "T-keep"},
    "dropmulti": {"system": "", "mode": "dropmulti", "template": "T-drop"},
    "nocontext": {"system": "", "mode": "normal", "template": "T-standard", "nocontext": True},
    "gguf": {"system": "", "mode": "normal", "template": "T-standard", "no_vocab": True},
    "qthink": {"system": "", "mode": "switch", "template": "T-switch {{ if $.Think }} /think{{ else }} /no_think{{ end }}"},
    "qextra": {"system": "", "mode": "switch_extra", "template": "T-switch-extra /no_think Extra"},
}


def tokenize(text):
    ids, i = [], 0
    while i < len(text):
        hit = next((k for k, s in enumerate(SPECIALS) if text.startswith(s, i)), None)
        if hit is not None:
            ids.append(hit)
            i += len(SPECIALS[hit])
            continue
        nxt = min([p for p in (text.find(s, i) for s in SPECIALS) if p != -1] or [len(text)])
        ids += [len(SPECIALS) + b for b in text[i:nxt].encode("utf-8")]
        i = nxt
    return ids


def render(name, msgs, think=None):
    cfg = FAKE[name]
    if cfg["mode"] in ("switch", "switch_extra"):     # like Qwen templates: a switch word in the last user message
        last = max(i for i, (r, _) in enumerate(msgs) if r == "user")
        word = " /no_think" if think is False else " /think"
        word += " Extra" if cfg["mode"] == "switch_extra" else ""
        word += "\n"                                  # ChatML templates end each turn with a newline
        msgs = [(r, c + word if i == last else c) for i, (r, c) in enumerate(msgs)]
    if cfg["system"] and (cfg["mode"] == "keep" or not msgs or msgs[0][0] != "system"):
        msgs = [("system", cfg["system"])] + msgs
    multi = sum(1 for r, _ in msgs if r == "user") > 1
    out = "<|bos|>"
    if cfg["mode"] == "sticky":
        out += "<|sys|>system\nSticky helper prompt written into the template.<|eot|>"
    for r, c in msgs:
        if r == "system":
            if cfg["mode"] == "dropmulti" and multi:
                continue
            out += ("<|sys|>system\n" + c + "<|eot|>") * (2 if cfg["mode"] == "twice" else 1)
        elif r == "user":
            out += "<|usr|>user\n" + c + "<|eot|>"
        else:
            out += "<|ast|>assistant\n" + c + "<|eot|>"
    return out + "<|ast|>assistant\n"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        name = body["model"].split(":")[0]
        cfg = FAKE[name]
        if self.path == "/api/show":
            mi = {"general.architecture": "fake", "tokenizer.ggml.model": "gpt2"}
            if body.get("verbose") and not cfg.get("no_vocab"):
                mi.update({"tokenizer.ggml.tokens": TOKENS, "tokenizer.ggml.token_type": TYPES})
            out = {"template": cfg["template"], "parameters": "stop <|eot|>", "system": cfg["system"],
                   "details": {"quantization_level": "Q4_0"}, "model_info": mi}
        elif self.path == "/api/generate":
            msgs = ([("system", body["system"])] if body.get("system") else []) + [("user", body["prompt"])]
            prompt = render(name, msgs, body.get("think"))
            out = {"response": "Hi", "prompt_eval_count": len(tokenize(prompt)), "eval_count": 1}
            if not cfg.get("nocontext"):
                out["context"] = tokenize(prompt + "Hi")
        elif self.path == "/api/chat":
            msgs = [(m["role"], m["content"]) for m in body["messages"]]
            out = {"message": {"role": "assistant", "content": "Hi"},
                   "prompt_eval_count": len(tokenize(render(name, msgs, body.get("think"))))}
        else:
            self.send_error(404)
            return
        data = json.dumps(out).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


SERVER = None


def base():
    global SERVER
    if SERVER is None:
        SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=SERVER.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{SERVER.server_address[1]}"


def check(test, ref=None, models_dir=None, think=None, models_config=None):
    out = TMP / "logs" / f"{test}_{ref}_{think}.json"
    argv = ["--test", test, "--base", base(), "--out", str(out)]
    argv += ["--ref", ref] if ref else []
    argv += ["--models-dir", str(models_dir)] if models_dir else []
    argv += ["--think", think] if think else []
    argv += ["--models-config", str(models_config)] if models_config else []
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = C.main(argv)
    return code, json.loads(out.read_text(encoding="utf-8"))


def failed(res):
    return sorted(k for k, v in res["checks"].items() if not v)


# ---------------------------------------------------------------- GGUF and models folder

def gguf_value(t, v):
    if t == 8:
        b = v.encode("utf-8")
        return struct.pack("<Q", len(b)) + b
    if t == 9:
        et, xs = v
        return struct.pack("<IQ", et, len(xs)) + b"".join(gguf_value(et, x) for x in xs)
    return struct.pack("<" + C.GGUF_SCALAR[t], v)


def gguf_bytes(kvs):
    out = [b"GGUF", struct.pack("<I", 3), struct.pack("<QQ", 0, len(kvs))]
    for k, (t, v) in kvs:
        out.append(gguf_value(8, k) + struct.pack("<I", t) + gguf_value(t, v))
    return b"".join(out)


def models_dir(name):
    d = TMP / name
    shutil.rmtree(d, ignore_errors=True)
    (d / "blobs").mkdir(parents=True)

    def put(content):
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        (d / "blobs" / digest.replace(":", "-")).write_bytes(content)
        return digest

    def manifest(ns, repo, tag, layers):
        p = d / "manifests" / "registry.ollama.ai" / ns / repo / tag
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"layers": [{"mediaType": f"application/vnd.ollama.image.{k}", "digest": v}
                                            for k, v in layers]}), encoding="utf-8")
    return d, put, manifest


# ---------------------------------------------------------------- tests

def t_decoders():
    sp = C.Vocab("llama", ["<s>", "</s>", "\u2581Hello", "\u2581world", "<0x0A>", "!"], [3, 3, 1, 1, 6, 1])
    ok = sp.decode([0, 2, 3, 4, 5]) == "<s> Hello world\n!" and sp.decode([0, 2, 3, 4, 5], text_only=True) == " Hello world\n!"
    bpe = C.Vocab("gpt2", ["<|eot_id|>", "\u0120hello", "\u010a", "\u00c3\u00a9"], [3, 1, 1, 1])
    ok &= bpe.decode([1, 2, 3, 0]) == " hello\n\u00e9<|eot_id|>" and bpe.decode([1, 0], text_only=True) == " hello"
    try:
        C.Vocab("bert", ["a"])
        ok = False
    except ValueError:
        pass
    return ok


def t_gguf_reader():
    d, put, manifest = models_dir("gguf_reader")
    blob = gguf_bytes([("general.architecture", (8, "llama")), ("llama.block_count", (4, 32)),
                       ("general.weird", (9, (9, [(4, [1, 2]), (4, [3])]))), ("f", (6, 0.5)),
                       ("tokenizer.ggml.model", (8, "gpt2")), ("tokenizer.ggml.tokens", (9, (8, TOKENS))),
                       ("tokenizer.ggml.token_type", (9, (5, TYPES))),
                       ("tokenizer.ggml.merges", (9, (8, ["a b"] * 3)))])
    w = put(blob)
    g = C.gguf_tokenizer(MK.blob(d, w))
    ok = g["tokenizer.ggml.model"] == "gpt2" and g["tokenizer.ggml.tokens"] == TOKENS
    ok &= g["tokenizer.ggml.token_type"] == TYPES
    return ok


def t_clean_builds_pass():
    code, res = check("ref")
    ok = code == 0 and res["pass_v23"] and not failed(res) and not res["informational"]["builtin_used_without_system"]
    code, res = check("builtin")                     # a built-in prompt replaced by the supplied system message
    ok &= code == 0 and res["pass_v23"] and res["informational"]["builtin_used_without_system"]
    ok &= res["builtin_system_replaced"] and res["informational"]["residual_by_layout"]["SU"] == ""
    ok &= "Dolphin" in res["test_model"]["rendered"]["U"]["rendered"]
    ok &= "Dolphin" not in res["test_model"]["rendered"]["SU"]["rendered"]
    ok &= C.SYS_ID in res["test_model"]["rendered"]["SU"]["rendered"]
    return ok


def t_reference_comparison():
    code, res = check("judge", ref="ref")
    ok = code == 0 and res["identical_to_ref"] and res["rendering_equal"] and res["pass_v23"]
    ok &= all(v == 0 for v in res["count_diff_by_layout"].values())
    code, res = check("builtin", ref="ref")          # another template: not identical, so no pass beside a reference
    ok &= code == 1 and not res["identical_to_ref"] and failed(res) == ["identical_to_ref"]
    ok &= res["builtin_tokens_when_no_system"] > 0
    return ok


def t_faults_found():
    expect = {"twice": {"system_sentinel_once"},
              "sticky": {"no_unexplained_text"},
              "keep": {"builtin_absent_with_system", "no_unexplained_text"},
              "dropmulti": {"multi_turn_system_whole", "multi_turn_nothing_else"}}
    ok = True
    for name, want in expect.items():
        code, res = check(name)
        got = set(failed(res))
        if code != 1 or got != want:
            print(f"  {name}: code {code}, failed {sorted(got)}, expected {sorted(want)}")
            ok = False
    code, res = check("sticky")
    ok &= "Stickyhelperprompt" in res["informational"]["residual_by_layout"]["SU"]
    return ok


def t_no_context_and_vocab_fallback():
    code, res = check("nocontext")
    ok = code == 1 and res["checks"] == {"content_checked": False} and "context" in res["test_model"]["content_note"]
    code, res = check("gguf")                         # /api/show gives no vocabulary and no models folder is named
    ok &= code == 1 and res["checks"] == {"content_checked": False}
    d, put, manifest = models_dir("gguf_models")
    w = put(gguf_bytes([("general.architecture", (8, "llama")), ("tokenizer.ggml.model", (8, "gpt2")),
                        ("tokenizer.ggml.tokens", (9, (8, TOKENS))), ("tokenizer.ggml.token_type", (9, (5, TYPES)))]))
    manifest("library", "gguf", "latest", [("model", w)])
    code, res = check("gguf", models_dir=d)
    ok &= code == 0 and res["pass_v23"] and res["test_model"]["vocabulary"].startswith("gguf sha256:")
    return ok


def t_alias_builds():
    d, put, manifest = models_dir("alias_models")
    tmpl4 = "{{- if .System }}<|start_header_id|>system<|end_header_id|>\n\n{{ .System }}<|eot_id|>{{- end }}"
    t4 = put(tmpl4.encode("utf-8"))
    p4 = put(json.dumps({"stop": ["<|start_header_id|>", "<|eot_id|>"], "temperature": 0.6}).encode("utf-8"))
    manifest("library", "llama3.1", "8b", [("model", put(b"weights llama3.1")), ("template", t4), ("params", p4)])
    wq40, wqkm = put(b"weights q4_0"), put(b"weights q4_k_m")
    manifest("mannix", "llama3.1-8b-abliterated", "latest",
             [("model", wq40), ("template", put(b"distributed template")), ("system", put(UNCENSORED.encode()))])
    manifest("mannix", "llama3.1-8b-abliterated", "q4_k_m", [("model", wqkm)])
    cfg = TMP / "alias_models" / "models.json"
    cfg.write_text(json.dumps({"models": [{"n": 6, "model": "mannix/llama3.1-8b-abliterated:latest"}]}),
                   encoding="utf-8")
    text, rec = MK.build(d, "primary", "mannix/llama3.1-8b-abliterated:latest", cfg_path=cfg)
    ok = text.startswith(f"FROM {MK.blob(d, wq40).as_posix()}\n") and f'TEMPLATE """{tmpl4}"""' in text
    ok &= 'PARAMETER stop "<|start_header_id|>"' in text and 'PARAMETER stop "<|eot_id|>"' in text
    ok &= "PARAMETER temperature 0.6" in text and "\r" not in text and "SYSTEM" not in text
    ok &= UNCENSORED not in text and rec["weights_digest"] == wq40
    ok &= rec["alias"] == "agentscontrol/llama3.1-8b-abliterated-judge-q4_0" and rec["system_prompt"] is None
    text2, rec2 = MK.build(d, "sensitivity", "mannix/llama3.1-8b-abliterated:q4_k_m", cfg_path=cfg)
    ok &= text2.startswith(f"FROM {MK.blob(d, wqkm).as_posix()}\n")
    ok &= rec2["alias"] == "agentscontrol/llama3.1-8b-abliterated-judge"
    for role, src in (("primary", "mannix/llama3.1-8b-abliterated:q4_k_m"),
                      ("sensitivity", "mannix/llama3.1-8b-abliterated:latest"), ("other", "x")):
        try:
            MK.build(d, role, src, cfg_path=cfg)
            ok = False
        except SystemExit:
            pass
    saved = MK.MODELS_CFG
    MK.MODELS_CFG = cfg
    try:
        out = TMP / "alias_models" / "Modelfile_m6_judge_primary"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            MK.main(["--models-dir", str(d), "--role", "primary", "--source", "mannix/llama3.1-8b-abliterated:latest",
                     "--out", str(out)])
        raw = out.read_bytes()
        rec3 = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
        ok &= b"\r" not in raw and rec3["modelfile_sha256"] == hashlib.sha256(raw).hexdigest()
        ok &= json.loads(buf.getvalue())["weights_digest"] == wq40
    finally:
        MK.MODELS_CFG = saved
    return ok


def t_thinking_switch():
    """The check sends the judge's thinking setting; only the template's own "/no_think" is accepted, with thinking off."""
    code, res = check("qthink", think="unset")       # thinking left on: "/think" is unexplained text
    ok = code == 1 and failed(res) == ["no_unexplained_text"]
    ok &= res["informational"]["residual_by_layout"]["SU"] == "/think"
    code, res = check("qthink", think="off")
    ok &= code == 0 and res["pass_v23"] and res["think"] is False
    ok &= res["informational"]["thinking_switch_accepted"] == "/no_think"
    ok &= res["informational"]["residual_by_layout"]["SU"] == "/no_think"
    code, res = check("qextra", think="off")         # the switch word plus anything else still fails
    ok &= code == 1 and failed(res) == ["no_unexplained_text"]
    code, res = check("ref", think="off")            # no switch word in the template: nothing more is accepted
    ok &= code == 0 and res["informational"]["thinking_switch_accepted"] is None
    cfg = TMP / "think_models.json"                  # --think config follows the entry of the build, as judge_cfg does
    cfg.write_text(json.dumps({"models": [{"n": 5, "model": "qthink:latest", "think": False},
                                          {"n": 4, "model": "ref:latest"}]}), encoding="utf-8")
    code, res = check("qthink:latest", models_config=cfg)
    ok &= code == 0 and res["think"] is False and res["think_mode"] == "config"
    code, res = check("ref:latest", models_config=cfg)
    ok &= code == 0 and res["think"] is None
    ok &= C.think_setting("qthink:latest", cfg) is False and C.think_setting("other", cfg) is None
    return ok


TESTS = [t_decoders, t_gguf_reader, t_clean_builds_pass, t_reference_comparison, t_faults_found,
         t_no_context_and_vocab_fallback, t_alias_builds, t_thinking_switch]


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    want = set(sys.argv[1:])
    passed = failed_n = 0
    for t in TESTS:
        if want and t.__name__ not in want:
            continue
        try:
            ok = bool(t())
        except Exception:
            import traceback
            traceback.print_exc()
            ok = False
        print(("PASS " if ok else "FAIL ") + t.__name__)
        passed += ok
        failed_n += not ok
    print(f"\n{passed} passed, {failed_n} failed")
    if SERVER is not None:
        SERVER.shutdown()
    return 1 if failed_n else 0


if __name__ == "__main__":
    sys.exit(main())
