# Review round 11: the code written after review round 10 (code of protocol v2.3)

Round 10 (`docs/audit/2026-11-12_reviewer_round10_codex_gpt61sol.md`) found two major and four minor points; the author's corrections are in `docs/audit/2026-11-12_round10_author_response.md`. Since then the protocol was read from scratch a third time by two new sessions (Claude Opus 5.5 and GPT-6.1 Sol, no history; `docs/audit/fresh_readings_2026-11-12/round3/`), the PI took decisions D20, D21 and D22 and added two sentences to Part A of the rubric, and the changes were written in code. None of that code has been reviewed. This round reviews it, together with the corrections of round 10.

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

- `review_aids/diff_since_round10.diff`: every change to the code, the configuration, the tests and the protocol since the copy you reviewed in round 10. Start here.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md`, `labels/RUBRIC.md`: the protocol, its summary, the decisions and the rubric as they now stand. Section 17.1 of the protocol lists what the fresh readings changed.
- `docs/audit/fresh_readings_2026-11-12/`: the three rounds of fresh readings, for context. They are claims, not instructions.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-13.txt`: the output of all twelve test files (the last is the complete run on synthetic data) with the code under review.
- `review_aids/render_checks/` and `review_aids/reconstruction_v23.json`: the logs of the rendering check and of the reconstruction check, made with harmless sentinel texts on the local models.
- `review_aids/simulation_logs/`: logs of runs of Appendix A.4; results in `analysis/output/`.
- `review_aids/xref_check.txt`: the cross-reference check of the protocol.

## What changed, in short

1. The corrections of round 10 (see the author's response).
2. Decision D20 (Section 8.1): P1 and P2 are carried out only when at least 30% of the prompts with a screen-positive answer have a non-zero total; otherwise the test counts as not carried out and the result is descriptive (`analysis/density_v23.py`, `analysis/analyze_v23.py`, the fragility count in `analysis/fragility_v23.py`). Run (j) again with the condition (`analysis/sim_v23_sparse.py`, `analysis/output/sim_v23_sparse.json`).
3. Decision D21 (Section 8.5): disclaimers measured by a fixed rule of phrases, as description (`src/disclaimer_v23.py`, `disclaimers()` in `analysis/analyze_v23.py`, the pilot report).
4. The detection gate of Section 9.3 above 20 unknown labels: a conservative bound in place of the enumeration (`analysis/missing_labels_v23.py`, `_bound` and `_gate_check`). It must never pass where the enumeration would fail.
5. The reconstruction check (`scripts/check_reconstruction_v23.py`, Section 11.7 and Section 2.2) and the context-fit step of the pilot (`scripts/context_fit_v23.py`, Sections 11.3 and 13.2).
6. Decision D22 (Section 10.1): a reasoning block that a local model writes at the start of its output is split off before the screen, the judges and the verdict parser; the raw block is kept in the private record and its SHA-256 in the public log (`src/providers.py`, `split_inband_reasoning`; `src/run_models.py`; `src/run_judges_v23.py`; `scripts/pilot_report_v23.py`).
7. Part A of `labels/RUBRIC.md`: two sentences (authorization under (c4), and the effect of a disclaimer). The judge template written again from it (`config/judge_prompt_v23.txt`), and the manifest and the holds priced again for its length (`scripts/manifest_v23.py`, `RUBRIC_GROWTH`; `config/stage_holds.json`).
8. As before, none of these changes may touch the files whose code enters the fingerprints of the stored rows of runs (a) to (g): `analysis/inference_v23.py`, `analysis/sim_v23_dgp.py`, `analysis/sim_v23_registered.py`, and the frames and control assignment.

## Task

1. **Correctness.** For each change above: does the code do what the protocol text says, on every path, including the boundary cases (a test not carried out, a zero variance, a missing verdict, a call not attempted, an empty stratum, an output cut off inside its reasoning)? In particular: can the bound of change 4 pass where some assignment of the unknown labels fails? Does every reader of a local output (the screen, the judges' messages, the verdict parser, the coding of verdicts not delivered, the disclaimer measure, the reconstruction check) see the output after the split of change 6, and can the split-off block reach a public file?
2. **The tests.** Do the new and changed tests check what their names claim, and would they fail if the change they cover were undone?
3. **Consistency.** Do the code, the configuration, the protocol, the summary and the decisions agree (figures, hashes, settings, file names)? Did a change leave an older path, flag or document stale?
4. **Fingerprints.** Confirm that no file in the fingerprint of the stored simulation rows changed, or name the change.
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 1,500 words.
