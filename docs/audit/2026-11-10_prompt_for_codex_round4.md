# Review round 4: short targeted document check of protocol v2.3 (revised after round 3)

You reviewed protocol v2.3 in round 3 (`docs/audit/2026-11-10_reviewer_round3_codex_gpt61sol.md`). Your section 9 asked for "a short targeted document check" after revision, and said that another unrestricted redesign round is unnecessary. This is that check.

## Rules

- Read-only: do not create, modify or delete any file.
- Read only files inside the working directory. Do not open, list or search anything outside it, even where the sandbox would allow it.
- Shell: PowerShell is broken on this machine and every PowerShell command hangs. Run every command through `exec_command` with the parameter `shell` set to `C:\Program Files\Git\bin\bash.exe`. `cat`, `sed -n`, `grep`, `head`, `wc`, `diff` and `awk` work, and `awk` does arithmetic. Python and `jq` are not available in the sandbox. Read long files in parts of about 250 lines (for example `sed -n '1,250p' file`) and set `max_output_tokens` high enough that the output is not truncated. Never print a whole file of more than 1,000 lines.
- Do not run any model or API call.
- Web search is allowed only to verify a cited paper. Never put text from this folder in a query, beyond paper titles, arXiv numbers and generic topic keywords. Mark each literature statement as [verified online], [from memory] or [unsure].
- If a number needs a simulation you cannot run, specify it exactly; the author will run it.
- The folder holds no answer text, no benchmark prompt file, no label key and no secret.
- Conflict of interest: you are model 11 of the commercial panel. Say where a point you raise bears on your own developer's models.

## Files

- `docs/STUDY_PROTOCOL_v2.3.md`: the revised protocol. Appendix A is its last part.
- `docs/audit/2026-11-10_round3_author_response.md`: the author's answer to each of your round-3 findings, with section numbers.
- `review_aids/protocol_diff_round3_to_round4.diff`: unified diff between the text you reviewed in round 3 and the revised text.
- `docs/audit/2026-11-10_reviewer_round3_codex_gpt61sol.md`: your round-3 report.
- `labels/RUBRIC.md`, `docs/annotator_packet/`, `README.md`, `docs/PI_DECISIONS.md`: the other documents that changed.
- `analysis/output/`: stored simulation results and the tables of Appendix A. `review_aids/check_count_2026-11-10.txt`: the count of the checks of Appendix A.4 made by script from those files.
- `review_aids/`: offline test outputs and the cross-reference check of the revised protocol.

## Task

1. **Round-3 findings.** For R3-C1, R3-M1 to R3-M7 and R3-m1 to R3-m3: Resolved, Resolved on a condition, or Not resolved. One or two sentences each, with the section that decides it.
2. **Undeclared differences.** Are the eight differences of your section 3A now declared and handled correctly (Section 17.2)?
3. **Consistency.** Check that the revised text agrees with itself: numbers (labels, calls, costs, seeds, check counts), the branches (eleven or ten models; with or without a second annotator), the order of registration steps, the cross-references, and the statements about what code exists. Check a sample of numbers against the stored result files.
4. **New problems.** Report only problems that the revision introduced or that you missed before and that would matter for registration. Rank them critical, major or minor. Give the place and a concrete fix.
5. **Verdict.** Is the protocol, as revised, ready for the PI's decisions and for implementation of the missing code? What, if anything, must change first?

Do not propose a new design. Do not repeat points that the author response answered unless you judge the answer inadequate, and then say why.

## Output

Markdown with the five sections above, then a short list of anything you could not check. Keep it under about 2,500 words.
