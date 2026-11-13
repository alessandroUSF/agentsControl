# Review round 17: the corrections of review round 16 (code of protocol v2.3)

Round 16 (`docs/audit/2026-11-13_reviewer_round16_codex_gpt61sol.md`) found no critical or major point and five minor points in the changes of decision D27. The author's corrections are in `docs/audit/2026-11-13_round16_author_response.md`. This short round checks them.

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

- `review_aids/diff_since_round16.diff`: every change since the copy you reviewed in round 16. Start here.
- `docs/audit/2026-11-13_round16_author_response.md`: what was changed for each point.
- `docs/STUDY_PROTOCOL_v2.3.md` (Sections 11.6, 12.1, 13.1), `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md` (D27): as they now stand.
- Code: `src/run_judges_v23.py` (`pilot_repeat_gate`, `JudgeRun.run`, `main`), `scripts/pilot_report_v23.py` (`repeatability`, `main`, `markdown`). Tests: `tests/test_judges_v23.py` (`t_pilot_repeat_gate`, `t_pilot_report`), `tests/test_e2e_v23.py`.
- `review_aids/offline_tests_2026-11-13.txt`: the output of all twelve test files with the code under review.

## Task

1. **The repeat gate.** Are the pilot repeat calls of a local judge now sent only when its other calls of the round are final and none of its own answers to the round's harmful prompts is missing, on every path (one session, several sessions, a pending call, a deferred pair, `--max-calls`, `--allow-missing`, the longer context of Section 10.2, `--complete-block`)? Does the stop on a changed draw happen before any call, paid or local? Can the gate hold repeat calls forever where the protocol expects them to be sent, or let them through where it does not? Does it change any call that is not a pilot repeat call?
2. **The report.** Does `investigate` now follow any difference of flag, status or output? Is a judge with fewer pairs than planned marked incomplete in the JSON, the rule line and the Markdown, and is the planned number right? Does the report still write no flag?
3. **The texts.** Are the corrections of Sections 11.6, 12.1 and 13.1, the summary and D27 right and consistent with the code?
4. **The tests.** Does `t_pilot_repeat_gate` check what it claims, and would it fail if the gate were removed or ignored missing answers? Do the strengthened checks of `t_pilot_report` fail if output differences or incomplete coverage were ignored?
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 700 words.
