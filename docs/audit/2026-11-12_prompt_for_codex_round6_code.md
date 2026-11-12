# Review round 6: check of the corrections after review round 5 (code of protocol v2.3)

Round 5 (`docs/audit/2026-11-12_reviewer_round5_codex_gpt61sol.md`) reviewed the code of protocol v2.3 and advised against registering the pilot with it: two critical points (spending under crashes and threads), ten major and three minor ones. The author's response (`docs/audit/2026-11-12_round5_author_response.md`) lists a correction for each, with the files, the protocol sections and the tests. This round checks those corrections. It is not a new full review.

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

- `docs/audit/2026-11-12_reviewer_round5_codex_gpt61sol.md`: your report of round 5.
- `docs/audit/2026-11-12_round5_author_response.md`: the corrections, point by point.
- `review_aids/diff_since_round5.diff`: every change to the code, the configuration, the tests and the protocol since the copy you reviewed in round 5. Start here.
- `docs/STUDY_PROTOCOL_v2.3.md`, `docs/PI_DECISIONS.md`: the protocol and the decisions as they now stand.
- Code: `src/`, `scripts/`, `analysis/`, `config/`. Tests: `tests/`.
- `review_aids/offline_tests_2026-11-12.txt`: the output of all eleven test files with the code under review.
- `review_aids/xref_check.txt`: the cross-reference check of the protocol.

## Task

1. **Each point of round 5.** For every critical, major and minor point of your report, and for the scope note on the bounds over calls not attempted: is it resolved, partly resolved or not resolved? Give the evidence (`file:line`) and, if not resolved, what is still wrong.
   - The domain degrees of freedom were answered by changing the text, not the code (prompts with N_p ≠ 0). Judge whether the text and the code now agree, and whether the reason given holds. Amendment D19 stays the PI's decision; do not decide it.
   - For spending: walk through the crash windows again (before the reservation line, between it and the send, between the send and the private record, between the record and the ledger line) for answers, verdicts and the availability check, and the thread interleavings of reservation and settlement. Say whether any window still pays twice, loses a payment, keeps two verdicts for one call, or resends a call whose answer was recorded.
2. **New problems.** Did the corrections introduce a defect, break a behaviour that worked in round 5, or leave the text and the code apart? Look in particular at the challenge pairs of block 5 (counts per part and holds), the repricing file (prices, scenarios, holds, cuts), the pilot planning input, the agreement and challenge-change intervals, and the protocol patch.
3. **Tests.** Do the new tests check what their names claim? Would they fail if the correction were undone?
4. **Verdict.** Is the code ready for the pilot registration, apart from the PI's decisions? List what must still change, ranked critical, major or minor, each with `file:line` and a concrete fix.

Do not propose a new design. Report a design point only if the code cannot implement the text as written.

## Output

Markdown with the four sections above, then a short list of what you could not check. Keep it under about 2,000 words.
