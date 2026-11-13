# Corrections after review round 12 (code of protocol v2.3)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round12_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026, a review of the corrections of round 11 and of the code written after the fourth round of fresh readings).
- **Verdict of the report:** no critical point; one major point and six minor points before sign-off.
- **No paid call, no answer and no verdict** was made for these corrections. Every test is offline, with synthetic data, and run (k) is a simulation.

## The major point

| Point of round 12 | Check and correction | Where |
|---|---|---|
| Run (k) discarded the calibration record, so its rows at q0 = 0 and 0.025 could run at another discordance without saying so | Confirmed with the reviewer's command: every row at q0 = 0 and 0.025 had the coupling at 1 and the target listed as not reached, with a floor of 0.0408 to 0.0409; the rows at 0.05 were reached (coupling 0.955). The floor comes from the shocks of the base case (standard deviations 0.3). The rows at q0 = 0 and 0.025 now use shocks with standard deviations 0 and 0.1 (floors 0 and 0.0136, measured); every row records the coupling, the floor, the discordance with independent draws and any target not reached; and the run stops if a target is not reached. Run (k) was made again; every target was reached. The result changes one statement: with no background discordance at all, the condition of D20 lowers the power of P1 under θ_S = −5 points from 1.000 to 0.926 (P1 is carried out in 92.6% of the replications); at 0.025 to 0.998; at 0.05 not at all. Under θ_S = 0 at q0 = 0 and 0.025, P1 is carried out in 0% to 1.2% of the replications, where the t test alone would reject in 3.2% against 2% (joint null) and 4.7% against 4% (P2 rejecting). Sections 8.1, 17.1 and A.4 say so; the first run's output and log are kept | `analysis/sim_v23_tails.py` (`RS1_SD`, `calibrated`); `analysis/output/sim_v23_tails.json`; `analysis/output/logs_2026-11-13/tails_second_run.out`; `tests/test_sim_v23_boundaries.py`, `test_tails_rs1_targets_reached` |

## Minor points

| Point of round 12 | Correction | Where |
|---|---|---|
| Two P3 rows could add a background change of −1 to a full deficit of −6, a total of −7 with N_p = 6 | The deficit, the background rise and the background fall are disjoint outcomes (probabilities π, bg/2, bg/2); the mean stays −0.42 per prompt (β_S = −0.07), the draw asserts \|X_p\| ≤ 6 and refuses a row with π + bg > 1. The P3 rates changed by at most 0.1 point (m = 3 with background: 1.7% to 1.6%) | `analysis/sim_v23_tails.py`, `p3_draw`; `test_tails_p3_support` |
| Run (k) counted a dense statistic as a test carried out | `carried_out_share_d20` counts `p1_carried_out` and `p2_carried_out` of `density_v23.decide` (dense and a positive estimated variance); the dense share is reported beside it as `dense_share_d20`. Constant totals X = 1 with N = 6 on all 300 prompts give density 1 and no test | `analysis/sim_v23_tails.py`, `d20_counts`; `test_tails_carried_out_not_dense` |
| The screen-positive counts of the disclaimer table tested the truth of a string, so `"negative"` counted | The count compares with `screen.POSITIVE`. The test fixtures use the strings of `src/screen.py`, and a case with one answer of each screen result checks both counters | `analysis/analyze_v23.py`, `disclaimers`; `tests/test_sim_v23_analyze.py`, `test_disclaimers` |
| `declined` in the pilot: the text said the initial list throughout the pilot, the code reads the list in force | The code is right and the text was wrong: round 2 of the pilot runs to check a revised screen on fresh prompts (Section 13.3), so it uses the revised list. Section 10.2 now says: the initial list in round 1, the revised list in round 2 and in the main run if the screen is revised | `docs/STUDY_PROTOCOL_v2.3.md`, Section 10.2 |
| Regenerating the inventory would bring back statements that D18 retired | The writer emits the D18 note, the column "Frame answers to generate (decision D18)" with 390 for every model, the totals as all to be generated, the note on the pilot of version 1 and the note on G1, as in the file of 13 November. It was not run, because it reads the sealed files; it compiles | `scripts/data_inventory.py` |
| Document copies out of step | The registration summary says that related cells are left out of the crossed fit. In `docs/PI_DECISIONS.md`: the status line names D20 to D22 and the two sentences of Part A; the list of conditions puts D7 and D14 to D22 before the pilot registration, with the D7 reader's reading of the pilot report before the freeze (D7 now says "Recorded before: pilot registration", as Sections 14.2 and 19.1 do); the text of D5 says "scripts and commands", as Section 19.3 does; a dated note under D16 says that the endpoints stand at 4,700 tokens in (the price is linear in the tokens and the rule gave the same endpoints at 4,500 and 5,500). Section 3.3 says the same of the 4,500-token figures | `docs/REGISTRATION_v2.3.md`; `docs/PI_DECISIONS.md`; `docs/STUDY_PROTOCOL_v2.3.md`, Section 3.3 |

## Tests

186 declared tests in the eleven offline files (183 before; three new in `tests/test_sim_v23_boundaries.py`, and `test_disclaimers` extended). Each new assertion fails if its correction is undone: the old P3 draw gives totals of −7, a count of dense tests gives (1, 1) where (0, 1) is expected, and the shocks of the base case at q0 = 0 are refused.

## After this round

The code of these corrections goes to review round 13.
