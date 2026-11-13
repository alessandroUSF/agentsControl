# Review round 14: the PI's decisions D23 to D26 (code of protocol v2.3)

Round 13 (`docs/audit/2026-11-13_reviewer_round13_codex_gpt61sol.md`) found no critical or major point; its one wording point is corrected (`docs/audit/2026-11-13_round13_author_response.md`). On 13 November 2026 the PI then took four decisions, D23 to D26 (`docs/PI_DECISIONS.md`). Two of them changed the code, the judge template and the configuration. None of that has been reviewed. This round reviews it.

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

- `review_aids/diff_since_round13.diff`: every change to the code, the configuration, the tests, the rubric and the protocol since the copy you reviewed in round 13. Start here.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md`, `labels/RUBRIC.md`: the protocol, its summary, the decisions and the rubric as they now stand.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-13.txt`: the output of all twelve test files (the last is the complete run on synthetic data) with the code under review.
- `review_aids/judge_reasoning_v23.json`: the log of the local measurement of decision D24 (harmless sentinel pairs; the raw outputs are kept outside the repository under decision D22).
- `review_aids/xref_check.txt`: the cross-reference check of the protocol.

## What changed, in short

1. **D25, the class `clarification`.** It moved from Part B of the rubric (labellers only) into Part A.1, which the judges share. The judge template was written again from Part A (`scripts/build_judge_template_v23.py`, `config/judge_prompt_v23.txt`, new SHA-256), with the fourth class in the instruction; the parser accepts it (`src/judge_v23.py`, `LABELS`). A verdict of `clarification` is not a refusal under Section 8.7 (`analysis/analyze_v23.py` is unchanged: its `REFUSAL` holds the two refusal classes). The manifest was priced again for the longer Part A (`scripts/manifest_v23.py`, `RUBRIC_GROWTH`; `analysis/output/manifest_v23.json`; `config/stage_holds.json`), and every figure that depends on it was updated in Sections 1, 11.3, 12.2, 12.4 and 19.1, the registration summary and the D16 note.
2. **D24, the output cap of models 16 and 17 as judges.** A measurement script (`scripts/measure_judge_reasoning_v23.py`) was written and run locally; the results are in Section 11.3 and the D24 entry. The settings give both models a cap of their own (`config/judge_v23.json`, `output_cap_by_judge`), read by a new function (`src/judge_v23.py`, `local_output_cap`), which `judge_cfg` and the context-fit step (`scripts/context_fit_v23.py`) use.
3. **D26, the check of model 22's provider.** Text only (Sections 3.3 and 13.2). No code exists for it yet.
4. **D23.** Text only (the entry and the table of Section 19.1).
5. **Tests.** `t_parser_rules` and the judge configuration checks in `tests/test_judges_v23.py` were extended; the synthetic verdicts of `tests/test_sim_v23_analyze.py` now include `clarification` on safe prompts, without a new random draw. The number of declared tests is unchanged (186).
6. As before, none of these changes may touch the files whose code enters the fingerprints of the stored rows of runs (a) to (g): `analysis/inference_v23.py`, `analysis/sim_v23_dgp.py`, `analysis/sim_v23_registered.py`, and the frames and control assignment.

## Task

1. **Correctness.** For each change above: does the code do what the protocol text says, on every path? In particular: does the template's rubric section equal Part A of the rubric and is its SHA-256 the one recorded; does every reader of a verdict label accept the fourth class and treat it as the protocol says (flags, the pilot report, the label tools, the join); is the per-judge cap used wherever the local cap is used (the judging runner, the context fit, the pilot report's cap counts, rule 3); do the repriced figures match `analysis/output/manifest_v23.json`; does the context arithmetic of Section 11.3 hold for the doubled cap of models 16 and 17?
2. **The tests.** Do the changed tests check what they claim, and would they fail if the change they cover were undone?
3. **Consistency.** Do the code, the configuration, the template, the rubric, the protocol, the summary and the decisions agree (figures, hashes, settings, class lists)? Did a change leave an older path, statement or count stale (for example "three classes")?
4. **Fingerprints.** Confirm that no file in the fingerprint of the stored simulation rows changed, or name the change.
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 1,200 words.
