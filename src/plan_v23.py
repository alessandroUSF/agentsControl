"""Call plans of protocol v2.3 (Sections 5, 6, 9.4, 11.4 to 11.6, 12 and 13.2): who answers which prompt, and which
answer each judge classifies, in which block, arm, presentation and pair.

Respondents (src/run_models.py):
  block 1  pilot round r: local models answer the round's 100 prompts, API models its 20 'api' prompts
  block 2  primary panel: harmful frame (300) and safe frame (90); only answers that do not exist are generated
  block 4  commercial panel: common set (60) and safe frame (90)

Judges (src/run_judges_v23.py). Parts carry the names of the holds file (config/stage_holds.json):
  block 1  pilot_r<r>      local judges: own round answers, both presentations (200 calls); API judges: own 20
                           answers and 10 screen-positive answers of local refusal-removed models to the round's
                           harmful prompts, both presentations (60 calls)
  block 3  own_harmful, control_harmful     primary panel on the harmful frame (registered assignment)
  block 5  own_safe, control_safe           primary panel on the safe frame
           label_blind                      every labelled answer, blind, unless the judge already gives that blind
                                            verdict as author or control (Section 12.1)
           challenge_context                the challenge set, in context, unless the judge already gives that
                                            in-context verdict as author or control
           repeat                           both presentations of 10 own answers to harmful prompts, drawn by seed
           control_local                    local refusal-removed judges: answers whose control in the block
                                            'refusal_removed_local' differs from the registered one (Section 6.5)
  block 6  own, control_harmful             commercial judges; then reference_h1, reference_h2 (blind); then
           control_safe, repeat
  block 7  challenge_blind, challenge_context   commercial judges: both presentations of each challenge answer as
                                            one pair in hash order; cut 3 removes the in-context half only
Arms: A (author), C (control), L (label sample, blind), X (challenge set), R (reference subset), P (repeat),
Q (pilot control), K (local control). A pair is the two presentations of one answer by one judge.

Answers without content are never sent to a judge (Section 10.1); they are listed in Plan.skipped as 'no_content'
so that the counts stay complete. Answers that do not exist are listed as 'missing'.

Standard library only.
"""
import hashlib
import json
from pathlib import Path

import judge_v23 as J

ROOT = Path(__file__).resolve().parents[1]
ASSIGNMENT = ROOT / "analysis" / "output" / "control_assignment_v23.json"
PILOT = ROOT / "config" / "pilot_prompts_v23.json"
SEED = 20261108


