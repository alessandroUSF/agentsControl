"""Check the files listed in docs/SEALED_HASHES.md against their recorded SHA-256.

Reads bytes only, to hash them. Prints one line per file (ok, MISMATCH or missing) and, with --unlisted, the
files under results/raw and results/logs that the record does not list, with their size and hash. No content of
any file is printed.

Usage: python -I scripts/check_sealed_hashes.py              check the recorded files
       python -I scripts/check_sealed_hashes.py --unlisted   also list files that are not recorded
Exit code 1 if a recorded file is missing or has another hash.
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "docs" / "SEALED_HASHES.md"
ROW = re.compile(r"^\|\s*`?([^|`]+?)`?\s*\|\s*`?([0-9a-f]{64})`?\s*\|")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def recorded():
    out = {}
    for line in RECORD.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            out[m.group(1).strip().replace("\\", "/")] = m.group(2)
    return out


def main():
    rec = recorded()
    if not rec:
        sys.exit("no row of docs/SEALED_HASHES.md could be read; check the table format")
    bad = 0
    for rel, want in rec.items():
        p = ROOT / rel
        if not p.exists():
            print(f"missing   {rel}")
            bad += 1
        elif sha256(p) != want:
            print(f"MISMATCH  {rel}")
            bad += 1
        else:
            print(f"ok        {rel}")
    print(f"{len(rec)} recorded files, {bad} problem(s)")
    if "--unlisted" in sys.argv:
        for base in ("results/raw", "results/logs"):
            for p in sorted((ROOT / base).rglob("*")):
                rel = p.relative_to(ROOT).as_posix()
                if p.is_file() and rel not in rec:
                    print(f"unlisted  {rel} | {p.stat().st_size} bytes | {sha256(p)}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
