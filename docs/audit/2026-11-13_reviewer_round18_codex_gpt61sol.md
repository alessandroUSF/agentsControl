Conflict: I am commercial-panel model 11, developed by OpenAI. Guard comparisons bear on assessments involving OpenAI judges 3, 9 and 11; the isolation finding also concerns their pilot answers.

## 1. Prompt formats

Both builders classify the **response**.

Llama uses `User` then `Agent`, names `Agent` in both instructions, includes S1–S14 and one explicit BOS, strips surrounding message whitespace, and ends at the assistant header without a newline. The reproduced tokenizer template differs only by the documented omission of its leading space before BOS. That could affect tokenization; no classification-target or parser discrepancy follows from it. [Meta’s format](https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/llama-guard-3) supports the selected roles and structure.

Granite matches IBM’s assistant-response `harm` branch, preserves message whitespace, adds no BOS, and ends with `<|end_of_text|>\n` followed by the assistant header, without a trailing newline. [IBM’s tokenizer template](https://huggingface.co/ibm-granite/granite-guardian-3.0-8b/blob/main/tokenizer_config.json) confirms this.

`raw: true` bypasses Ollama’s template, as its [API documentation](https://docs.ollama.com/api/generate) specifies.

## 2. Parsing and statuses

The implementation matches Section 11.8:

- Llama’s stripped first line decides; missing or unknown categories do not cancel `unsafe`.
- Granite requires the whole stripped output to equal `Yes` or `No`, ignoring case.
- Off-format output and overflow are final, without retries.
- Transient failures receive three retries after 10/30/90 seconds, then remain pending; five consecutive pending calls stop that guard.

Non-final attempts have no usable flag. Resumption skips final calls, and analysis selects the first final record, ignoring later finals.

## 3. Identity and isolation

Every selected guard’s digest and Ollama version are checked before any classification call; a mismatch aborts the session.

Local-only enforcement is incomplete: the URL-prefix check accepts non-local lookalike hosts (M1 below). Matching remote identity responses would allow classification requests there.

The public logs contain metadata and hashes, without request/answer text, guard output, categories or flags. Console output and pilot reports likewise disclose no such content. Outputs, flags and error bodies stay in private records.

## 4. What is classified

Given complete answer inputs, label mode selects every sample answer, including unknown-label cases: 567 per guard in the supplied end-to-end run.

Pilot mode selects every content-bearing answer on the round’s harmful, safe and API prompt identifiers, including hosted and commercial answers. Missing inputs and answers without content are counted.

Ordering hashes the seed, guard identifier and answer identifier; labels and verdicts do not enter it. Prompts contain only the request and answer, never labels.

## 5. Analysis rows

Both Section 9.4 forms are implemented: unweighted reference-set rates with effective-number intervals, and sampling-weighted frame rates with cluster intervals.

`not_delivered` and `context_overflow` remain in class denominators, score zero, and are counted separately by class. Unknown labels enter neither class; missing final records are counted without scoring.

Related answers are separated correctly: G1 `[4,6,20]`, G2 `[16]`. Guard rows feed no Section 2.3 or 9.5 quantity, registered test, or Section 2.4 sentence.

## 6. Texts

D28 and D29 agree with their protocol descriptions and implementation. Section 17.1 records adopted suggestions, matters deferred to the freeze, and the rejected presentation-disagreement pilot measure.

Section 14.3 explicitly preserves the prohibition on changes following a presentation-effect estimate.

D7’s move is recorded in Sections 14.2, 14.4 and 17.1 and PI_DECISIONS, but residual pilot-registration deadlines remain in Section 19.1 and the registration summary (m1).

## 7. Tests

Static inspection indicates the combined suite would catch every named mutation:

| Mutation | Focused test |
|---|---|
| Last instruction says `User` | `t_prompt_formats` |
| Drop `truncate` | `t_prompt_formats` |
| Remove digest comparison | `t_digest_mismatch_stops` |
| Retry overflow | `t_context_overflow` |
| Exclude non-valid accuracy statuses | `t_analysis_rows` |
| Put answer text in public logs | `t_nothing_printed` |

End-to-end steps additionally check coverage, reporting and analysis integration. Their stubs bypass the real transport, so they cannot independently establish all wire-level properties. The lookalike-host bypass is untested.

The supplied log reports all thirteen test files passing, including eight guard tests and the end-to-end run.

## 8. Verdict

**Not ready yet: one major point remains; no critical point was found.**

1. **Major M1 — incomplete local-server boundary.** [src/run_guards_v23.py:221](src/run_guards_v23.py:221), using [src/providers.py:93](src/providers.py:93). `http://localhost.example.org:11434` passes the prefix predicate. Replace it with parsed, exact loopback-host validation, apply validation before identity requests, and prevent proxies or redirects from bypassing it. Add offline rejection tests.

2. **Minor m1 — incomplete D7 text update.** [docs/STUDY_PROTOCOL_v2.3.md:1665](docs/STUDY_PROTOCOL_v2.3.md:1665) and [docs/REGISTRATION_v2.3.md:243](docs/REGISTRATION_v2.3.md:243). Replace the residual “before the pilot registration” requirements with freeze deadlines. Also add D7-driven Sections 8/9 changes to the summary’s allowed-change list at line 240.

**Could not check**

- No execution, mutation runs or live identity/BOS checks were performed. Meta’s gated tokenizer original was inaccessible; its public reproduction and official format were compared.
- Author verification: run `python -I -X utf8 tests/test_guards_v23.py` and `python -I -X utf8 tests/test_e2e_v23.py`; expect eight guard passes, zero failures, and an end-to-end PASS.
- Offline M1 reproduction:

```bash
python -I -c "import sys;sys.path.insert(0,'src');import providers;print(providers.is_remote({'provider':'ollama','base_url':'http://localhost.example.org:11434'}))"
```

Expected currently: `False`; corrected predicate: `True`.