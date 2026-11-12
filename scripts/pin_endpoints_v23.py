"""Record the pinned endpoint of every model reached through OpenRouter, and the judge builds of model 6, in
config/models.json (decision D16 and Section 3.3 of protocol v2.3).

For each OpenRouter model, 'pin' holds the facts of the endpoint named first in its provider_order, as listed in
the public zero-retention snapshot of 11 November 2026 (data/selection/2026-11-11/raw/or_endpoints_zdr.json):
tag, serving provider, precision, prices (US$ per million tokens), safety retention, status, context length and
supported parameters. src/spend_v23.preflight compares the live list with these facts before every paid session,
and the reservation bound uses the larger of the recorded and the live prices. 'd2_safety_retention' records
decision D2 for an endpoint marked for safety retention: null (not decided: no call), 'safe_only' or 'all'.

Model 6 (Section 3.3): the primary judge build is the Q4_0 weights of the respondent build with model 4's chat
template ('judge_model'; its digest stays null until scripts/make_judge_alias_m6.py has built it and both checks
of Section 11.7 have passed); the Q4_K_M build of v2.2 is the sensitivity build ('judge_model_sensitivity').

Usage: python -I scripts/pin_endpoints_v23.py            show what would change
       python -I scripts/pin_endpoints_v23.py --write    write config/models.json (same formatting)
No network access. Standard library only.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import spend_v23 as S  # noqa: E402

MODELS = ROOT / "config" / "models.json"
SNAPSHOT = ROOT / "data" / "selection" / "2026-11-11" / "raw" / "or_endpoints_zdr.json"
SNAPSHOT_DATE = "2026-11-11"
M6_PRIMARY = "agentscontrol/llama3.1-8b-abliterated-judge-q4_0"
M6_SENSITIVITY = "agentscontrol/llama3.1-8b-abliterated-judge:latest"


def pin_of(m, zdr):
    tag = (m.get("provider_order") or [None])[0]
    hit = [e for e in zdr if e.get("model_id") == m["model"] and e.get("tag") == tag]
    if len(hit) != 1:
        raise SystemExit(f"{m['key']}: {len(hit)} entries for {m['model']} at {tag} in the snapshot")
    facts = S.endpoint_facts(hit[0])
    facts["supported_parameters"] = sorted(hit[0].get("supported_parameters") or [])
    facts["discount"] = (hit[0].get("pricing") or {}).get("discount")
    facts["source"] = SNAPSHOT.relative_to(ROOT).as_posix()
    facts["recorded"] = SNAPSHOT_DATE
    return facts


def update(cfg, zdr):
    changes = []
    for m in cfg["models"]:
        if S.account_of(m) == "openrouter":
            pin = pin_of(m, zdr)
            if m.get("pin") != pin:
                changes.append(f"{m['n']:2d} {m['key']}: pin {pin['tag']} ({pin['provider_name']}, {pin['quantization']}, "
                               f"in {pin['prompt_usd_per_m']} / out {pin['completion_usd_per_m']} US$/M, "
                               f"safety_retention {pin['safety_retention']}, status {pin['status']})")
                m["pin"] = pin
            if "d2_safety_retention" not in m:
                m["d2_safety_retention"] = None
                changes.append(f"{m['n']:2d} {m['key']}: d2_safety_retention null (decision D2 not recorded)")
            if m.get("allow_fallbacks", False) or m.get("zdr") is not True:
                raise SystemExit(f"{m['key']}: fallbacks must be off and zdr on (decision D16)")
        if m["n"] == 6:
            old = m.get("judge_model")
            if old != M6_PRIMARY:
                m["judge_model_sensitivity"] = M6_SENSITIVITY
                m["judge_model_sensitivity_digest"] = m.get("judge_model_digest")
                m["judge_model"] = M6_PRIMARY
                m["judge_model_digest"] = None
                m["judge_model_note"] = (
                    "Protocol v2.3, Section 3.3. Primary judge build (judge_model): the Q4_0 weights of the respondent "
                    "build with model 4's official Llama 3.1 template and parameters and no built-in prompt; its "
                    "digest is recorded after scripts/make_judge_alias_m6.py has built it and both checks of Section "
                    "11.7 have passed (until then no judging call of model 6 is sent). Sensitivity build "
                    "(judge_model_sensitivity): the Q4_K_M build of v2.2 (mannix/llama3.1-8b-abliterated:q4_k_m "
                    "weights with the same template), which on 8 Nov 2026 matched llama3.1:8b in template hash, "
                    "parameter hash and prompt token counts in six layouts.")
                changes.append(f" 6 {m['key']}: judge_model {old} -> {M6_PRIMARY} (digest null until built); "
                               f"sensitivity build {M6_SENSITIVITY}")
    return changes


def main():
    text = MODELS.read_text(encoding="utf-8")
    cfg = json.loads(text)
    if json.dumps(cfg, indent=1, ensure_ascii=False) + "\n" != text:
        raise SystemExit("config/models.json does not round-trip with indent=1: refusing to rewrite it")
    zdr = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["data"]
    changes = update(cfg, zdr)
    print("\n".join(changes) if changes else "nothing to change")
    if "--write" in sys.argv and changes:
        MODELS.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print("written", MODELS.relative_to(ROOT))


if __name__ == "__main__":
    main()
