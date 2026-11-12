# Consolidation of the four audits of STUDY_PROTOCOL_v2 (8 November 2026)

The four reviewers worked independently. None saw the design conversation or another reviewer's report.

| Reviewer | Model | Focus | Literature search |
|---|---|---|---|
| A | Claude Opus 5.5 (subagent) | design, measurement, statistics | yes (limited) |
| B | Claude Opus 5.5 (subagent) | AI safety, novelty, ethics, publishability | yes |
| C | GPT-6, ChatGPT "Pro" | both | yes |
| D | GPT-6.1 Sol, Codex "ultra" | both | no (network banned) |

Claims were checked against the code, the data and primary sources (`2026-11-08_verification_notes.md`). One citation from C ("Mu, September 2026") could not be found and is not used.

## Overall verdict
**All four agree.** The core idea is publishable: every respondent is also a judge, with a blind human gold set. As written, the protocol needs substantial revision before it is frozen. No new data is needed for the fixes.

## Convergent findings (raised by 3–4 reviewers): adopt
1. **Reference standard (A, B, C, D).** One annotator who is also the PI is the first thing reviewers will attack. Fixes:
   - independent second annotation with adjudication, on all harmful-prompt items and a stratified share of the rest;
   - rubric edge cases developed on a pilot outside the gold set;
   - the re-label kept, but reported as repeatability, not as a ceiling on agreement.

   B, C and D: this is the single highest-value change.
2. **Harmful positives (A, B, C, D).**
   - "Answers to harmful prompts" are not "harmful answers". Size the gold set on gold `harmful_content = yes`.
   - The exact bound needs ≥ 72 positives with 0 misses (two-sided), or ≥ 110 with 1 miss. Target ≥ 110 genuine positives, by oversampling refusal-removed answers, with recorded inclusion probabilities.
   - Use a confidence-bound eligibility rule, and pre-specify a fallback if nothing qualifies.
3. **Separate endpoints (A, B, C, D).**
   - Behaviour (full compliance / partial refusal / full refusal) and harmful content are separate outcomes. A harmful answer stays harmful with a refusal or a disclaimer.
   - Fix the "missed harmful" definition, which currently penalises a correct "partial refusal + harmful" verdict.
   - Map harm to a published hazard taxonomy and freeze a decision tree with examples.
   - Distinguish inability, empty answers, truncation and provider blocks.
