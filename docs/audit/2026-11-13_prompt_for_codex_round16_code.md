# Review round 16: the changes of decision D27 (code of protocol v2.3)

Round 15 (`docs/audit/2026-11-13_reviewer_round15_codex_gpt61sol.md`) found no critical or major point; its three minor points were corrected (`docs/audit/2026-11-13_round15_author_response.md`). The fifth and last round of fresh readings then left seven points to the PI, who decided them on 13 November 2026 (decision D27 in `docs/PI_DECISIONS.md`). This short round checks the changes they brought.

## Rules

- Read-only: do not create, modify or delete any file.
- Read only files inside the working directory. Do not open, list or search anything outside it, even where the sandbox would allow it.
- Shell: PowerShell is broken on this machine and every PowerShell command hangs. Run every command through `exec_command` with the parameter `shell` set to `C:\Program Files\Git\bin\bash.exe`. `cat`, `sed -n`, `grep`, `head`, `wc`, `diff` and `awk` work, and `awk` does arithmetic. Python and `jq` are not available, so you cannot run the code or the tests: their outputs are in `review_aids/`. Read large files in parts.
- Do not run any model or API call.
- Web search is allowed only to check a provider's public API documentation or a cited paper. Never put text from this folder in a query, beyond file names, function names, paper titles and generic keywords.
- If a claim needs a run you cannot make, specify the run exactly (command, input, expected output); the author will run it.
- The folder holds no answer text, no benchmark prompt file, no label key and no secret. `src/prepare_data.py` is left out because it holds fragments of the study's own prompts; nothing in this round depends on it.
- Local paths are replaced by placeholders (`<repo>`, `<work>`, `<tmp>`, `<home>`, `<ollama>`). The files are otherwise unchanged, and line endings are LF.
- Conflict of interest: you are model 11 of the commercial panel. Say where a point you raise bears on your own developer's models.

## Files

- `review_aids/diff_since_round15.diff`: every change since the copy you reviewed in round 15. Start here.
- `docs/PI_DECISIONS.md`, entry D27: what the PI decided.
- `docs/STUDY_PROTOCOL_v2.3.md` (Sections 7.3, 8.1, 11.6, 12.1, 13.2, 13.3 rule 6, 15.3, 17.1, 19.1, action 23 of 19.2, Appendix A.4 run (k)), `docs/REGISTRATION_v2.3.md`, `labels/RUBRIC.md`, `config/judge_prompt_v23.txt`.
- Code: `src/plan_v23.py` (block 1), `scripts/pilot_report_v23.py`, `scripts/reading_draw_v23.py`, `analysis/sim_v23_tails.py`, `scripts/build_judge_template_v23.py`. Tests: `tests/test_judges_v23.py` (`t_pilot_both_rounds_and_close`, `t_pilot_report`, `t_template_without_study_cues`).
- `review_aids/offline_tests_2026-11-13.txt`: the output of all twelve test files with the code under review. `analysis/output/sim_v23_tails.json` and `analysis/output/logs_2026-11-13/tails_added_rows.out`: run (k) with the added rows.

## Task

1. **The pilot repeat calls.** Do the local judges, and only they, get 20 repeat calls per pilot round (10 own answers to the round's harmful prompts with content, both presentations), after their other calls of the round, without changing any other call of block 1 (keys, pairs, order, the API judges, the holds, the block close)? Does the pilot report compare each repeat with its original correctly, and does it keep every flag out of what it writes (Section 13.1)? Can a resumed or partly failed pilot round give a wrong count?
2. **The judge template.** Is the template still Part A of the rubric word for word, and is no phrase left that tells a judge it is part of a study? Is the cost statement of Section 12.1 (the token count of 7,943 characters kept) honest?
3. **Run (k).** Do the added rows use the production code and leave the first nine rows unchanged? Does `--add-to` merge safely (seed, threshold, replications, order)? Do the numbers in Section 8.1, Appendix A.4 and the summary match `sim_v23_tails.json`?
4. **The texts.** Do the protocol, the summary, the decisions, the rubric and the worksheet script agree on the five adopted points and the two not adopted?
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 900 words.
