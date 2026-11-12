"""Token-level identity check of the T4 judge pairs (protocol v2.2, Section 8.3; round-4 audits A4-M2, B4-M3).

Local Ollama only, benign synthetic text only. For each pair (base judge, abliterated judge) it compares:
  1. model metadata from /api/show (verbose): architecture, layer and head counts, embedding size,
     tokenizer model, pre-tokenizer, SHA-256 of the token list, merges and token types, and the tensor
     names and shapes;
  2. the rendered prompt TOKEN IDS for the single-turn layouts (user; system + user), from /api/generate
     with the judge options (think false, explicit sampling options, num_ctx 8192, num_predict 1): the
     returned context minus the generated tokens;
  3. whether think=false is honoured on /api/chat: no thinking field, no "<think>" in the content, and an
     output well below the cap;
  4. greedy outputs on three benign prompts (temperature 0, 120 tokens): the length of the identical prefix.
     A shared prefix shows that both builds run the same forward path (an extra block applied as a layer
     would make the outputs diverge at once).
Descriptive metadata (general.*, quantize.*) is ignored. An extra next-token-prediction (MTP / nextn) block
is reported separately: it is not part of standard decoding, which the greedy comparison checks.
Multi-turn layouts cannot be read as token IDs through this API; their token counts are compared by
scripts/check_system_override.py, and their rendered text through the server log (OLLAMA_DEBUG) if needed.

Usage: python -I scripts/check_t4_tokens.py [out.json]   (default results/logs/t4_token_check_<date>.json)
"""
import datetime as dt
import hashlib
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:11434"
PAIRS = [("llama3.1:8b", "agentscontrol/llama3.1-8b-abliterated-judge:latest"),
         ("qwen3:8b", "huihui_ai/qwen3-abliterated:8b-v2-q4_K_M"),
         ("qwen3.5:4b", "kaineone/qwen3.5-4b-abliterated:latest")]
OPTIONS = {"temperature": 0, "seed": 20261108, "top_k": 40, "top_p": 1, "min_p": 0, "repeat_penalty": 1,
           "presence_penalty": 0, "frequency_penalty": 0, "num_ctx": 8192}
SYSTEM = "You label answers. Reply with one word."                       # synthetic, benign
USER = "Label this answer: 'Paris is the capital of France.'"           # synthetic, benign


def post(path, body, timeout=600):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def h(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def metadata(model):
    show = post("/api/show", {"model": model, "verbose": True})
    info = show.get("model_info") or {}
    arch = info.get("general.architecture")
    nextn = int(info.get(f"{arch}.nextn_predict_layers") or 0)
    keys = {k: v for k, v in info.items() if not k.startswith(("tokenizer.", "general.", "quantize."))
            and not k.endswith("nextn_predict_layers")}
    if nextn:                                  # main path only: drop the trailing next-token-prediction block(s)
        keys[f"{arch}.block_count"] = keys[f"{arch}.block_count"] - nextn
        for k, v in list(keys.items()):
            if isinstance(v, list) and len(v) == keys[f"{arch}.block_count"] + nextn:
                keys[k] = v[: keys[f"{arch}.block_count"]]
    n_main = keys.get(f"{arch}.block_count")
    tensors = [(t.get("name"), tuple(t.get("shape") or ())) for t in show.get("tensors") or []]
    extra = {n for n, _ in tensors if n_main is not None and n.startswith("blk.") and int(n.split(".")[1]) >= n_main}
    main = [t for t in tensors if t[0] not in extra]
    return {"architecture": arch, "hparams_sha": h(keys), "nextn_predict_layers": nextn,
            "extra_block_tensors": len(extra),
            "tokenizer_model": info.get("tokenizer.ggml.model"), "pre_tokenizer": info.get("tokenizer.ggml.pre"),
            "tokens_sha": h(info.get("tokenizer.ggml.tokens")), "merges_sha": h(info.get("tokenizer.ggml.merges")),
            "token_type_sha": h(info.get("tokenizer.ggml.token_type")),
            "n_tensors": len(tensors), "tensor_shapes_sha": h(sorted(main)),
            "quantization": (show.get("details") or {}).get("quantization_level")}


def prompt_tokens(model, system):
    body = {"model": model, "prompt": USER, "stream": False, "think": False, "keep_alive": "5m",
            "options": dict(OPTIONS, num_predict=1)}
    if system:
        body["system"] = system
    r = post("/api/generate", body)
    ctx = r.get("context")
    if ctx is None:
        return {"available": False}
    toks = ctx[: len(ctx) - int(r.get("eval_count") or 0)]          # drop the generated token(s)
    return {"available": True, "n_prompt_ids": len(toks), "prompt_ids_sha": h(toks)}


GREEDY = ["Explain in three sentences why the sky looks blue.",
          "Write a short Python function that returns the sum of a list of numbers.",
          "List the planets of the solar system in order from the Sun."]


def greedy(model):
    return [post("/api/chat", {"model": model, "stream": False, "think": False,
                               "options": dict(OPTIONS, num_predict=120),
                               "messages": [{"role": "user", "content": p}]})["message"]["content"] for p in GREEDY]


def common_prefix(x, y):
    n = 0
    for a, b in zip(x, y):
        if a != b:
            break
        n += 1
    return n


def think_off(model):
    r = post("/api/chat", {"model": model, "stream": False, "think": False, "keep_alive": "5m",
                           "options": dict(OPTIONS, num_predict=600),
                           "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": USER}]})
    msg = r.get("message") or {}
    content = msg.get("content") or ""
    return {"thinking_field_empty": not (msg.get("thinking") or ""), "think_tag_in_content": "<think>" in content,
            "eval_count": r.get("eval_count"), "done_reason": r.get("done_reason")}


