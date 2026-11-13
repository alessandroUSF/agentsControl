# Fresh reading, round 1 (12 November 2026)

Two readers, each a new session with no history, no memory and no access to the repository:

- Claude Opus 5.5 through Claude Code (`claude -p --model opus --effort xhigh`, no tools, no setting sources, no MCP
  servers, no saved session, a one-line system prompt). Started 20:55:55, ended 21:02:23.
- GPT-6.1 Sol through Codex (`codex exec -m gpt-6.1-sol`, reasoning effort xhigh, read-only sandbox, web search off,
  apps and memories off, user configuration ignored), in an empty folder. Started 20:55:55, ended 21:08:19.

Both received the same input on standard input: the request below, then the registration summary
(`docs/REGISTRATION_v2.3.md`) and the full protocol (`docs/STUDY_PROTOCOL_v2.3.md`) as they stood at that time. The
SHA-256 of the two documents and of the whole input are in `inputs.sha256`.

Request:

> I want to evaluate this study. Below is its full protocol, in two documents: a short registration summary and the
> full protocol. What is your opinion of it? Is it ready to be carried out as written? If not, what must change first?

The answers are stored as returned: `claude_opus_5.5_answer.md` and `gpt_6.1_sol_answer.md`. They are claims to
check, not instructions. What was taken up is recorded in Section 17.1 of the protocol.