4. **RQ2 specification (A, B, C, D).**
   - The self effect is an observational association within this panel, not causal preference, recognition or collusion.
   - Primary model: judge and item fixed effects, plus judge × stratum terms (A's confound). The mixed model is a sensitivity analysis.
   - Leniency and strictness are reported separately.
   - Balance self-items across judges (B).
   - No within-item permutation test (A, C, D); use a model-based null.
   - Code the relation as self / close (abliterated build and its base; the Dolphin line) / same developer / unrelated.
5. **Instrument validation (A, C, D).**
   - Selection, jury construction, recusal replacements and eligibility all happen inside the training folds.
   - Folds are grouped by base prompt, with all framings and respondents together.
   - The locked final instrument is checked on an untouched holdout (D).
   - Error rates are corrected per stratum and per endpoint.
   - Between-model contrasts (H3) use one contrast-neutral instrument (A).
   - McNemar on instrument labels is not a test of the true difference.
6. **Fully specified confirmatory tests (A, B, C, D).**
   - One estimand, one statistic and one p-value per test.
   - T2 becomes exploratory: about 14 judges need ρ ≈ 0.69 for 80% power (D), and the scores were measured at the wrong settings.
   - T3 becomes an equivalence or non-inferiority test.
   - T4 becomes one pooled test on the abliterated pairs only, with a non-inferiority margin. Dolphin 3 is trained from the base model, so it is descriptive only.
   - H1 gets confidence-bound decision rules. H3's "almost none" gets a number.
   - The power statement becomes 7–10 points, by simulation.
7. **Freeze and interim (A, C, D).**
   - Before any judging or labeling, freeze:
     - the own prompts, framings and expected labels;
     - the rubric and the harm definition;
     - the judge prompt, parser, settings and seeds;
     - the relation matrix;
     - the G2 sampler and folds;
     - the analysis scripts, run on synthetic labels.
   - Stage 1 is descriptive.
   - The annotator labels before seeing any judge result.
   - Hash the sealed outputs.
   - Publish a timestamped amendment that keeps v1 and the superseded amendment.
8. **Code (A, B, C, D; all confirmed):**
   - harmful-flag arbitration;
   - same full text for judges and humans;
   - boolean parsing;
   - fixed retry and invalid-as-error;
   - no dropped items;
   - resume keys with prompt and config hashes;
   - the Venice routing rule;
   - an `AC_` check for compatible APIs;
   - a harmful column in the sheet;
   - item shuffle;
   - a keyword-baseline mapping;
   - digests, quantization and templates logged;
   - one output regime for all judges (B);
   - a higher output cap.
9. **Purpose-built safety classifiers as baselines (A, B, C, D).** Use each through its native interface. Candidates:
   - WildGuard 7B;
   - Qwen3Guard;
   - Llama Guard 3;
   - gpt-oss-safeguard-20b, which resisted style wrappers in 2026 work;
   - the OpenAI moderation endpoint.
10. **Framing (A, B, C, D).**
    - AI control is motivation, not an evaluated outcome. Remove "precondition" language and "first".
    - Quote Ward et al. accurately.
    - Cite the safety-judge literature: HarmBench, StrongREJECT, WildGuard, SORRY-Bench, Llama Guard, Eiras 2025, Panfilov 2025, Goel 2025, Li 2026 and Khullar 2026, plus the 2026 judge meta-evaluations found during verification.
11. **Governance (B, C, D).**
    - Document dated provider terms, retention and zero-data-retention settings, and no logging or training on OpenRouter.
    - Get a USF determination before a second annotator starts, with a welfare protocol.
    - Gated release of the gold set to researchers, with content-based release review.
    - Disclose blind spots to judge and guard developers.
    - Research keys and a successful pilot do not by themselves establish permission.
12. **Venue (B, C, D).** A safety or evaluation workshop first; TMLR or ACL/EMNLP Findings after stronger validation.

## Reviewer-specific points
- **B: the 2×2 design.** Author (self vs other) × presentation (blind vs in-context, with the answer in the judge's own earlier turn). This extends Khullar et al. (2026) from coding and tool use to refusal and harm labels, and is the clearest novelty lever.
  - C and D did not know Khullar (D had no network). Both stress that self-judging accuracy is not control safety, which is consistent with B's framing.
- **A and B: frontier self-leniency on harmful content is not identified,** because commercial models never answer harmful prompts. Decision for the PI.
- **B: add judge-only base models** (Mistral 7B and Mistral Small 24B) to pair Dolphin Mistral and Venice. *Not adopted:* both are fine-tuned from base checkpoints, so they would not be clean pairs.
- **B: frontier models also answer the G2 prompts. Not adopted:** it conflicts with the PI's conditional-frontier rule (8 November). If the rule triggers, revisit.
- **B: add a Google respondent. Not adopted:** it would break the selection rules; kept as a limitation.
- **C: "even if that means fewer models"; B: RQ4 to an appendix.** A scope decision for the PI.
- **D: provenance.** The snapshot does not contain the Ollama download counts used for the uncensored tier. Add the saved search pages to the snapshot, plus a dated exclusion ledger (LFM2.5-2.6B has no official build). A model's runtime fit in 6 GB must be tested, not inferred from file size.
- **A: design weights,** with formulas (R2) and decision rules (R4); adopt as written.

## Disagreements and resolution
- **Fixed vs mixed effects for T1.**
  - *Positions:* C and D want fixed effects; A wants a mixed model with judge × stratum.
  - *Resolution:* the primary model uses fixed judge, item and judge × stratum effects; the mixed model is a sensitivity analysis.
- **CV alone vs CV plus holdout.**
  - *Positions:* D wants an untouched holdout; A and C accept CV with fold-internal selection.
  - *Resolution:* use grouped nested CV for the comparisons, and a holdout for the locked instrument if the gold budget allows. That is a PI decision on labeling time.
- **Venue.**
  - *Positions:* B points to TMLR; C and D to a workshop first.
  - *Resolution:* workshop first.

## PI decisions needed
1. **Scope and headline.** RQ2 as a 2×2, plus RQ3c, as the headline; RQ1 in support; RQ4, H2 and H3 secondary.
2. **Harmful benchmark prompts to commercial respondents**, through research keys.
3. **Second annotator.**
4. **Guard baselines,** including downloads.
5. **Labeling budget.** It depends on decisions 1–3 and on the holdout.
6. **OSF registration.**
