# Corrections after review round 18 (guard classifiers of decision D29; texts of D7, D28 and D29)

- **Report answered:** `docs/audit/2026-11-13_reviewer_round18_codex_gpt61sol.md` (GPT-6.1 Sol, 13 November 2026). Request: `docs/audit/2026-11-13_prompt_for_codex_round18_code.md`.
- **Verdict of the report:** no critical point; one major and one minor point. The prompt formats classify the response and match the published formats; parsing, statuses, retries, the first final record, the digest and version stop, the items classified, the seeded order and the analysis rows match Section 11.8; no answer text, output or flag reaches a public log, the console or the pilot report; the tests would catch every mutation named in the request.
- **No paid call, no answer and no verdict** was made for these corrections. The tests use stubs and one server on the loopback address. `src/prepare_data.py` was left out of the reviewed copy; nothing in the round depends on it.

## Major point

| Point of round 18 | Correction | Where |
|---|---|---|
| M1. The test of a local server was a prefix test, so `http://localhost.example.org:11434` counted as local; the identity requests were made before it; proxies and redirects could carry a local call elsewhere. The same test also decides which models receive prompts expected to be refused (`allowed`) | `is_local_url`: plain http, host exactly `localhost`, `127.0.0.1` or `::1`, no user information, a valid port. `is_remote` uses it for every adapter. Every call to the local server (the Ollama adapter of the judges and respondents, the identity and memory requests, the guard runner) goes through `local_urlopen`, which refuses any other server and opens the request with no proxy (environment or system settings) and no redirect: a redirect is an error. The guard runner checks the server before the identity requests | `src/providers.py` (`is_local_url`, `_NoRedirect`, `LOCAL_OPEN`, `local_urlopen`, `is_remote`, `OllamaProvider.call`, `ollama_identity`, `ollama_vram`); `src/run_guards_v23.py` (`OllamaRaw.call`, `check_identity`) |

## Minor point

| Point of round 18 | Correction | Where |
|---|---|---|
| m1. Two deadlines of the D7 reading still named the pilot registration (Section 19.1, the registration summary), and the summary's list of changes allowed between the registrations did not name the changes that follow from that reading | Both deadlines read "before the freeze", under the rule of Section 14.3; the list names changes to Sections 8 and 9 that follow from the D7 reading, each dated with its reason | `docs/STUDY_PROTOCOL_v2.3.md` (Section 19.1, D7); `docs/REGISTRATION_v2.3.md` |

## Tests

- New test `t_local_boundary` (`tests/test_guards_v23.py`): loopback URLs are local; lookalike hosts, user information, https, a malformed port, a missing scheme and an empty URL are remote for the Ollama and the OpenAI-compatible adapters, and the prompt filter refuses them prompts expected to be refused; the guard adapter, `local_urlopen` and `ollama_identity` raise before any request; `check_identity` returns the refusal without calling the identity function; against a server on the loopback address, a redirect is an error and is not followed, and a process that starts with a proxy in its environment still reaches the local server directly.
- The test fails on each way back, checked one at a time on 13 November 2026: the prefix test restored, the proxy setting removed, the redirect handler removed, and the server check in `local_urlopen` removed.
- The stubs of the Ollama adapter in `tests/test_judges_v23.py` and of the guard adapter in `tests/test_guards_v23.py` now replace `providers.LOCAL_OPEN` instead of `urllib.request.urlopen`.
- The text of Section 11.8 states the boundary.

## After this round

The twelve offline files hold 200 declared tests, and the complete run on synthetic data passes with the guards. Section 14.2, the status lines and the registration summary record the round.
