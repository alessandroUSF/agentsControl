"""Prompts of the crossed subset of protocol v2.3 (Section 8.8), recorded in config/crossed_subset_v23.json.

The rule is src/plan_v23.crossed_prompts: in each source of the harmful frame, the first 50 prompts in the order of
the SHA-256 of their identifiers. It reads the frame only (identifiers and sources, never a prompt text), so the
subset is fixed before any answer exists. The judging runner and the analysis compute it from the frame with the same
function; this script prints it, records it with the SHA-256 of the list, and checks a stored record against the
rule.

Usage: python -I scripts/crossed_subset_v23.py            print the counts and compare with the stored record
       python -I scripts/crossed_subset_v23.py --write    write config/crossed_subset_v23.json
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import frames_v23  # noqa: E402
import plan_v23  # noqa: E402

OUT = ROOT / "config" / "crossed_subset_v23.json"


def build(frames=None):
    frames = frames or frames_v23.frames()
    ids = plan_v23.crossed_prompts(frames)
    src = frames["harmful"][1]
    by_source = {}
    for p in ids:
        by_source.setdefault(src[p], []).append(p)
    return {"protocol": "2.3", "section": "8.8",
            "rule": "in each source of the harmful frame, the first 50 prompts in the order of the SHA-256 of their "
                    "identifiers (src/plan_v23.crossed_prompts)",
            "per_source": {s: len(v) for s, v in sorted(by_source.items())},
            "prompts": ids,
            "prompts_sha256": hashlib.sha256(json.dumps(ids).encode("utf-8")).hexdigest(),
            "judges": "the ten local judges of the primary panel (models 4, 5, 6 and 15 to 21)"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    rec = build()
    print(f"crossed subset: {len(rec['prompts'])} prompts {rec['per_source']}; list SHA-256 {rec['prompts_sha256']}")
    if "--write" in argv:
        OUT.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(f"written: {OUT.relative_to(ROOT).as_posix()}")
        return 0
    if OUT.exists():
        stored = json.loads(OUT.read_text(encoding="utf-8"))
        same = stored.get("prompts") == rec["prompts"] and stored.get("prompts_sha256") == rec["prompts_sha256"]
        print("stored record: " + ("the same" if same else "DIFFERENT from the rule"))
        return 0 if same else 1
    print("no stored record (run with --write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
