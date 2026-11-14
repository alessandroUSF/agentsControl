# Review round 18: the guard classifiers (decision D29) and the texts of decisions D7, D28 and D29

Since round 17 (`docs/audit/2026-11-13_reviewer_round17_codex_gpt61sol.md`, corrections in `docs/audit/2026-11-13_round17_author_response.md`) the PI took four decisions on 13 November 2026:

- D28: analyses that are not registered appear only in a separate section headed *post hoc* (Section 8.5).
- D29: two local guard classifiers, Llama Guard 3 8B and Granite Guardian 3.0 8B, classify the 567 labelled answers once, blind, as a descriptive reference for the judges' blind accuracy (Sections 9.4 and 11.8); in the pilot they classify each round's answers to check format, parser and time (Section 13.2).
- D7: the reading of the protocol by an outside methodologist moves from the conditions of the pilot registration to those of the freeze. Changes to Sections 8 and 9 that follow from it are allowed until the freeze (Sections 14.2, 14.3, 14.4, 17.1, 19.1).
- Section 17.1 records mock reviews of the design, what was left for the freeze, and one suggestion not adopted.

This round checks the new code and these texts.

## Rules

- Read-only: do not create, modify or delete any file.
- Read only files inside the working directory. Do not open, list or search anything outside it, even where the sandbox would allow it.
- Shell: PowerShell is broken on this machine and every PowerShell command hangs. Run every command through `exec_command` with the parameter `shell` set to `C:\Program Files\Git\bin\bash.exe`. `cat`, `sed -n`, `grep`, `head`, `wc`, `diff` and `awk` work, and `awk` does arithmetic. Python and `jq` are not available, so you cannot run the code or the tests: their outputs are in `review_aids/`. Read large files in parts.
- Do not run any model or API call.
- Web search is allowed only to check public documentation: the model cards and prompt formats of Llama Guard 3 (Meta) and Granite Guardian 3.0 (IBM), Ollama's API documentation, a provider's public API documentation, or a cited paper. Never put text from this folder in a query, beyond file names, function names, paper titles and generic keywords.
- If a claim needs a run you cannot make, specify the run exactly (command, input, expected output); the author will run it.
- The folder holds no answer text, no benchmark prompt file, no label key and no secret. `src/prepare_data.py` is left out because it holds fragments of the study's own prompts. `review_aids/guard_checks/` holds the check of Section 11.8 on six invented texts written for that check; they are not study material.
- Local paths are replaced by placeholders (`<repo>`, `<work>`, `<tmp>`, `<home>`, `<ollama>`). The files are otherwise unchanged, and line endings are LF.
- Conflict of interest: you are model 11 of the commercial panel. Say where a point you raise bears on your own developer's models.

## Files

- `review_aids/diff_since_round17.diff`: every change since the copy you reviewed in round 17. Start here.
- Code: `config/guards_v23.json`; `src/run_guards_v23.py` (`build_prompt`, `parse`, `OllamaRaw`, `outcome`, `check_identity`, `label_items`, `pilot_items`, `order`, `GuardRun`, `Session`, `main`); `analysis/analyze_v23.py` (`read_guards`, `_guard_forms`, `guard_accuracy`, `analyse`); `scripts/pilot_report_v23.py` (`guards`, `markdown`); `scripts/run_with_memory_guard.py` (mode `guards`).
- Tests: `tests/test_guards_v23.py`, `tests/test_e2e_v23.py` (the guard steps). `review_aids/offline_tests_2026-11-13.txt`: the output of all thirteen test files with the code under review.
- Texts: `docs/STUDY_PROTOCOL_v2.3.md` (Sections 8.5, 9.4, 11.8, 12.1, 13.2, 14.2 to 14.4, 15.2, 16.6, 17.1, 18.4, 19.1), `docs/REGISTRATION_v2.3.md`, `docs/PI_DECISIONS.md` (D7, D28, D29).

## Task

1. **Prompt formats.** Does `build_prompt` render, for each guard, the response-classification format that its developer publishes (the chat template shipped with the model, a user turn and an assistant turn), with the policy named in Section 11.8? Check the role names, the final instruction, the special tokens (the begin-of-text token written by the runner for Llama Guard 3; none for Granite Guardian), white space and the end of the prompt. Say whether any difference from the published format could change what the guard classifies or how its output parses.
2. **Parsing and statuses.** Do `parse` and `outcome` implement the rules of Section 11.8 (first line `safe`/`unsafe`; `Yes`/`No` in any case; anything else not delivered; `context_overflow`; no retry of an off-format output; transient failures retried, then pending; five pending calls in a row stop the guard; the first final attempt is the record)? Can a guard's flag be recorded from a non-final or repeated attempt?
3. **Identity and isolation.** Does the runner stop before any call when the digest or the Ollama version differs? Can it send anything to a non-local server? Is any answer text, request text, output or flag written to the public log, printed, or put in the pilot report?
4. **What is classified.** Are the label-sample items and the pilot items the ones Section 11.8 names (all 567 labelled answers, blind presentation only; in the pilot every answer with content of the round, hosted models' answers included)? Is the order drawn by seed and independent of labels and verdicts? Does the guard ever see a label?
5. **Analysis rows.** Do `guard_accuracy` and `_guard_forms` give the two forms of Section 9.4 for each guard, with not delivered and `context_overflow` counted by class and scored as no flag, unknown labels in no class, and the answers of related models (developer `meta` for Llama Guard 3: models 4, 6, 20; `ibm` for Granite Guardian: model 16) reported apart? Do any of these rows enter a quantity of Sections 2.3 or 9.5, a test or a sentence of Section 2.4?
6. **Texts.** Are Sections 8.5 (D28), 11.8, 14.2 to 14.4, 17.1, 19.1, the registration summary and PI_DECISIONS (D7, D28, D29) consistent with each other and with the code? In particular: is the move of the D7 reading to the freeze stated everywhere it is a condition, and does the new row of Section 14.3 keep the rule that no change follows an estimate of a presentation effect?
7. **Tests.** Would `tests/test_guards_v23.py` and the guard steps of `tests/test_e2e_v23.py` fail if the role of the last instruction were *User*, if `truncate` were dropped, if the digest check were removed, if an overflow were retried, if non-valid statuses were left out of the accuracy rows, or if answer text reached the public log?
8. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions and actions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly whether any critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the eight sections above, then a short list of what you could not check. Keep it under about 900 words.
