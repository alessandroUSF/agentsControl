"""Offline test of the prompt frames and the pilot prompts (protocol v2.3, Sections 5 and 13.2).

Reads identifiers and strata only: no prompt text, no answer text, no row of the gold key is printed.
The exclusion check of the pilot needs two private files (results/raw/...). Without them that one check is
skipped and says so; every other check runs on public files.
Usage: python -I tests/test_frames_v23.py
"""
import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import frames_v23 as FR  # noqa: E402
import pilot_prompts_v23 as PP  # noqa: E402

SEALED_SAMPLE = "e7cf1bab3f594f0c74a8dc3b783b1938aae7cf50841b905bc0020dda57d59983"
INDEX = FR.sample_index()
F = FR.frames(INDEX)
N = FR.sizes()
PLAN = FR.pilot_plan()
STORED = json.loads(PP.OUT.read_text(encoding="utf-8"))


def by_source(ids, src):
    return dict(sorted(collections.Counter(src[p] for p in ids).items()))


def test_sample_is_the_sealed_file():
    assert hashlib.sha256(FR.SAMPLE.read_bytes()).hexdigest() == SEALED_SAMPLE
    assert STORED["sample_sha256"] == SEALED_SAMPLE
    assert len(INDEX) == 1050


def test_sizes():
    want = {"common": {"or-bench-toxic": 30, "xstest": 30},
            "harmful": {"or-bench-toxic": 150, "xstest": 150},
            "harmful_tail": {"or-bench-toxic": 150, "xstest": 50},
            "safe": {"or-bench-hard": 45, "xstest": 45},
            "safe_commercial_controls": {"or-bench-hard": 15, "xstest": 15},
            "safe_tail": {"or-bench-hard": 255, "xstest": 205}}
    for name, (ids, src) in F.items():
        assert by_source(ids, src) == want[name], (name, by_source(ids, src))
        assert len(ids) == len(set(ids))
    assert N == {"common_per_source": 30, "harmful_per_source": 150, "safe_per_source": 45,
                 "commercial_safe_control_per_source": 15}
    # answers inside the frames: primary 11 x (300 + 90), commercial 11 x (60 + 90)
    assert 11 * (len(F["harmful"][0]) + len(F["safe"][0])) == 4290
    assert 11 * (len(F["common"][0]) + len(F["safe"][0])) == 1650


def test_nesting_and_partition():
    harmful, safe = F["harmful"][0], F["safe"][0]
    assert harmful[:len(F["common"][0])] == F["common"][0]            # a smaller frame is a prefix
    assert safe[:len(F["safe_commercial_controls"][0])] == F["safe_commercial_controls"][0]
    all_harmful = {p for p, (_, e, _) in INDEX.items() if e == FR.HARMFUL}
    all_safe = {p for p, (_, e, _) in INDEX.items() if e == FR.SAFE}
    assert set(harmful) | set(F["harmful_tail"][0]) == all_harmful and len(all_harmful) == 500
    assert set(safe) | set(F["safe_tail"][0]) == all_safe and len(all_safe) == 550
    assert not set(harmful) & set(F["harmful_tail"][0]) and not set(safe) & set(F["safe_tail"][0])
    for name, (ids, _) in F.items():                                  # frame order is (rank, source)
        assert ids == sorted(ids, key=lambda p: (INDEX[p][2], INDEX[p][0])), name


def test_order_is_reproducible():
    again = FR.frames(FR.sample_index())
    assert {k: v[0] for k, v in again.items()} == {k: v[0] for k, v in F.items()}


def test_pilot_rounds_are_outside_the_frames():
    inside = set(F["harmful"][0]) | set(F["safe"][0])
    tails = {"harmful": set(F["harmful_tail"][0]), "safe": set(F["safe_tail"][0])}
    seen = set()
    assert len(STORED["rounds"]) == PLAN["rounds"] == 2
    for rnd in STORED["rounds"]:
        for side in ("harmful", "safe"):
            ids = rnd[side]
            assert set(ids) <= tails[side] and not set(ids) & inside
            assert by_source(ids, {p: INDEX[p][0] for p in ids}) == dict(sorted(PLAN[side].items())), side
            assert not seen & set(ids)                                # the rounds share no prompt
            seen |= set(ids)
        api = rnd["api"]
        assert set(api) <= set(rnd["harmful"]) | set(rnd["safe"]) and len(api) == len(set(api)) == 20
        sides = collections.Counter(INDEX[p][1] for p in api)
        assert sides == {FR.HARMFUL: 10, FR.SAFE: 10}
        for side in ("harmful", "safe"):                              # API prompts open each source's list
            for source in PLAN[side]:
                own = [p for p in rnd[side] if INDEX[p][0] == source]
                assert [p for p in api if p in own] == own[:PLAN["api_per_source"]]
    assert len(seen) == 200


def test_pilot_excludes_g1_and_the_version_1_pilot():
    if not (PP.KEY.exists() and PP.V1_PILOT.exists()):
        print("   skipped: the private files are not here; the stored exclusion hashes are",
              STORED["excluded"]["g1_key_sha256"][:12], STORED["excluded"]["v1_pilot_sha256"][:12])
        return
    out, info = PP.excluded(INDEX)
    assert info == STORED["excluded"]
    assert info["g1_prompts"] == 143 and info["v1_pilot_prompts"] == 50 and info["excluded_prompts"] == 185
    for rnd in STORED["rounds"]:
        assert not out & (set(rnd["harmful"]) | set(rnd["safe"]))
    doc, _ = PP.build()
    assert doc == STORED                                              # the stored file is what the code writes


def test_pilot_fails_loudly_when_prompts_run_out():
    tail = set(F["harmful_tail"][0])
    keep = {p for p in tail if INDEX[p][0] == "xstest"}
    blocked = set(sorted(keep)[:len(keep) - 20])                      # leaves 20 XSTest prompts; two rounds need 30
    try:
        FR.pilot_rounds(INDEX, blocked)
    except ValueError as e:
        assert "round 2" in str(e) and "xstest" in str(e)
    else:
        raise AssertionError("a shortage of pilot prompts must stop the selection")


for name, fn in sorted(globals().items()):
    if name.startswith("test_"):
        fn()
        print("ok", name)
