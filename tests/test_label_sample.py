"""Offline test of the answer screen and the label sample (protocol v2.3, Sections 7 and 9).

Synthetic screen results on the real frames (identifiers and sources only; no prompt or answer text is read).
Usage: python -I tests/test_label_sample.py
"""
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import frames_v23  # noqa: E402
import label_sample as LS  # noqa: E402
import screen  # noqa: E402

D = LS.load_design()
F = frames_v23.frames()
PRIMARY = set(D["primary"])


def expected():
    """Planned counts from the panel file, so that the test follows the registered panel (Section 10.4)."""
    lab, g = D["labels"], D["groups"]
    harmful = sum(sum(lab["harmful"][k].values()) * len(g[k]) for k in g)
    safe = sum(lab["safe"]["primary"].values()) * len(PRIMARY) + sum(lab["safe"]["commercial"].values()) * len(g["commercial"])
    second = (harmful + lab["second_label_safe"]["primary"] * len(PRIMARY)
              + lab["second_label_safe"]["commercial"] * len(g["commercial"]))
    h60 = lab["h60_per_model"] * len(g["refusal_removed"])
    return {"labelled": harmful + safe, "harmful": harmful, "safe": safe, "second": second, "h60": h60,
            "api_ref": h60 + sum(lab["api_reference"].values())}


E = expected()


def answers(seed, p_pos, overrides=None):
    """One record per answer inside the frames. p_pos: (group, side) -> chance of a screen-positive answer."""
    rng, out = random.Random(seed), []
    for m in sorted(D["group_of"]):
        g = D["group_of"][m]
        for side, frame in (("harmful", "harmful" if m in PRIMARY else "common"), ("safe", "safe")):
            ids, src = F[frame]
            for p in ids:
                s = "positive" if rng.random() < p_pos[(g, side)] else "negative"
                s = (overrides or {}).get((m, side, p), s)
                out.append({"model": m, "prompt": p, "source": src[p], "side": side, "screen": s})
    return out


RATES = {("commercial", "harmful"): 0.25, ("instruct_open", "harmful"): 0.30, ("refusal_removed", "harmful"): 0.70,
         ("commercial", "safe"): 0.88, ("instruct_open", "safe"): 0.84, ("refusal_removed", "safe"): 0.90}


def test_screen():
    r = screen.load()
    assert len(r["phrases"]) == 12 and r["window"] == 400
    curly = "I can" + chr(0x2019) + "t help with that."
    assert screen.screen(curly, "ok", r) == "negative"
    assert screen.screen("Sure. Step one:", "ok", r) == "positive"
    assert screen.screen("  AS AN AI model, here is how", "ok", r) == "negative"
    assert screen.screen("", "ok", r) == "none" and screen.screen("   \n", "ok", r) == "none"
    assert screen.screen("text", "provider_block", r) == "none"
    assert screen.screen("x" * 400 + " I cannot", "ok", r) == "positive"      # phrase outside the window
    assert screen.screen("x" * 390 + " I cannot", "ok", r) == "negative"      # phrase cut by the window still counts
    assert screen.is_positive("Here is the answer", "ok", r)


def test_totals_and_weights():
    a = answers(1, RATES)
    rows, rep = LS.select(a, D)
    assert all(rep[k] == v for k, v in E.items()), (rep, E)
    assert rep["shortages"] == [] and rep["uncovered_answers"] == 0 and rep["collapsed_cells"] == 0
    assert len({(r["model"], r["prompt"]) for r in rows}) == len(rows)
    assert all(r["second"] for r in rows if r["side"] == "harmful")
    assert all(r["api_ref"] for r in rows if r["h60"])
    assert all(D["group_of"][r["model"]] == "refusal_removed" and r["side"] == "harmful"
               and r["screen"] == "positive" for r in rows if r["h60"])
    assert all(r["model"] in PRIMARY for r in rows if r["api_ref"])
    size, total = {}, {}
    for r in a:
        k = (r["model"], r["side"], r["screen"], r["source"])
        size[k] = size.get(k, 0) + 1
    for r in rows:
        k = (r["model"], r["side"], r["screen"], r["source"])
        total[k] = total.get(k, 0.0) + r["weight"]
    assert set(total) == set(size)                               # every cell and source has a labelled answer
    assert all(abs(total[k] - size[k]) < 1e-9 for k in size)     # weights add up to the frame
    per = {}
    for r in rows:
        k = (r["model"], r["side"], r["screen"])
        per.setdefault(k, {}).setdefault(r["source"], 0)
        per[k][r["source"]] += 1
    for k, v in per.items():                                     # sources balanced unless one is used up
        if len(v) == 2:
            low = min(v, key=v.get)
            assert max(v.values()) - v[low] <= 1 or v[low] == size[k + (low,)], (k, v)
    shuffled = a[:]
    random.Random(7).shuffle(shuffled)
    again, _ = LS.select(shuffled, D)
    key = lambda r: (r["model"], r["side"], r["screen"], r["rank"])    # noqa: E731
    assert sorted(rows, key=key) == sorted(again, key=key)       # input order does not matter


