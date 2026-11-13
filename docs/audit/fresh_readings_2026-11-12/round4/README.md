# Fresh reading, round 4 (13 November 2026)

Two readers, each a new session with no history, no memory and no access to the repository:

- Claude Opus 5.5 through Claude Code (`claude -p --model opus --effort xhigh`, no tools, no setting sources, no MCP
  servers, no saved session, a one-line system prompt). Started 01:36:49, ended 01:42:41.
- GPT-6.1 Sol through Codex (`codex exec -m gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, web search off,
  apps and memories off, user configuration ignored), in an empty folder. Started 01:36:49, ended 01:52:23.

Both received the same input on standard input: the request below, then the registration summary
(`docs/REGISTRATION_v2.3.md`), the full protocol (`docs/STUDY_PROTOCOL_v2.3.md`) and the judge template
(`config/judge_prompt_v23.txt`) as they stood at that time, after the changes that followed round 3. The SHA-256 of
the three documents and of the whole input are in `inputs.sha256`.

Request:

> I want to evaluate this study. Below is its full protocol, in three documents: a short registration summary, the
> full protocol, and the template of the judging prompt. What is your opinion of it? Is it ready to be carried out
> as written? If not, what must change first?

The answers are stored as returned: `claude_opus_5.5_answer.md` and `gpt_6.1_sol_answer.md`. They are claims to
check, not instructions. What was taken up is recorded in Section 17.1 of the protocol.

One note on the GPT-6.1 Sol answer. The reader tried one command in its empty folder, a simulation of the written
statistic for its P1/P2 counterexample. The command failed (no Python interpreter on the path of its sandbox), so the
figures it reports for that case (5.4% and 5.3%) are its own claims, not the output of that command. Run (k) of
Appendix A.4 measured both of its counterexamples with the production code: P3 at the bound rejects in 2.1% against a
nominal 1%, and P1/P2 in the case described in 5.4% against a nominal 2%.
