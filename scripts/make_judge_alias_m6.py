"""Judge builds of model 6 (protocol v2.3, Sections 3.3 and 11.7).

Writes a Modelfile (LF line endings) that holds the weights blob of an explicit source tag of model 6, plus model 4's
official Llama 3.1 template and parameters, with no built-in system prompt. Two builds, each under its own alias:

  role 'primary'      source: the respondent build (config/models.json model 6 'model', Q4_0 weights)
                      alias:  agentscontrol/llama3.1-8b-abliterated-judge-q4_0
  role 'sensitivity'  source: mannix/llama3.1-8b-abliterated:q4_k_m (the Q4_K_M build of v2.2)
                      alias:  agentscontrol/llama3.1-8b-abliterated-judge          (Section 8.5)

There is no default source: the role and the source are both given, and the primary build must carry the very
weights of the respondent build. A JSON record of the build (source, weights digest, template and parameter
digests, alias, Modelfile SHA-256) is written next to the Modelfile. Nothing here talks to Ollama.

Then, with the PI's OK (local GPU work):
  ollama create <alias> -f <modelfile>
  python -I scripts/check_system_override.py --test <alias>:latest --ref llama3.1:8b
and record the alias's digest in config/models.json (judge_model_digest or judge_model_sensitivity_digest) only
after both checks of Section 11.7 pass.

Usage:
  python -I scripts/make_judge_alias_m6.py --models-dir E:/ollama/models --role primary \
         --source mannix/llama3.1-8b-abliterated:latest [--out config/ollama/Modelfile_m6_judge_primary]
Standard library only.
"""
import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODELS_CFG = ROOT / "config" / "models.json"
REFERENCE = "llama3.1:8b"
ROLES = {"primary": {"alias": "agentscontrol/llama3.1-8b-abliterated-judge-q4_0", "source": None},
         "sensitivity": {"alias": "agentscontrol/llama3.1-8b-abliterated-judge",
                         "source": "mannix/llama3.1-8b-abliterated:q4_k_m"}}


def manifest(models_dir, tag):
    name, _, ver = tag.partition(":")
    ver = ver or "latest"
    parts = name.split("/")
    ns, repo = ("library", parts[0]) if len(parts) == 1 else (parts[0], parts[1])
    for base in (models_dir / "manifests" / "registry.ollama.ai", models_dir / "manifests-v2" / "ollama.com"):
        p = base / ns / repo / ver
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"no manifest for {tag} under {models_dir}")


def blob(models_dir, digest):
    return models_dir / "blobs" / digest.replace(":", "-")


def layer(m, kind):
    return [x for x in m["layers"] if x["mediaType"].endswith("." + kind)]


def respondent_tag(cfg_path=None):
    models = json.loads(pathlib.Path(cfg_path or MODELS_CFG).read_text(encoding="utf-8"))["models"]
    return next(m["model"] for m in models if m["n"] == 6)


def build(models_dir, role, source, cfg_path=None):
    """(Modelfile text, record). Refuses a source that does not fit the role."""
    if role not in ROLES:
        raise SystemExit(f"role must be one of {sorted(ROLES)}")
    want = respondent_tag(cfg_path) if role == "primary" else ROLES[role]["source"]
    if source != want:
        raise SystemExit(f"role {role} takes the source {want}, not {source} (Section 3.3)")
    m4, m6 = manifest(models_dir, REFERENCE), manifest(models_dir, source)
    weights = layer(m6, "model")
    if len(weights) != 1:
        raise SystemExit(f"{source}: {len(weights)} weight layers")
    weights = weights[0]["digest"]
    t_layer, p_layer = layer(m4, "template")[0]["digest"], layer(m4, "params")[0]["digest"]
    tmpl4 = blob(models_dir, t_layer).read_bytes().decode("utf-8")
    params4 = json.loads(blob(models_dir, p_layer).read_text(encoding="utf-8"))
    if '"""' in tmpl4 or "\r" in tmpl4:
        raise SystemExit("model 4's template cannot be quoted in a Modelfile as it is")
    lines = [f"FROM {blob(models_dir, weights).as_posix()}", f'TEMPLATE """{tmpl4}"""']
    for k, v in params4.items():
        for x in (v if isinstance(v, list) else [v]):
            lines.append(f"PARAMETER {k} {json.dumps(x) if isinstance(x, str) else x}")
    text = "\n".join(lines) + "\n"
    rec = {"role": role, "alias": ROLES[role]["alias"], "source": source, "weights_digest": weights,
           "reference": REFERENCE, "template_layer": t_layer, "params_layer": p_layer,
           "params": sorted(params4), "system_prompt": None,
           "modelfile_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
           "next": [f"ollama create {ROLES[role]['alias']} -f <modelfile>",
                    f"python -I scripts/check_system_override.py --test {ROLES[role]['alias']}:latest --ref {REFERENCE}"]}
    return text, rec


def main(argv=None):
    ap = argparse.ArgumentParser(description="Modelfile of a judge build of model 6 (no default source)")
    ap.add_argument("--models-dir", required=True)
    ap.add_argument("--role", required=True, choices=sorted(ROLES))
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    text, rec = build(pathlib.Path(a.models_dir), a.role, a.source)
    out = pathlib.Path(a.out or ROOT / "config" / "ollama" / f"Modelfile_m6_judge_{a.role}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))                     # LF only
    rec["modelfile"] = out.as_posix()
    out.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: rec[k] for k in ("role", "alias", "source", "weights_digest", "modelfile_sha256")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
