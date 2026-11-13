# Review round 13: the corrections of review round 12 (code of protocol v2.3)

Round 12 (`docs/audit/2026-11-13_reviewer_round12_codex_gpt61sol.md`) found no critical point, one major point and six minor points; the author's corrections are in `docs/audit/2026-11-13_round12_author_response.md`. Run (k) of Appendix A.4 was made again after them. None of that code has been reviewed. This round reviews it.

## Rules

- Read-only: do not create, modify or delete any file.
- Read only files inside the working directory. Do not open, list or search anything outside it, even where the sandbox would allow it.
- Shell: PowerShell is broken on this machine and every PowerShell command hangs. Run every command through `exec_command` with the parameter `shell` set to `C:\Program Files\Git\bin\bash.exe`. `cat`, `sed -n`, `grep`, `head`, `wc`, `diff` and `awk` work, and `awk` does arithmetic. Python and `jq` are not available, so you cannot run the code or the tests: their outputs are in `review_aids/`. Read large files in parts.
- Do not run any model or API call.
- Web search is allowed only to check a provider's public API documentation or a cited paper. Never put text from this folder in a query, beyond file names, function names, paper titles and generic keywords.
- If a claim needs a run you cannot make, specify the run exactly (command, input, expected output); the author will run it.
- The folder holds no answer text, no benchmark prompt file, no label key and no secret.
- Local paths are replaced by placeholders (`<repo>`, `<work>`, `<tmp>`, `<home>`, `<ollama>`). The files are otherwise unchanged, and line endings are LF.
- Conflict of interest: you are model 11 of the commercial panel. Say where a point you raise bears on your own developer's models.

## Files

- `review_aids/diff_since_round12.diff`: every change to the code, the configuration, the tests and the protocol since the copy you reviewed in round 12. Start here.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md`, `docs/DATA_INVENTORY.md`, `labels/RUBRIC.md`: the protocol, its summary, the decisions, the inventory and the rubric as they now stand.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-13.txt`: the output of all twelve test files (the last is the complete run on synthetic data) with the code under review.
- `review_aids/simulation_logs/logs_2026-11-13/`: the logs of both runs of (k) (`tails.out` the first, `tails_second_run.out` the second); results in `analysis/output/sim_v23_tails.json`, and the first run's output in `analysis/output/logs_2026-11-13/sim_v23_tails_first_run.json`.
- `review_aids/xref_check.txt`: the cross-reference check of the protocol.

## What changed, in short

1. Run (k), part 3 (the major point): the rows at q0 = 0 and 0.025 use smaller shocks so that the target discordance can be reached (`RS1_SD`); every row records its calibration; the run stops if any target is not reached (`calibrated`). Part 1: the P3 draws are disjoint outcomes (`p3_draw`). Part 3: tests carried out are counted from `p*_carried_out` (`d20_counts`). Run (k) was made again, and its figures changed the text of Sections 8.1 and 17.1 and of Appendix A.4: with no background discordance the condition of D20 lowers the power of P1 under θ_S = −5 points to 0.926.
2. The screen-positive counts of the disclaimer table (`analysis/analyze_v23.py`, `disclaimers`).
3. Text only: the `declined` rule in round 2 of the pilot (Section 10.2); the token figures of the D16 rule (Section 3.3 and a dated note in `docs/PI_DECISIONS.md`); the registration summary of the crossed comparison; the status, conditions, D5 and D7 in `docs/PI_DECISIONS.md`; status lines.
4. The inventory writer `scripts/data_inventory.py` brought in line with decision D18. It was not run, because it reads the sealed files.
5. Tests: three new in `tests/test_sim_v23_boundaries.py` and `test_disclaimers` extended; 186 declared tests in the eleven offline files.
6. As before, none of these changes may touch the files whose code enters the fingerprints of the stored rows of runs (a) to (g): `analysis/inference_v23.py`, `analysis/sim_v23_dgp.py`, `analysis/sim_v23_registered.py`, and the frames and control assignment.

## Task

1. **Correctness.** For each change above: does the code do what the protocol text says, on every path? In particular: does every row of run (k) reach its targets, and does its output record that; are the P3 draws a distribution with the stated mean and bound; do the figures in Sections 8.1, 17.1 and A.4 match `analysis/output/sim_v23_tails.json`; would the inventory writer, if run, write what `docs/DATA_INVENTORY.md` now says in the parts that D18 changed?
2. **The tests.** Do the new and changed tests check what their names claim, and would they fail if the change they cover were undone?
3. **Consistency.** Do the code, the configuration, the protocol, the summary, the inventory and the decisions agree (figures, hashes, settings, file names)? Did a change leave an older path, flag or document stale?
4. **Fingerprints.** Confirm that no file in the fingerprint of the stored simulation rows changed, or name the change.
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 1,200 words.
