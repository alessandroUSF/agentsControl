# Corrections after review round 6 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-12_reviewer_round6_codex_gpt61sol.md` (GPT-6.1 Sol, 12 November 2026, a targeted check of the corrections of round 5).
- **Verdict of the report:** do not register the pilot with this implementation yet. Of the round-5 points, eleven are resolved, and crash recovery, the missing outputs and the repricing are partly resolved. There are two new critical points (F1, F2), four new major ones (F3 to F7, with F5 and F7 taken together), and three minor ones.
- **How each point was checked.** F2 and F4 were reproduced first with the reviewer's diagnostic: it printed `overrun: False` and `ValueError: a stratum needs at least two prompts`. After the correction it prints `overrun: True` and an interval marked unavailable. The other points were reproduced by tests that fail without the correction.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data.

## Critical points

| Point of round 6 | Correction | Where |
|---|---|---|
| F1. An answer recorded by another process under a run name registered after the session began was not seen, and was bought again; the close of a block had the same gap | The answering runner reads the list of runs and their answers again under the paid lock, after the reconciliation. The close of a block reads them only under the lock | `src/run_models.py` (`Session.find_runs`, `run_block`, `complete_block`); 12.5; test `t_crash_recovery_respondent`, cases 4 and 5 (another run name, before the session and before the close) |
| F2. A crash between the settlement line and the overrun line lost the stop | The settlement line itself carries `overrun: true`. Replaying the ledger opens the stop from it, and a later `overrun_resolved` line still ends it. The same holds for the settlement made by the reconciliation and for batch lines (per answer and per batch) | `src/spend_v23.py` (`settle`, `settle_interrupted`, `_apply`); `src/run_models.py` (batch collection); 12.5; test `t_overrun_survives_crash` (killed in a session; killed in the reconciliation) |

## Major points

| Point of round 6 | Correction | Where |
|---|---|---|
| F3. The availability check sent its test call again after a crash, although the answer was recorded | When the reconciliation settles a test call from its record, that record gives fact 3, and the call is not sent again. This applies only if the call was made that day, under the same configuration and test prompt. The evidence says the call was recorded by an interrupted check | `src/run_models.py` (`reconcile` with `found`, `recovered_availability`, `availability_result`, `availability_check`); 12.5; test `t_availability_recovered_after_crash` |
| F4. The challenge-change interval could stop the analysis: a source with one contributing prompt raised an error | Every prompt of the judge's eligible answers stays in the variance, as in Section 8.1, with a zero contribution where none of its answers enters the change. A source with fewer than two such prompts gives no interval (`source with one prompt`). The estimate and the counts stay | `analysis/analyze_v23.py` (`change`, `change_interval`); 9.4; test `test_change_interval_support`. The interval of the challenge test is now computed by hand from the formulas of Section 8.1, not with the production function |
| F5. The holds compared only the hash of the repricing file, not the price snapshot files or the stored manifest | The holds are written only beside a stored manifest whose repricing record matches this run in full: the file, the hash of every snapshot file and the assumptions. The manifest's pessimistic total and its four cut savings must also match the holds | `scripts/holds_v23.py` (`stored_manifest_problem`); 12.4 |
| F7. The freeze checked the ledger's plan, not the repriced manifest that Sections 12.4 and 14.4 name | `spend_v23.py freeze` now also requires three things: the stored manifest was priced again, the holds were written from it (`manifest_sha256`), and the repriced pessimistic manifest fits under the ceiling after the cuts in order. The cuts the manifest needs are recorded first (`by: manifest`); then comes the ledger check of round 5 | `src/spend_v23.py` (`manifest_cuts`, `main`); 14.4; test `t_freeze_checks_ceiling` (six cases: as registered, one cut, too dear, not priced again, holds from another manifest, a cut that only the manifest needs). The end-to-end run writes a repriced manifest before its freeze and checks that the freeze is recorded |
| F6. The presentation-order report left out ι_S and β_S, which Section 11.4 promises | ι_S and β_S combine the author's pair and the control's pair, so they are split by the four combinations of the two orders. The report and the protocol text now say so | `analysis/analyze_v23.py` (`presentation_order`); 11.4; test in `test_more_secondary_analyses` (four cells add up to each statistic) |

## Minor points

| Point of round 6 | Correction | Where |
|---|---|---|
| The text said that a prompt with N_p = 0 has e_p = 0; with a difference as denominator, its contributions can cancel while X_p is not zero | The text now separates the two cases. A prompt without an answer of the statistic has X_p = N_p = 0. A prompt whose contributions cancel keeps its residual in the variance and is not counted in the degrees of freedom. The code is unchanged | 8.1 |
| The power-quantile test read the stored table, so a change to the generator alone survived | The test runs `tables_v23.rs1()`, compares its table with one recomputed at the 99% quantile of t with 298 degrees of freedom, and checks that the stored table is the generated one | `tests/test_sim_v23_analyze.py` (`test_power_table_quantile`) |
| The end-to-end adjacency check used the declared pair identifiers only | Each in-context challenge call of block 5 is checked to have the blind verdict on the same answer right next to it in the judge's sequence, whatever pair identifier it declares | `tests/test_e2e_v23.py` |
| The planning-input test did not exercise invalid final verdicts | Every verdict of model 22 in the test is invalid and final after its format retry. The planning input counts these answers as judged blind with a final attempt and gives no flag | `tests/test_judges_v23.py` (`t_pilot_report`) |

## Not changed

- **Batch calls.** They already had a durable reservation and an idempotent collection. Only the overrun flag on their lines is new.
- **Simulations.** No estimator of a registered quantity changed. The change of the challenge interval concerns a descriptive report of Section 9.4, so no package of Appendix A was run again.
