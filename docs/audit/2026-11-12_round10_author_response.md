# Corrections after review round 10 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-12_reviewer_round10_codex_gpt61sol.md` (GPT-6.1 Sol, 12 November 2026, a review of the code written on 12 November 2026 after the first and second rounds of fresh readings).
- **Verdict of the report:** two major and four minor corrections, and the rendering check of the new layout still open.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data. The rendering check is local, with harmless sentinel texts.

## Major points

| Point of round 10 | Correction | Where |
|---|---|---|
| M1. When the own and sibling regressors are collinear once the effects are removed, the crossed estimator dropped the sibling term and reported the remaining coefficient as δ, which changes the model | The rank is checked on the full model of Section 8.8. When own and sibling are collinear after the judge and answer effects, both coefficients are reported as not identified, and so is everything that depends on them. The reviewer's reproduction is a regression test: it now gives "not identified". A second case, where own varies alone, gives δ and leaves σ not identified | `analysis/crossed_v23.py`, `_one_presentation`; `tests/test_crossed_v23.py`, `test_collinear_not_identified` |
| M2. Primary ingestion kept the `long_context` mark but never refused it, so an overridden verdict file could bring longer-context verdicts into the registered arrays; the sensitivity merge checked neither the mark nor the judge | The primary analysis refuses any canonical record marked `long_context` ("made with the longer context"). A replacement in the sensitivity analysis must carry the mark, come from a local judge, and match the judge, answer and presentation of the overflow it replaces; anything else is refused | `analysis/analyze_v23.py`, `analyse()` and `merged_long_context()`; `tests/test_sim_v23_analyze.py`, `test_long_context` (negative cases for a marked primary record, an unmarked replacement and a hosted judge) |

## Minor points

| Point of round 10 | Correction | Where |
|---|---|---|
| `within_sentence()` gave "could not be estimated" for every missing interval, an estimate with zero variance included | Three states, as Section 2.4 has them: "could not be estimated" (no estimate), "has no interval" (an estimate without an interval, with the estimate and the reason kept), and the sentence with the interval | `analysis/analyze_v23.py`, `within_sentence()`; `tests/test_sim_v23_analyze.py`, `test_within_sentence_states` |
| The delimiter-collision counts promised by Section 11.2 were missing | The pilot report counts the requests and answers that contain a closing delimiter (`</request>`, `</answer>`), by model, and prints no text. A section of the report gives the counts. Both delimiters are tested | `scripts/pilot_report_v23.py`, `delimiter_collisions()`; `tests/test_judges_v23.py`, `t_pilot_report` |
| The hash recorded in the stage holds seemed not to match the manifest, and the manifest's introduction still described caching | The mismatch was an artifact of the copy given to the reviewer: the build script of that copy reformatted the JSON files, which changed their bytes. The manifest and the holds of the repository match their recorded hashes; the build script now copies those files byte for byte. The introduction of the manifest says that neither presentation uses caching. Its output is unchanged | `scripts/manifest_v23.py` (docstring); the review copy's build script |
| The tests lacked the hosted-cap exemption assertions, the equality of the original messages in the long-context mode, and a midnight case with both dates and timestamps moved | `t_pilot_report` asserts that models 22 and 23 keep their cap under rule 3. `t_long_context_mode` asserts that the call with the longer context sends exactly the messages of the call that overflowed. `t_availability_midnight_rollover` moves the later record's time past midnight, runs the check on the next day, and requires the next day's record to be used and the earlier day's to be sent again | `tests/test_judges_v23.py`; `tests/test_runner_offline.py` |

## The rendering check of the new layout

Run on 12 November 2026, in the evening, on all eleven local judge builds (the Q4_0 and Q4_K_M builds of model 6, beside model 4, and the nine others), with the conditions of the system slot of Section 11.2: the supplied prompt of model 6 once and whole, the built-in prompt of models 20 and 21 once, and nothing else. All eleven pass every condition (`results/logs/render_check_v23_<build>.json`). Sections 11.7 and 14.2 record it.

## After this round

Section 14.2 gives the test count after these corrections. These corrections were not sent to a further review round of their own. The code written after them for the third round of fresh readings (decision D20, the disclaimer measure of decision D21, the bound of the detection gate, the reconstruction and context-fit checks) goes to the next code review round.
