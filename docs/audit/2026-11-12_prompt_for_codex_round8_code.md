# Review round 8: check of the corrections after review round 7 (code of protocol v2.3)

Round 7 (`docs/audit/2026-11-12_reviewer_round7_codex_gpt61sol.md`) found no remaining critical point. It found one major point (F3: a recorded availability answer was bought again when the check stopped after its ledger line) and minor gaps in the tests. The author's response (`docs/audit/2026-11-12_round7_author_response.md`) lists the corrections. This round checks them and gives the verdict. It is not a new full review.

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

- `docs/audit/2026-11-12_reviewer_round7_codex_gpt61sol.md`: your report of round 7.
- `docs/audit/2026-11-12_round7_author_response.md`: the corrections, point by point.
- `review_aids/diff_since_round7.diff`: every change to the code, the configuration, the tests and the protocol since the copy you reviewed in round 7. Start here.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/PI_DECISIONS.md`: the protocol and the decisions as they now stand.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-12.txt`: the output of all eleven test files with the code under review.
- `review_aids/xref_check.txt`: the cross-reference check of the protocol.

## Task

1. **F3.** Is it resolved? Walk through the availability check again: a crash before the record, between the record and the ledger line, after the ledger line, during a reconciliation, and a check run again the same day. Does any case buy a recorded answer again, lose a payment, or give fact 3 from an answer the text does not allow (another day, configuration or test prompt, or a call that was never settled)?
2. **The minor points of round 7.** Do the new and changed tests check what their names claim, and would they fail if the correction they cover were undone? Two older availability tests changed their expectations because a same-day check now reuses recorded answers; judge whether the change follows Section 12.5.
3. **New problems.** Did the corrections introduce a defect or leave the text and the code apart?
4. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions? List anything that must still change, ranked critical, major or minor, each with `file:line` and a concrete fix. Say explicitly if no critical or major point remains.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the four sections above, then a short list of what you could not check. Keep it under about 1,200 words.
