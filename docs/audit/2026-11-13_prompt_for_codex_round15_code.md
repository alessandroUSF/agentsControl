# Review round 15: the corrections of review round 14 (code of protocol v2.3)

Round 14 (`docs/audit/2026-11-13_reviewer_round14_codex_gpt61sol.md`) found no critical point, one major point (the check of decision D26 was described in Section 13.2 but not written) and four minor points. The author's corrections are in `docs/audit/2026-11-13_round14_author_response.md`. This short round checks them.

## Rules

- Read-only: do not create, modify or delete any file.
- Read only files inside the working directory. Do not open, list or search anything outside it, even where the sandbox would allow it.
- Shell: PowerShell is broken on this machine and every PowerShell command hangs. Run every command through `exec_command` with the parameter `shell` set to `C:\Program Files\Git\bin\bash.exe`. `cat`, `sed -n`, `grep`, `head`, `wc`, `diff` and `awk` work, and `awk` does arithmetic. Python and `jq` are not available, so you cannot run the code or the tests: their outputs are in `review_aids/`. Read large files in parts.
- Do not run any model or API call.
- Web search is allowed only to check a provider's public API documentation or a cited paper. Never put text from this folder in a query, beyond file names, function names, paper titles and generic keywords.
- If a claim needs a run you cannot make, specify the run exactly (command, input, expected output); the author will run it.
- The folder holds no answer text, no benchmark prompt file, no label key and no secret. `src/prepare_data.py` is left out because it holds fragments of the study's own prompts; nothing in this round depends on it. The tokenizer files of model 22 are not in it (17 MB); their SHA-256 values are in `src/run_models.py` (`D26_TOKENIZER`), and the two reference counts they gave are 12 and 566 tokens.
- Local paths are replaced by placeholders (`<repo>`, `<work>`, `<tmp>`, `<home>`, `<ollama>`). The files are otherwise unchanged, and line endings are LF.
- Conflict of interest: you are model 11 of the commercial panel. Say where a point you raise bears on your own developer's models.

## Files

- `review_aids/diff_since_round14.diff`: every change since the copy you reviewed in round 14. Start here.
- `docs/audit/2026-11-13_round14_author_response.md`: what was changed for each point.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md`: as they now stand.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-13.txt`: the output of all twelve test files with the code under review.
- `review_aids/judge_reasoning_v23.json`, `review_aids/xref_check.txt`.

## Task

1. **The major point.** Does `--provider-prompt-check` do what Section 13.2 now says, on every path: after the registration and before the freeze only; the preflight, one call of model 22 with the respondent configuration, reserved and settled against the cap outside every block, recovered after a crash like the D13 call; the answer in the private record only; the reading against the two counts; no second call once one is recorded; the counts in the pilot report? Did generalizing the D13 test call (`test_call`, `write_availability_attempt`, `settle_outside_plan`, `reconcile`) change anything for D13?
2. **The minor points.** Is each correction right and complete?
3. **The tests.** Does `t_provider_prompt_check` check what it claims, and would it fail if the check were broken? Do the strengthened cap and context-fit checks fail if their change were undone?
4. **Consistency and fingerprints.** Do the code, the protocol, the summary and the decisions agree after these changes? Confirm that no input of the stored simulation rows changed.
5. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the five sections above, then a short list of what you could not check. Keep it under about 900 words.
