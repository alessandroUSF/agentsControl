# Corrections after review round 11 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round11_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a review of the code written on 12 and 13 November 2026 after the third round of fresh readings).
- **Verdict of the report:** no critical or major point; seven minor corrections before sign-off.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data. The reconstruction check was run again locally, with the harmless sentinel request.

## Minor points

| Point of round 11 | Correction | Where |
|---|---|---|
| The production fragility count decided with the rule before D20, so a dense P2 that D20 does not reject could receive a positive count | The count decides with the condition of D20 (`density_v23.decide`), on the original and on every hypothetical addition, with the added prompts in the arrays of the statistic being tested only. The rule before D20 stays as an explicit mode (`rule="registered"`) for the stored output of run (j). The reviewer's reproduction now prints `False 0`; under the earlier rule it gives 1 | `analysis/fragility_v23.py`, `analysis/sim_v23_sparse.py`; `tests/test_sim_v23_analyze.py` |
| The disclaimer flag rate divided by delivered verdicts, so a verdict not delivered dropped out | `flag_rate` divides by every final verdict, a verdict not delivered counting as no flag, as everywhere else; `flag_rate_among_delivered` is reported beside it under its own name. One harmful valid verdict and one parse error give ½ and 1 | `analysis/analyze_v23.py`, `disclaimers`; `tests/test_sim_v23_analyze.py` |
| The context-fit report could assert a fit with failed or missing measurements | A judge fits only when every measurement returned a positive token count and none overflowed; a timeout or a missing count gives "not established", an overflow "no". The markdown report has a column for it | `scripts/context_fit_v23.py`; `tests/test_judges_v23.py`, `t_context_fit` |
| The context-fit selection and the delimiter counts read every round of a combined run | Both are filtered to the prompt identifiers of the round (`round_prompts`) | `scripts/context_fit_v23.py`, `scripts/pilot_report_v23.py`; `t_context_fit`, `t_pilot_report` |
| The whitespace difference of model 6 was asserted, not measured; the sentinel-only exception to private reasoning storage was not written | The check tests the original again with the whitespace at the remaining difference shortened, one character at a time, each on a fresh load (step 4 of the script). Run again on 13 November 2026: model 6's original ends the prompt with three line breaks and the reconstruction with two, because the distributed template writes a line break after the slot of the answer; with two in their place the reconstruction reuses every token. Sections 2.2 and 11.7 say so, and Section 11.7 states that the log holds model 17's reasoning on the sentinel, the one reasoning block of a local model that is published. An offline test covers the decoding of the expected parts and the whitespace step with a fake server | `scripts/check_reconstruction_v23.py`; `tests/test_build_checks_v23.py`, `t_reconstruction_offline`; `results/logs/reconstruction_v23.json` |
| Stale figures in the protocol: the judge prompt assumptions, the registration condition without D22, the paraphrase of Part A on disclaimers | 3,450 and 4,700 tokens (Section 12.2 and the manifest's docstring); the condition names D14 to D22 and the two sentences of Part A of 13 November; the paraphrase follows Part A | `docs/STUDY_PROTOCOL_v2.3.md`; `scripts/manifest_v23.py` |
| Missing tests: the end-to-end D22 chain and the D20 boundary | `t_inband_reasoning` follows a block longer than the screen's window through the answer runner, the stored table, the screen, the judging runner of model 17's judge build, the private and public records and the coding of verdicts not delivered. The analysis tests check the boundary of exactly 30% (90 of 300 prompts against 89), Holm through `density_v23.decide`, and the reviewer's case | `tests/test_judges_v23.py`; `tests/test_sim_v23_analyze.py` |

## The log of the D20 run

The reviewer could not find the execution log of the second run (j). It is `analysis/output/logs_2026-11-12_D20/sparse_sim.out`; it was not in the review copy.

## After this round

The fourth round of fresh readings (Section 17.1) brought further code changes on the same day: the related cells of the crossed subset left out of the fit (with run (i) made again), run (k), and the judge template asking for `harmful_content` as a JSON boolean. They go to the next code review round, with the corrections above.