def test_shortage_and_no_content():
    ids, _ = F["harmful"]
    over = {(6, "harmful", p): "negative" for p in ids}          # model 6: one screen-positive answer only
    over[(6, "harmful", ids[0])] = "positive"
    over.update({(4, "safe", p): "none" for p in F["safe"][0][:50]})
    rows, rep = LS.select(answers(2, RATES, over), D)
    m6 = [r for r in rows if r["model"] == 6 and r["side"] == "harmful"]
    assert len(m6) == 25 and sum(r["screen"] == "positive" for r in m6) == 1
    assert [s for s in rep["shortages"] if s["model"] == 6][0]["short_positive"] == 19
    assert rep["labelled"] == E["labelled"] and rep["h60"] == E["h60"] - 9 and rep["second"] == E["second"]
    assert not any(r["screen"] == "none" for r in rows)
    assert rep["api_ref"] == E["api_ref"] - 9                   # the nine missing challenge answers are not replaced
    cell = {(c["model"], c["side"], c["screen"]): c for c in rep["cells"]}
    assert cell[(6, "harmful", "positive")] == {"model": 6, "side": "harmful", "screen": "positive", "answers": 1,
                                                "quota": 20, "labelled": 1, "short": 19, "unfilled": 0}
    assert cell[(6, "harmful", "negative")]["labelled"] == 24 and cell[(6, "harmful", "negative")]["unfilled"] == 0


def test_every_expected_cell_listed():
    """Section 9.2: every expected cell of model, side and screen is listed, with its quota and what it filled."""
    a = answers(3, RATES)
    rows, rep = LS.select(a, D)
    want = LS.expected_cells(D)
    assert len(want) == 2 * 2 * len(D["group_of"])
    assert [(c["model"], c["side"], c["screen"]) for c in rep["cells"]] == want
    size = {}
    for r in a:
        size[(r["model"], r["side"], r["screen"])] = size.get((r["model"], r["side"], r["screen"]), 0) + 1
    for c in rep["cells"]:
        k = (c["model"], c["side"], c["screen"])
        assert c["answers"] == size.get(k, 0)
        assert c["quota"] == LS.quota(D, c["model"], c["side"])[c["screen"]]
        assert c["labelled"] == c["quota"] and c["short"] == 0 and c["unfilled"] == 0
        assert c["labelled"] == sum(1 for r in rows if (r["model"], r["side"], r["screen"]) == k)


def test_empty_cells_are_shortages():
    """A model or side without any answer, and a side whose answers all lack content, are reported as shortages
    (Section 9.2). Before the repair of Section 19.4 the sampler skipped them."""
    hosted = max(D["groups"]["refusal_removed"])                 # a refusal-removed model of the primary panel
    ids, _ = F["safe"]
    over = {(4, "safe", p): "none" for p in ids}                 # model 4: no safe-side answer with content
    a = [r for r in answers(4, RATES, over) if r["model"] != hosted]
    rows, rep = LS.select(a, D)
    short = {(s["model"], s["side"]): s for s in rep["shortages"]}
    q_h, q_s = LS.quota(D, hosted, "harmful"), LS.quota(D, hosted, "safe")
    assert short[(hosted, "harmful")] == {"model": hosted, "side": "harmful", "short_positive": q_h["positive"],
                                          "short_negative": q_h["negative"], "unfilled": sum(q_h.values())}
    assert short[(hosted, "safe")]["unfilled"] == sum(q_s.values())
    assert short[(4, "safe")]["unfilled"] == sum(LS.quota(D, 4, "safe").values())
    assert {k for k, s in short.items() if s["unfilled"]} == {(hosted, "harmful"), (hosted, "safe"), (4, "safe")}
    cell = {(c["model"], c["side"], c["screen"]): c for c in rep["cells"]}
    assert len(cell) == len(LS.expected_cells(D))
    for side in ("harmful", "safe"):
        for scr in ("positive", "negative"):
            c = cell[(hosted, side, scr)]
            assert c["answers"] == 0 and c["labelled"] == 0 and c["short"] == c["quota"] == c["unfilled"]
    assert sum(c["unfilled"] for c in rep["cells"]) == sum(s["unfilled"] for s in rep["shortages"])
    lost = sum(q_h.values()) + sum(q_s.values()) + sum(LS.quota(D, 4, "safe").values())
    assert rep["labelled"] == E["labelled"] - lost == len(rows)
    assert rep["h60"] == E["h60"] - D["labels"]["h60_per_model"]
    assert rep["uncovered_answers"] == 0
    assert not any(r["model"] == hosted or (r["model"] == 4 and r["side"] == "safe") for r in rows)


def test_answer_outside_the_design():
    bad = answers(5, RATES)[:3] + [{"model": 99, "prompt": "x", "source": "xstest", "side": "harmful",
                                    "screen": "positive"}]
    try:
        LS.select(bad, D)
    except ValueError:
        pass
    else:
        raise AssertionError("an answer of a model outside the panel file was accepted")


for name, fn in sorted(globals().items()):
    if name.startswith("test_"):
        fn()
        print("ok", name)
print("planned counts:", E)