def _h(*parts):
    return hashlib.sha256("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def aid(model_key, prompt_id):
    return f"{model_key}|{prompt_id}"


# ---- configuration ---------------------------------------------------------------------------------------------------

class Panel:
    """Numbers, keys and groups of the 23 models; the registered hosted models (decision D13)."""

    def __init__(self, models, design, registered_hosted=None):
        self.models = models
        self.by_key = {m["key"]: m for m in models}
        self.key_of = {m["n"]: m["key"] for m in models}
        self.n_of = {m["key"]: m["n"] for m in models}
        self.groups = {g: [int(x) for x in v] for g, v in design["groups"].items()}
        hosted_all = [int(x) for x in design["hosted_primary"]]
        self.hosted_all = hosted_all
        self.hosted = hosted_all if registered_hosted is None else [n for n in hosted_all if n in registered_hosted]
        left_out = set(hosted_all) - set(self.hosted)
        self.left_out = sorted(left_out)
        self.primary = [int(n) for n in design["primary_panel"] if int(n) not in left_out]
        self.instruct = self.groups["instruct_open"]
        self.removed = [n for n in self.groups["refusal_removed"] if n not in left_out]
        self.removed_local = [n for n in self.removed if n not in hosted_all]
        self.commercial = self.groups["commercial"]
        self.local = [m["n"] for m in models if m["provider"] == "ollama"]
        self.removed_block = ("refusal_removed" if not left_out else
                              "refusal_removed_local" if not self.hosted else
                              "refusal_removed_without_" + "_".join(str(x) for x in sorted(left_out)))

    def keys(self, numbers):
        return [self.key_of[n] for n in numbers]


def load_assignment(path=ASSIGNMENT):
    """{(block name, frame): {prompt_id: {author number: control number}}}, after checking the recorded digest."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    canon = json.dumps([[b["group"], b["frame"], b["assignment"]] for b in d["blocks"]], sort_keys=True,
                       separators=(",", ":"))
    if hashlib.sha256(canon.encode("utf-8")).hexdigest() != d["assignment_sha256"]:
        raise ValueError("control assignment: digest does not match its blocks")
    out = {}
    for b in d["blocks"]:
        out[(b["group"], b["frame"])] = {p: {int(a): int(k) for a, k in m.items()} for p, m in b["assignment"].items()}
    return out, d["assignment_sha256"]


def load_pilot(path=PILOT):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---- respondents -------------------------------------------------------------------------------------------------------

def respondent_plan(block, panel, frames, pilot=None, rnd=None):
    """{model_key: [prompt ids]} for a respondent block."""
    block = str(block)
    if block == "1":
        r = pilot["rounds"][int(rnd) - 1]
        out = {}
        for m in panel.models:
            if m["n"] in panel.local:
                out[m["key"]] = list(r["harmful"]) + list(r["safe"])
            elif m["n"] in panel.hosted or m["n"] in panel.commercial:
                out[m["key"]] = list(r["api"])
        return out
    if block == "2":
        ids = list(frames["harmful"][0]) + list(frames["safe"][0])
        return {panel.key_of[n]: ids for n in panel.primary}
    if block == "4":
        ids = list(frames["common"][0]) + list(frames["safe"][0])
        return {panel.key_of[n]: ids for n in panel.commercial}
    raise ValueError(f"block {block} has no respondent calls")


# ---- judges -------------------------------------------------------------------------------------------------------------

D2_PARTS = ("challenge_blind", "challenge_context", "reference_h1", "reference_h2")


def d2_excluded(part, side):
    """True for a judging call that a judge under decision D2 (safe prompts only) never makes: every call on a
    harmful-side answer, and the challenge set and the reference subset on either side (Section 19.1: "no control
    verdicts on harmful prompts, no challenge set, no reference subset"). The runner does not send these calls; its
    close and the analysis count them as excluded under D2."""
    return side == "harmful" or part in D2_PARTS


def _pair(block, part, judge, answer, arm, seed, presentations=("blind", "context")):
    """The calls of one pair (or one single call), in the order fixed by the hash (Section 11.4)."""
    order = list(presentations)
    if len(order) == 2 and order[0] != J.first_presentation(judge, answer["answer_id"], seed):
        order.reverse()
    pair = _h(seed, "pairid", block, part, judge, answer["answer_id"])[:16] if len(order) == 2 else None
    return [{"block": str(block), "part": part, "judge": judge, "answer_id": answer["answer_id"],
             "author": answer["model_key"], "prompt_id": answer["prompt_id"], "side": answer["side"], "arm": arm,
             "presentation": p, "pair": pair, "position": i, "seq": J.sequence_key(judge, answer["answer_id"], part, seed)}
            for i, p in enumerate(order)]


class Plan:
    """The judging plan of one block. answers: {answer_id: row} of src/answers_v23 (main-run table, or the pilot
    table for block 1). labels: rows of the label sample file (blocks 5 to 7). pilot: config/pilot_prompts_v23.json."""

    def __init__(self, panel, frames, assignment, answers, labels=None, pilot=None, seed=SEED, repeat_n=10,
                 pilot_controls=10):
        self.p, self.frames, self.asg, self.answers = panel, frames, assignment, answers
        self.labels, self.pilot = labels or [], pilot
        self.seed, self.repeat_n, self.pilot_controls = seed, repeat_n, pilot_controls
        self.skipped = []

    # helpers ----------------------------------------------------------------------------------------------------------
    def side_of(self, prompt_id):
        """'harmful' or 'safe': the side of a prompt of the frames; None when it is in none of them."""
        for name, side in (("harmful", "harmful"), ("common", "harmful"), ("harmful_tail", "harmful"),
                           ("safe", "safe"), ("safe_commercial_controls", "safe"), ("safe_tail", "safe")):
            f = self.frames.get(name)
            if f is not None and prompt_id in f[1]:
                return side
        return None

    def answer(self, model_n, prompt_id, why):
        a = self.answers.get(aid(self.p.key_of[model_n], prompt_id))
        if a is None:
            self.skipped.append({"answer_id": aid(self.p.key_of[model_n], prompt_id), "why": why, "state": "missing",
                                 "author": self.p.key_of[model_n], "side": self.side_of(prompt_id)})
            return None
        if not a["has_content"]:
            self.skipped.append({"answer_id": a["answer_id"], "why": why, "state": "no_content"})
            return None
        return a

    def group_of(self, n):
        if n in self.p.instruct:
            return "instruct_open"
        if n in self.p.removed:
            return self.p.removed_block
        if n in self.p.commercial:
            return "commercial"
        raise ValueError(n)

    def controls(self, judge_n, frame, block_name=None):
        """(author number, prompt id) of the answers that this judge controls on a frame."""
        table = self.asg[(block_name or self.group_of(judge_n), frame)]
        return [(a, p) for p in self.frames[frame][0] for a, k in sorted(table[p].items()) if k == judge_n]

    def control_of(self, author_n, prompt_id, frame):
        return self.asg[(self.group_of(author_n), frame)][prompt_id].get(author_n)

    def own(self, judge_n, frame):
        return [(judge_n, p) for p in self.frames[frame][0]]

    def repeat_answers(self, judge_n, frame):
        """Section 11.6: 10 own answers to harmful prompts, drawn by seed (answers with content only)."""
        cands = [a for a in (self.answers.get(aid(self.p.key_of[judge_n], p)) for p in self.frames[frame][0])
                 if a is not None and a["has_content"]]
        cands.sort(key=lambda a: _h(self.seed, "repeat", a["answer_id"]))
        return cands[: self.repeat_n]

    def _judges(self, judges, numbers):
        if judges is None:
            return list(numbers)
        want = {self.p.n_of[k] for k in judges}
        return [n for n in numbers if n in want]

    def _pairs(self, block, jn, part, arm, pairs, presentations=("blind", "context")):
        key, out = self.p.key_of[jn], []
        for author_n, pid in pairs:
            a = self.answer(author_n, pid, f"{part} of {key}")
            if a is not None:
                out += _pair(block, part, key, a, arm, self.seed, presentations)
        return out

    # blocks -------------------------------------------------------------------------------------------------------------
    def calls(self, block, judges=None, rnd=None):
        """The planned calls of a block for the given judges (keys; default every judge of the block), in the order
        in which they are sent."""
        block = str(block)
        out = []
        if block == "1":
            for jn in self._judges(judges, self.p.local + self.p.hosted + self.p.commercial):
                out += self._pilot(jn, rnd)
        elif block == "3":
            for jn in self._judges(judges, self.p.primary):
                out += self._pairs("3", jn, "own_harmful", "A", self.own(jn, "harmful"))
                out += self._pairs("3", jn, "control_harmful", "C", self.controls(jn, "harmful"))
        elif block == "5":
            for jn in self._judges(judges, self.p.primary):
                key = self.p.key_of[jn]
                out += self._pairs("5", jn, "own_safe", "A", self.own(jn, "safe"))
                out += self._pairs("5", jn, "control_safe", "C", self.controls(jn, "safe"))
                out += self._label_blind(jn)
                out += self._challenge_context(jn)
                for a in self.repeat_answers(jn, "harmful"):
                    out += _pair("5", "repeat", key, a, "P", self.seed)
                if jn in self.p.removed_local and self.p.removed_block != "refusal_removed_local":
                    out += self._pairs("5", jn, "control_local", "K", self._local_controls(jn))
        elif block == "6":
            for jn in self._judges(judges, self.p.commercial):
                key = self.p.key_of[jn]
                out += self._pairs("6", jn, "own", "A", self.own(jn, "common") + self.own(jn, "safe"))
                out += self._pairs("6", jn, "control_harmful", "C", self.controls(jn, "common"))
                out += self._reference(jn)
                out += self._pairs("6", jn, "control_safe", "C", self.controls(jn, "safe_commercial_controls"))
                for a in self.repeat_answers(jn, "common"):
                    out += _pair("6", "repeat", key, a, "P", self.seed)
        elif block == "7":
            for jn in self._judges(judges, self.p.commercial):
                key = self.p.key_of[jn]
                for r in self._challenge_rows():
                    a = self.answers.get(r["answer_id"])
                    if a is None or not a["has_content"]:
                        continue
                    for c in _pair("7", "challenge", key, a, "X", self.seed):
                        c["part"] = "challenge_blind" if c["presentation"] == "blind" else "challenge_context"
                        out.append(c)
        else:
            raise ValueError(f"block {block} has no judging calls")
        return order_calls(out, block, self.p)

    def _challenge_rows(self):
        return [r for r in self.labels if r.get("h60")]

    def _already(self, jn, a):
        """True when judge jn classifies this answer anyway, as its author or as its registered control (both
        presentations are then made in the own and control parts)."""
        author = self.p.n_of[a["model_key"]]
        if author == jn:
            return True
        if author in self.p.primary and a["side"] in ("harmful", "safe") and a["prompt_id"] in self.frames[a["side"]][1]:
            return self.control_of(author, a["prompt_id"], a["side"]) == jn
        return False

    def _label_blind(self, jn):
        key, out = self.p.key_of[jn], []
        for r in self.labels:
            a = self.answers.get(r["answer_id"])
            if a is None or not a["has_content"] or self._already(jn, a):
                continue
            out += _pair("5", "label_blind", key, a, "L", self.seed, presentations=("blind",))
        return out

    def _challenge_context(self, jn):
        key, out = self.p.key_of[jn], []
        for r in self._challenge_rows():
            a = self.answers.get(r["answer_id"])
            if a is None or not a["has_content"] or self._already(jn, a):
                continue
            out += _pair("5", "challenge_context", key, a, "X", self.seed, presentations=("context",))
        return out

    def reference_halves(self):
        """Section 9.4: the other answers of the reference subset in SHA-256 order of their identifiers; the first
        half (30 of 60) is reference_h1, the rest reference_h2 (cut 4)."""
        other = [r for r in self.labels if r.get("api_ref") and not r.get("h60")]
        other.sort(key=lambda r: hashlib.sha256(r["answer_id"].encode("utf-8")).hexdigest())
        half = len(other) - len(other) // 2
        return other[:half], other[half:]

    def _reference(self, jn):
        key, out = self.p.key_of[jn], []
        for part, rows in zip(("reference_h1", "reference_h2"), self.reference_halves()):
            for r in rows:
                a = self.answers.get(r["answer_id"])
                if a is not None and a["has_content"]:
                    out += _pair("6", part, key, a, "R", self.seed, presentations=("blind",))
        return out

    def _local_controls(self, jn):
        """Answers of local refusal-removed authors that judge jn controls in 'refusal_removed_local' and whose
        registered control is another judge, on both frames (Section 6.5)."""
        out = []
        for frame in ("harmful", "safe"):
            loc = self.asg[("refusal_removed_local", frame)]
            reg = self.asg[(self.p.removed_block, frame)]
            for p in self.frames[frame][0]:
                for a, k in sorted(loc[p].items()):
                    if k == jn and reg[p].get(a) != jn:
                        out.append((a, p))
        return out

    def _pilot(self, jn, rnd):
        """Section 13.2: own answers to the round's prompts (local judges: all 100; API judges: the 20 'api'
        prompts), both presentations; API judges also 10 screen-positive answers of local refusal-removed models."""
        r = self.pilot["rounds"][int(rnd) - 1]
        part = f"pilot_r{int(rnd)}"
        ids = list(r["harmful"]) + list(r["safe"]) if jn in self.p.local else list(r["api"])
        out = self._pairs("1", jn, part, "A", [(jn, p) for p in ids])
        if jn not in self.p.local:
            key = self.p.key_of[jn]
            for a in self.pilot_control_answers(rnd):
                out += _pair("1", part, key, a, "Q", self.seed)
        return out

    def pilot_control_answers(self, rnd):
        """10 screen-positive answers of local refusal-removed models to the round's harmful prompts: the models in
        turn, each model's answers in hash order; the same answers for every API judge."""
        harmful = set(self.pilot["rounds"][int(rnd) - 1]["harmful"])
        pools = {}
        for a in self.answers.values():
            n = self.p.n_of.get(a["model_key"])
            if (n in self.p.removed_local and a["prompt_id"] in harmful and a["screen"] == "positive"
                    and a["has_content"]):
                pools.setdefault(n, []).append(a)
        for n in pools:
            pools[n].sort(key=lambda a: _h(self.seed, "pilot_control", rnd, a["answer_id"]))
        out, i, order = [], 0, sorted(pools)
        while len(out) < self.pilot_controls and any(pools[n] for n in order):
            n = order[i % len(order)]
            if pools[n]:
                out.append(pools[n].pop(0))
            i += 1
        return out


# Order inside a block (Sections 11.4 and 12.3): judges one after the other, hosted judges first; inside a judge,
# the stages of Section 12.3 in turn, pairs shuffled by seed, and the two calls of a pair next to each other.
STAGES = {"5": {"own_safe": 0, "control_safe": 0, "label_blind": 1, "challenge_context": 1, "repeat": 2,
                "control_local": 3},
          "6": {"own": 0, "control_harmful": 0, "reference_h1": 1, "reference_h2": 1, "control_safe": 2, "repeat": 2}}


def order_calls(calls, block, panel):
    hosted = set(panel.keys(panel.hosted))
    stage = STAGES.get(str(block), {})
    calls.sort(key=lambda c: (0 if c["judge"] in hosted else 1, c["judge"], stage.get(c["part"], 0), c["seq"],
                              c["position"]))
    return calls


def counts(calls):
    """{(judge, part): number of calls}."""
    out = {}
    for c in calls:
        out[(c["judge"], c["part"])] = out.get((c["judge"], c["part"]), 0) + 1
    return out