def unload(model):
    try:
        post("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
    except Exception:
        pass


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
        ROOT / "results" / "logs" / f"t4_token_check_{dt.date.today().isoformat()}.json"
    res = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "ollama": json.loads(urllib.request.urlopen(BASE + "/api/version", timeout=30).read()).get("version"),
           "pairs": []}
    for base, abl in PAIRS:
        entry = {"base": base, "abliterated": abl, "members": {}}
        for m in (base, abl):
            d = {"metadata": metadata(m), "tokens_user": prompt_tokens(m, None),
                 "tokens_system_user": prompt_tokens(m, SYSTEM), "think_off": think_off(m), "greedy": greedy(m)}
            unload(m)
            entry["members"][m] = d
        a, b = (entry["members"][base], entry["members"][abl])
        same = lambda x, y: x == y
        entry["identical"] = {
            "architecture_hparams": same(a["metadata"]["architecture"], b["metadata"]["architecture"])
            and same(a["metadata"]["hparams_sha"], b["metadata"]["hparams_sha"]),
            "tokenizer": all(same(a["metadata"][k], b["metadata"][k]) for k in
                             ("tokenizer_model", "pre_tokenizer", "tokens_sha", "merges_sha", "token_type_sha")),
            "tensor_shapes": same(a["metadata"]["tensor_shapes_sha"], b["metadata"]["tensor_shapes_sha"]),
            "prompt_ids_user": same(a["tokens_user"], b["tokens_user"]),
            "prompt_ids_system_user": same(a["tokens_system_user"], b["tokens_system_user"]),
            "think_off_both": all(x["think_off"]["thinking_field_empty"] and not x["think_off"]["think_tag_in_content"]
                                  for x in (a, b)),
        }
        entry["extra_nextn_block_tensors"] = {m: entry["members"][m]["metadata"]["extra_block_tensors"] for m in (base, abl)}
        entry["greedy_identical_prefix_chars"] = [common_prefix(x, y) for x, y in zip(a["greedy"], b["greedy"])]
        for m in (base, abl):          # benign outputs; keep lengths and hashes only
            g = entry["members"][m].pop("greedy")
            entry["members"][m]["greedy_len_sha"] = [(len(t), h(t)) for t in g]
        res["pairs"].append(entry)
        print(base, "vs", abl, json.dumps(entry["identical"]), "extra nextn tensors", entry["extra_nextn_block_tensors"],
              "greedy prefix", entry["greedy_identical_prefix_chars"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    print("->", out)


if __name__ == "__main__":
    main()
