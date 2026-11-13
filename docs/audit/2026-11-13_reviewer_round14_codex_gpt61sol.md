## 1. Correctness

**D24 and D25 work in the implemented paths. D26 remains unimplemented.**

**Conflict disclosure:** I am commercial-panel model 11, developed by OpenAI. D25’s shared class handling applies to OpenAI models 3, 9 and 11. The findings concerning local caps, sentinel measurements and model 22 do not specifically concern OpenAI models.

- **D23:** No inference change was required or introduced.
- **D25:** The template’s rubric section equals Part A after the specified trailing-newline removal. Both contain **7,943 characters**. The template SHA-256 is `6bc0bb6232a3465ae5a4d34f6f4c574965059a2f7c73aa2b7f680f8fb812ada4`, matching the recorded value and measurement log. The builder and instruction include all four classes.
- The runner’s parser and analysis verdict reader accept `clarification`. Harmful-prompt flags depend on `harmful_content`; safe-prompt flags include only the two refusal classes. The pilot report’s permitted blind harm counts remain label-independent. The label tools already accept the fourth behaviour class, and the join and lock preserve it.
- **D24:** `judge_cfg()` uses each judge’s cap; the runner passes it through to Ollama’s `num_predict`, including retries and longer-context calls. Models 16 and 17 receive 2,000 tokens, or 4,000 when doubled. Context fit reserves that same doubled cap. Pilot cap counts use recorded stop reasons, without a hard-coded 600-token threshold.
- Section 11.3’s arithmetic holds: **9,300 − 1,200 + 4,000 = 12,100**, leaving approximately **188 tokens** within 12,288. This validates the stated planning arithmetic, not actual tokenizer fit.
- The D24 log supports the reported ranges, 24 valid verdicts and five model-17 outputs above 600. Its median calculation needs correction below.

## 2. The tests

I counted **186 declared tests and 186 named passing results**. The supplied twelfth-file synthetic end-to-end run also passes. These are supplied results; I did not execute them.

The changed parser assertions would fail if fourth-class acceptance or the instruction’s fourth class were removed. The synthetic analysis change preserves the existing draws on its safe-label branch. Its independent expected flags, checked by `test_canonical_verdicts` and the safe-side comparisons, would detect treating clarification as refusal.

The cap assertions catch reverting `judge_cfg()` to the common cap under the current configuration. Two protections are missing:

- They compare caps with configuration values without asserting that both overrides equal **2,000**.
- `t_context_fit` never checks the numeric margin or a case where reserving 4,000 changes the fit decision. Reverting its cap calculation to 1,200 would still satisfy its current assertions.

No supplied test covers D26.

## 3. Consistency

The repriced figures agree with the manifest: **US$57.54 expected**, **US$102.30 pessimistic**, cuts **US$1.68 / 4.85 / 5.66 / 2.43**, and **US$21.70** beneath the freeze ceiling. The commercial and hosted subtotals, provider totals and D1 costs also agree. Independently summing the holds gives US$102.299861, rounding to US$102.30.

The holds’ manifest hash matches the original CRLF serialization exactly. Its difference from the LF review copy is explained by the declared normalization.

The supplied cross-reference check reports **798 references, zero dangling**. Remaining inconsistencies are the labeller-only wording, doubled-cap wording and median figures listed below. Historical references to the former three-class scheme are appropriately historical.

## 4. Fingerprints

**No fingerprint input for stored runs (a)–(g) changed in the supplied complete diff.**

The registered, label and safe fingerprint constructors hash inference, DGP, simulation, frame, yoking and label-sampling modules as applicable. Those modules and their panel/frame/control inputs are unchanged.

`analysis/crossed_v23.py` changed only docstrings and is outside these fingerprints. The control-assignment file still hashes to `b18714d2ccbf3c4b047d2f95bbf049eef991733684ce47e01675dec3fb7ada41`. This confirms unchanged inputs relative to round 13, without recomputing every stored row fingerprint.

## 5. Verdict

**The complete implementation is not ready for pilot registration: one major completeness point remains. No critical point remains.**

1. **Major — implement D26’s check and reporting.** [src/run_models.py:1203](E:/claude/_audit_copy/agentsControl_r25_round14_code/src/run_models.py:1203), [scripts/pilot_report_v23.py:407](E:/claude/_audit_copy/agentsControl_r25_round14_code/scripts/pilot_report_v23.py:407). Neither the pilot path nor another supplied command implements the sentinel/tokenizer comparison required by Section 13.2; the report has no input or fields for its two counts. Add the specified production-settings call and ledger accounting before round-1 responses, record the tokenizer comparison, and include both counts in JSON and Markdown reports. Verify with a stub provider. This is missing implementation, separate from PI approval or executing the paid call.

2. **Minor — correct rule 3’s local-cap values.** [docs/STUDY_PROTOCOL_v2.3.md:1140](E:/claude/_audit_copy/agentsControl_r25_round14_code/docs/STUDY_PROTOCOL_v2.3.md:1140), [docs/REGISTRATION_v2.3.md:233](E:/claude/_audit_copy/agentsControl_r25_round14_code/docs/REGISTRATION_v2.3.md:233). State 1,200 for ordinary local judges and **4,000 for models 16 and 17**. Keep the current code.

3. **Minor — remove obsolete labeller-only classification.** [docs/STUDY_PROTOCOL_v2.3.md:641](E:/claude/_audit_copy/agentsControl_r25_round14_code/docs/STUDY_PROTOCOL_v2.3.md:641). Remove `clarification` from the parenthetical list of fields exclusive to labellers; it belongs to shared Part A.1.

4. **Minor — correct the medians.** [scripts/measure_judge_reasoning_v23.py:174](E:/claude/_audit_copy/agentsControl_r25_round14_code/scripts/measure_judge_reasoning_v23.py:174) selects the upper middle observation. Use `statistics.median(outs)`: the supplied rows give **508.5 for model 17** and **64.5 for model 16**. Update the summary and repeated protocol/D24 figure from existing rows; no model rerun is needed.

5. **Minor — strengthen cap regression checks.** [tests/test_judges_v23.py:332](E:/claude/_audit_copy/agentsControl_r25_round14_code/tests/test_judges_v23.py:332), [tests/test_judges_v23.py:1112](E:/claude/_audit_copy/agentsControl_r25_round14_code/tests/test_judges_v23.py:1112). Assert the two 2,000-token overrides and add a stub returning **9,000 prompt tokens**. Expected margins: **−712, fit false** for models 16/17; **2,088, fit true** for an ordinary local judge. Author command after extending the checks: `python -I -X utf8 tests/test_judges_v23.py t_template_layouts t_context_fit`; expect both PASS and exit 0.

**Could not check:**

- Python execution, actual mutation runs or complete fingerprint recomputation.
- Live tokenizer/context fit or provider behaviour.
- Private raw sentinel outputs, their hashes or exact reasoning-token boundaries.

No files were changed and no model/API calls were made.