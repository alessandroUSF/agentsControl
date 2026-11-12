# Review round 5: the code of protocol v2.3, before the pilot registration

Rounds 1 to 4 reviewed the design. Round 4 (`docs/audit/2026-11-10_reviewer_round4_codex_gpt61sol.md`) found the protocol ready for the PI's decisions and for the missing code. That code now exists. Section 19.4 of the protocol lists it, and it was tested offline only: stub providers, synthetic data, no model called. The PI has since taken decisions D12 and D14 to D18, D1, the rest of D2 and part of D13 (`docs/PI_DECISIONS.md`, Section 19.1). On 12 November 2026 the simulations before the freeze (Appendix A.4) also made a revision of the inference necessary: amendment D19 (domain degrees of freedom, Section 8.1) is applied for the check and awaits the PI's decision. No review round has checked the code, these decisions or D19. This round does.

## Rules

- Read-only: do not create, modify or delete any file.
- Read only files inside the working directory. Do not open, list or search anything outside it, even where the sandbox would allow it.
- Shell: PowerShell is broken on this machine and every PowerShell command hangs. Run every command through `exec_command` with the parameter `shell` set to `C:\Program Files\Git\bin\bash.exe`. `cat`, `sed -n`, `grep`, `head`, `wc`, `diff` and `awk` work, and `awk` does arithmetic. Python and `jq` are not available, so you cannot run the code or the tests: their outputs are in `review_aids/`. Read long files in parts of about 250 lines (for example `sed -n '1,250p' file`) and set `max_output_tokens` high enough that the output is not truncated. Never print a whole file of more than 1,000 lines.
- Do not run any model or API call.
- Web search is allowed only to check a provider's public API documentation or a cited paper. Never put text from this folder in a query, beyond file names, function names, paper titles and generic keywords.
- If a claim needs a run you cannot make, specify the run exactly (command, input, expected output); the author will run it.
- The folder holds no answer text, no benchmark prompt file, no label key and no secret. The render-check files in `review_aids/render_checks/` hold only sentinel texts.
- Local paths are replaced by placeholders (`<repo>`, `<work>`, `<tmp>`, `<home>`, `<ollama>`). The files are otherwise unchanged, and line endings are LF.
- Conflict of interest: you are model 11 of the commercial panel. Say where a point you raise bears on your own developer's models.

## Files

- `docs/STUDY_PROTOCOL_v2.3.md`: the protocol. Section 19.4 lists the code; Appendix A holds the simulations.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `docs/PI_DECISIONS.md`: the decisions, with their consequences for the code.
- `review_aids/offline_tests_2026-11-12.txt`: the output of all eleven test files on 12 November 2026, with the code under review (after D17, D18 and the change of amendment D19).
- `review_aids/code_diff_since_commit.diff`: the diff of `src/`, `scripts/`, `analysis/*.py`, `config/` and `tests/` since the local commit of 11 November 2026. The commit holds the code as first written. The diff holds decision D2 (Google adapter, later unused), D17 (model 14 out), D18 (no sealed answer used; respondent seed 20261126), the thinking setting of the render check, one fix in `analysis/analyze_v23.py` (`call_state`), the safe-side intervals withdrawn under Appendix A.4 (`SAFE_NO_INTERVAL`), and amendment D19 (`_domain_df` in `analysis/inference_v23.py`).
- `analysis/output/sim_v23_*.json`: the results of Appendix A with the code under review (amendment D19 applied). `review_aids/results_registered_code_before_D19/`: the same runs with the registered code, which led to D19. `review_aids/simulation_logs/`: the console output of every run (`sims_domdf`: the code under review; `sims_freeze` and `sims_d17`: the registered code; `try_domdf_rare.out`: a first trial of D19 in the cluster ratio only).
- `docs/PROVIDER_TERMS_FACTS_2026-11-12.md`: facts on the providers' terms, copied for the PI; context only, not under review.
- `review_aids/render_checks/`: the content checks of the eleven local judge builds (Section 11.7).
- `review_aids/xref_check.txt`, `review_aids/sealed_hash_check.txt`: the cross-reference check of the protocol and the hash check of the sealed files.

## Task

1. **Fidelity.** Does the code do what the protocol says? Take these in order and stop on each where the code and the text differ:
   a. Frames, the control assignment and yoking, the label sample and its weights (Sections 5, 6, 9.2 to 9.5).
   b. Judging: the four verdicts and the two presentations (Sections 2.2, 11.1, 11.2), settings (11.3), order (11.4), parser, retry and log (11.5), the statuses of failed calls (10.1, 10.2).
   c. What is sent: the blocks and their order (12.3), the pilot (13.2), decisions D2, D13, D17 and D18, the sealed runs, the respondent seed, the pinned endpoints (3.3, 16.2, 16.4).
   d. Money: the reservation bound, the settlement, the cap and ceiling, the cuts in their order, the holds, price changes, fees (12.2, 12.4, 12.5).
   e. Analysis: P1, P2 and P3 with their α (8.2, 8.3), the strata, the cluster ratio interval and its degrees of freedom (8.1, amendment D19: check `_domain_df` and each of its three callers, and look for any code that still assumes 298), the boundaries, the secondary analyses (8.5 to 8.7), the label estimators and the withdrawn intervals (9.5, Appendix A.4), the bounds for calls not attempted (10.3, 10.4).
   f. The numbers of the protocol that the code produces (Sections 12.1 and 12.2, Appendix A): can they be traced to the stored output files?
2. **Readings.** The code marks with `[reading: ...]` the places where the protocol leaves a detail open. For each, say whether the reading is faithful to the protocol, defensible, or wrong, and why.
3. **Safety and data handling.** Check that answer and prompt text never reaches a public log or a committed file. Check that keys are never printed, and that harmful prompts go only through the research keys (`AC_*`). Check that sealed runs are never written and never read as answers of the study. Then check that a crash and restart never pays twice or keeps two verdicts for one call, and that the cap holds under retries, concurrency and a price rise.
4. **Tests.** Do the tests check what their names claim? Name the important behaviours that no test covers, and code mutations that every test would miss.
5. **Verdict.** Is the code ready for the pilot registration? List what must change first, ranked critical, major or minor, each with `file:line` and a concrete fix.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 3,000 words.
