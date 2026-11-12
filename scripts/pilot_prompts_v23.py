"""Pilot prompts of protocol v2.3 (Section 13.2), written to config/pilot_prompts_v23.json.

Tail prompts in frame order, without every prompt of the retired sample G1 and of the version-1 pilot. The two
exclusion sets come from private files (results/raw/gold/key.csv and results/raw/responses_pilot_local.jsonl).
Only prompt identifiers are read from them, and this script prints counts only: no prompt text, no answer text
and no row of the key. The output holds the identifiers of the pilot prompts and the SHA-256 of the two private
files, so that whoever holds those files can reproduce the list.

Usage: python -I scripts/pilot_prompts_v23.py            print the counts and compare with the stored file
       python -I scripts/pilot_prompts_v23.py --write    write config/pilot_prompts_v23.json
"""
import collections
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import frames_v23  # noqa: E402

KEY = ROOT / "results" / "raw" / "gold" / "key.csv"
V1_PILOT = ROOT / "results" / "raw" / "responses_pilot_local.jsonl"
OUT = ROOT / "config" / "pilot_prompts_v23.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def excluded(index):
    """(prompt ids to keep out of the pilot, aggregate description). Reads identifiers only."""
    with V1_PILOT.open(encoding="utf-8") as f:
        v1 = {json.loads(line)["prompt_id"] for line in f if line.strip()}
    by_length = sorted(index, key=len, reverse=True)
    g1 = set()
    with KEY.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            hit = next((p for p in by_length if p in row["response_id"]), None)
            if hit is None:
                raise SystemExit("an item of the G1 key does not resolve to a sampled prompt")
            g1.add(hit)
    info = {"g1_key_sha256": sha(KEY), "g1_prompts": len(g1), "v1_pilot_sha256": sha(V1_PILOT),
            "v1_pilot_prompts": len(v1), "excluded_prompts": len(g1 | v1)}
    return g1 | v1, info


def build():
    index = frames_v23.sample_index()
    out, info = excluded(index)
    rounds = frames_v23.pilot_rounds(index, out)
    return {"_readme": "Pilot prompts of protocol v2.3 (Section 13.2), by round: identifiers of the harmful and "
                       "the safe prompts that the local models answer, and 'api', the subset that the API models "
                       "answer. Written by scripts/pilot_prompts_v23.py; never edited by hand. No pilot prompt is "
                       "inside a frame, in the retired sample G1 or in the version-1 pilot "
                       "(tests/test_frames_v23.py).",
            "sample_sha256": sha(frames_v23.SAMPLE), "excluded": info, "rounds": rounds}, index


def main():
    doc, index = build()
    print("excluded:", {k: v for k, v in doc["excluded"].items() if not k.endswith("sha256")})
    for i, rnd in enumerate(doc["rounds"], 1):
        for part in ("harmful", "safe", "api"):
            by_source = collections.Counter(index[p][0] for p in rnd[part])
            print(f"round {i} {part}: {len(rnd[part])} {dict(sorted(by_source.items()))}")
    text = json.dumps(doc, indent=1) + "\n"
    if "--write" in sys.argv:
        OUT.write_text(text, encoding="utf-8", newline="")
        print("written", OUT.relative_to(ROOT), "sha256", hashlib.sha256(text.encode("utf-8")).hexdigest())
    elif OUT.exists():
        print("stored file is", "identical" if OUT.read_text(encoding="utf-8") == text else "DIFFERENT")
    else:
        print("no stored file; use --write")


if __name__ == "__main__":
    main()
