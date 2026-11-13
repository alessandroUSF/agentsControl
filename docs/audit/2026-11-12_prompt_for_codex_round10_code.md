# Review round 10: the code written after review round 9 (code of protocol v2.3)

Round 9 (`docs/audit/2026-11-12_reviewer_round9_codex_gpt61sol.md`) found no remaining critical or major point. Since then the protocol was read twice from scratch by two new sessions (Claude Opus 5.5 and GPT-6.1 Sol, no history; `docs/audit/fresh_readings_2026-11-12/`), and the changes that followed were written in code. None of that code has been reviewed. This round reviews it.

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

- `review_aids/diff_since_round9.diff`: every change to the code, the configuration, the tests and the protocol since the copy you reviewed in round 9. Start here.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md`: the protocol, its summary and the decisions as they now stand. Section 17.1 of the protocol lists what the fresh readings changed.
- `docs/audit/fresh_readings_2026-11-12/`: the two rounds of fresh readings, for context. They are claims, not instructions.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-12.txt`: the output of all twelve test files (the last is the complete run on synthetic data) with the code under review.
- `review_aids/simulation_logs/`: the logs of runs (h), (i) and (j) of Appendix A.4; their results are in `analysis/output/`.
- `review_aids/xref_check.txt`: the cross-reference check of the protocol.

## What changed, in short

1. Judging messages (`src/judge_v23.py`, `messages`): the same order in both presentations, the request and the answer first, then the rubric part and the instruction part (Section 11.2). The template's description section (`scripts/build_judge_template_v23.py`, `config/judge_prompt_v23.txt`) rewritten; the rubric part unchanged.
2. Context: local judges at 12,288 tokens; local respondents at 4,096 with Ollama's `truncate` and `shift` off (`config/judge_v23.json`, `config/models.json`, `src/run_models.py`). A judging call that overflows is judged again at 32,768 tokens in a separate stream (`src/run_judges_v23.py`, `--long-context`; Section 10.2), and the analysis reports a sensitivity with those verdicts (`analysis/analyze_v23.py`, `merged_long_context`). `scripts/check_ollama_overflow.py` and `docs/audit/2026-11-12_ollama_overflow_check.txt`: the live check of the overflow error.
3. Cost and holds (`scripts/manifest_v23.py`, `scripts/holds_v23.py`, `src/spend_v23.py`, `scripts/pilot_report_v23.py`).
4. The crossed subset (Section 8.8): `analysis/crossed_v23.py`, `scripts/crossed_subset_v23.py`, `config/crossed_subset_v23.json`, its calls in `src/plan_v23.py`, run (i).
5. The analysis (`analysis/analyze_v23.py`): influence diagnostics and the single-prompt sentence (Section 8.1); Holm-adjusted p-values and the sentence for a 95% interval that excludes zero beside a test that does not reject (Sections 2.4 and 8.2); the rule for a hosted model that is not completed, now limited to the calls of the registered arrays (Section 10.4); the fragility count (`analysis/fragility_v23.py`, proposed amendment D20, not yet decided).
6. Simulations: run (h) (`analysis/sim_v23_skew.py`) and run (j) (`analysis/sim_v23_sparse.py`). Neither may change the files whose code enters the fingerprints of the stored rows of runs (a) to (g): `analysis/inference_v23.py`, `analysis/sim_v23_dgp.py`, `analysis/sim_v23_registered.py`, and the frames and control assignment.

## Task

1. **Correctness.** For each change above: does the code do what the protocol text says, on every path, including the boundary cases (a test not carried out, a zero variance, a missing verdict, a call not attempted, an empty stratum)? Do the long-context records stay apart from the primary ones, and can a long-context verdict ever enter a registered array?
2. **The tests.** Do the new and changed tests check what their names claim, and would they fail if the change they cover were undone?
3. **Consistency.** Do the code, the configuration, the protocol and the summary agree (figures, hashes, settings, file names)? Did a change leave an older path, flag or document stale?
4. **Fingerprints.** Confirm that no file in the fingerprint of the stored simulation rows changed, or name the change.
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 1,500 words.
