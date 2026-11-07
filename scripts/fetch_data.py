"""Download the public benchmarks at pinned revisions and verify their SHA-256 hashes.

Usage (from the project root):  python -I scripts/fetch_data.py
Files land in data/raw/<benchmark>/. Raw data is not committed to git (see .gitignore); this script reproduces it.
"""
import hashlib
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

# Pinned revisions (checked 2026-11-03)
XSTEST_REV = "d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d"   # github.com/paul-rottger/xstest, CC-BY-4.0
ORBENCH_REV = "e36d8b80e81837c8a8f264bbb2a49f1b32c7e272"  # huggingface.co/datasets/bench-llm/or-bench, CC-BY-4.0

FILES = [
    ("xstest/xstest_prompts.csv",
     f"https://raw.githubusercontent.com/paul-rottger/xstest/{XSTEST_REV}/xstest_prompts.csv",
     "11783fb294ed017473ee53c207d71f2161c7672c8d0b037501e78387f801cb5a"),
    ("xstest/LICENSE",
     f"https://raw.githubusercontent.com/paul-rottger/xstest/{XSTEST_REV}/LICENSE",
     "9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94"),
    ("or-bench/or-bench-hard-1k.csv",
     f"https://huggingface.co/datasets/bench-llm/or-bench/resolve/{ORBENCH_REV}/or-bench-hard-1k.csv",
     "a6e2f1166416efe5901f3bb05c47dc92ab3aca3acfe143693d38b8057d841e6d"),
    ("or-bench/or-bench-toxic.csv",
     f"https://huggingface.co/datasets/bench-llm/or-bench/resolve/{ORBENCH_REV}/or-bench-toxic.csv",
     "3be45901faae3b4b2b51bf7f8a2784c1650a1cc8c631dbc8b171d5312d4e0057"),
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for rel, url, expected in FILES:
        dest = RAW / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "agentsControl-research/0.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
        got = sha256(dest)
        status = "ok" if got == expected else "HASH MISMATCH"
        print(f"{status:13s} {rel} ({dest.stat().st_size} bytes)")
        if got != expected:
            raise SystemExit(f"Unexpected content for {rel}: {got}")


if __name__ == "__main__":
    main()
