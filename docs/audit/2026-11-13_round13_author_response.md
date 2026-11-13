# Corrections after review round 13 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round13_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a review of the corrections of round 12 and of run (k) made again).
- **Verdict of the report:** no critical or major point; the code is ready for the pilot registration apart from the PI's outstanding decisions and actions and one minor wording correction. The reviewer checked every row of run (k) against its calibration record, the figures of Sections 8.1, 17.1 and A.4 against the output, the 186 declared tests against the log, the hashes of the template and of the control assignment, and the fingerprint inputs of runs (a) to (g).
- **No paid call, no answer and no verdict** was made for this correction.

## Minor point

| Point of round 13 | Correction | Where |
|---|---|---|
| Read literally, the rule of the related cells left out of the crossed fit also excluded a judge's own answers, since the control rule treats a model as related to itself; the code builds pairs of distinct models only and keeps own cells | Both sentences now say: a cell whose judge and author are distinct models, related under the rule of Section 6.1, and not one of the three sibling pairs is left out; the cells of a judge on its own answers and those of the three sibling pairs stay in. The docstrings of `analysis/crossed_v23.py` say the same. No code or result changed; the crossed tests pass | `docs/STUDY_PROTOCOL_v2.3.md`, Section 8.8; `docs/REGISTRATION_v2.3.md`; `analysis/crossed_v23.py` (docstrings) |

## After this round

The change after round 13 is wording only. The code review rounds end here, unless a later change to the code calls for another round.
