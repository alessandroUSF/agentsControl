## 1. The pilot repeat calls

With a settled answer pool, the plan adds 20 calls per local judge per round: ten own harmful-prompt answers with content, both presentations, after ordinary calls. Existing keys, pairs, presentation order, API calls and paid holds remain unchanged. Block close includes repeats; the supplied two-round test counts **5,840 final calls**.

The report correctly matches originals by replacing only the part component of the key, takes the first final record, and treats invalid verdicts as no delivered flag. Repeatability exports aggregate difference counts, without individual flags, outputs or hashes. Registered blind-rate diagnostics remain.

Resume safety has exceptions below: growing answer pools can change the selected ten, and pending originals do not prevent repeats.

**Conflict disclosure:** I am commercial-panel model 11, developed by OpenAI. The local-repeat findings concern other developers’ models. Shared template and statistical-reporting assessments also bear on OpenAI models 3, 9 and 11.

## 2. The judge template

The RUBRIC section matches Part A byte for byte, excluding trailing blank lines. Its length is **7,878 characters**. The template SHA-256 is exactly D27’s `d0daff82…7dcb82`.

No study-identifying phrase remains in the sections sent to judges. ABOUT still mentions the study, but `messages()` never sends it.

The cost statement is honest as a planning approximation: it explicitly retains the assumptions for 7,943 characters, 65 characters more than the current rubric. It does not claim measured tokenizer counts.

## 3. Run (k)

The added rows use production `SR.draw`, `cluster_ratio`, registered tests and `DN.decide`. Existing row names, parameters and named streams are unchanged; the merge retains stored rows rather than recomputing them.

`--add-to` checks seed and threshold, rejects incompatible replication counts before writing, preserves Parts 1–2, and orders Part 3 by the declared grid. The replication check happens after computing missing rows, which wastes work on incompatible input but does not write a mixed result.

The JSON contains **28 unique rows**, each with 2,000 replications and no unreached calibration target. All 19 added log rows agree with it. Section 8.1 and Appendix A.4’s added figures match, including P1’s 0%/3.6% and P2’s 28.3%/81.7%. The summary has one numerical overstatement below.

## 4. The texts

The five adopted points are recorded consistently in substance: external-command restrictions, removal of study cues, local pilot repeats, worksheet refusal definitions and timing, and reporting test-execution shares.

The two unadopted points remain unimplemented: individual-labeller results add no gate, and model 17 retains the common local respondent cap. The worksheet script’s new guidance agrees with Part A.1 and Section 7.3.

Some older pilot wording and call totals still need reconciliation.

## 5. Verdict

**No critical or major point remains.** Complete these minor corrections before pilot registration:

1. **Minor — repeat selection and ordering on resume.** `src/plan_v23.py:450`; `src/run_judges_v23.py:433`. Selection is recalculated from currently available answers. Start with only the ten highest-hash harmful answers, finish their repeats, then supply the other forty: a disjoint ten can be selected, producing **40 repeat calls**. Separately, isolated pending ordinary calls can be passed before repeats begin. Defer repeat selection/sending until the round’s answer pool is settled and ordinary calls are final; report any content shortage explicitly.

2. **Minor — output-only changes do not trigger investigation.** `scripts/pilot_report_v23.py:136`; `tests/test_judges_v23.py:918`. `investigate` ignores `output_differs`, contrary to D27 and Section 11.6. Include it and replace the test assertion that currently enshrines the omission. An unchanged status and flag with different output must trigger investigation. Also distinguish incomplete repeat coverage from “no difference” at line 494.

3. **Minor — stale local call totals.** `docs/STUDY_PROTOCOL_v2.3.md:1009`. Change each local pilot round from 200 to **220**, the local column total from 2,617 to **2,657**, and the per-round local total at line 1015 from 2,000 to **2,200**.

4. **Minor — document the repeatability exception.** `docs/STUDY_PROTOCOL_v2.3.md:1117`; `docs/REGISTRATION_v2.3.md:227`. “Statuses, tokens and costs only” excludes D27’s in-context repeatability comparisons. Explicitly permit their aggregate difference counts while retaining the prohibition on presentation-effect estimates.

5. **Minor — qualify the summary’s 5.4% maximum.** `docs/REGISTRATION_v2.3.md:130`. Across Part 2, the maximum without D20 is **8.653%**, versus **5.4065%** with it. State 8.7%/5.4%, or restrict “with or without” to the dense scenarios, as Appendix A.4 does.

After adding the resume, pending-original and output-only fixtures, run:

```text
python -I -X utf8 tests/test_judges_v23.py t_pilot_both_rounds_and_close t_pilot_report t_template_without_study_cues
```

Expected: all three PASS, zero failures, exit 0. The supplied complete output already contains 189 passing tests plus the passing synthetic end-to-end run.

**Could not check:**

- Python execution or live provider behavior; no model/API calls were made.
- Independent reproduction of the original nine simulation rows. Author run: `python -I analysis/sim_v23_tails.py --out round16_verify.json`; expect matching numerical results, excluding `seconds`.
- No files were changed.