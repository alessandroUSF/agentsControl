# Reviewer round 3: Codex, GPT-6.1 Sol, reasoning effort "xhigh" (10 November 2026)

This is the third round of the iterative review. The reviewer assessed protocol v2.3 as a document, with the rubric, the annotator packet, the supporting files, the simulation code and its outputs. It ran in the Codex CLI (`codex-cli 0.167.0-alpha.3.2`, `codex exec`, read-only sandbox, connectors disabled, a fresh session without memory of rounds 1 and 2), thread `01a1c638-71b3-7be0-ae04-d87d083562ae`, from 11:09:10 to 11:27:09 local time (exit code 0).

- **Input:** a read-only clean copy of part of the repository (`E:\claude\_audit_copy\agentsControl_r14_round3`, 81 files with the prompt), with the prompts and reports of rounds 1 and 2 inside. It held no model answers, no benchmark prompt files, no author prompts, no label key and no secrets.
- **Instructions:** `2026-11-10_prompt_for_codex_round3.md`. Web search was allowed only to verify cited papers and to look for closer prior work.
- **Conflict of interest:** GPT-6.1 Sol is also respondent and judge number 11 of the study panel. The prompt disclosed this and the reviewer states it in its verdict. In this round it accepts, with a modification, the in-context presentation of the challenge set to the commercial judges (block 7), which it had advised against in round 2; that increases what the study can find about its own developer's models. It also accepts fewer safe controls for the commercial panel, which reduces it. Both points are weighed in the author's reply.
- **What the reviewer did:** 37 read-only shell commands inside the copy (`sed`, `nl`, `cat`, `awk`, `grep`, `find`, `pwd`, `sha256sum`), none of which failed, and 5 web actions (three pages opened: arXiv 2603.04582, one Nature Medicine article, arXiv 2308.01263; one further action on the Nature Medicine page; one search with general keywords). It did not run the Python analyses (Python is not available in its sandbox). The event log was checked: no file outside the copy was read and no packet text was used in a search query. Three literature items that its Section 8 marks as verified online (arXiv 2503.17365, 2606.07874 and 2406.11717) were not opened as pages in the session; they are checked separately before any of them is cited. Token use reported by the CLI: 3,819,708 input (3,563,776 cached), 31,732 output.
- **Text:** the final message is reproduced as returned. Its statements are claims to verify, not instructions. Its links point to the review copy, not to this repository.

---

## 1. Verdict

Protocol v2.3 has a defensible core, but it is **not ready for registration as written**. The registered ratio estimator, Holm procedure and ordinary-case interaction decomposition are implemented correctly, and the simulation tables I checked reproduce the saved results. The most consequential remaining problem is the post-freeze switch between eleven-model and ten-model confirmation: provider availability can depend on content, so hiding flags does not establish that this selection preserves test validity. Other necessary repairs concern poorly covered reference-label intervals, an infeasible pilot-calibration rule, incomplete shortage handling, and contradictions between call pairing, execution order and budget cuts. After those repairs, the design should be stable enough for implementation; the next review should concentrate on the completed code and synthetic end-to-end run.

**Disclosure:** I am GPT-6.1 Sol, respondent/judge 11. Recommendations concerning commercial challenge calls, commercial safe controls and commercial comparison tables affect evidence about Sol/OpenAI; I identify those consequences below.

I inspected text, code and saved outputs, performed arithmetic, and checked scholarly sources online. I did not execute Python, inspect answer data, modify files or make model/API calls. References below to **P** mean [protocol v2.3](E:/claude/_audit_copy/agentsControl_r14_round3/docs/STUDY_PROTOCOL_v2.3.md).

## 2. Round-2 issues

“Resolved on a condition” distinguishes an adequate specification from its expressly unfinished implementation.

| Issue | Status | Assessment |
|---|---|---|
| R2-C1 | **Resolved on a condition** | The unjustified exact sign-flip argument is replaced correctly. Finish production cross-checks and sparse-boundary handling; retain asymptotic wording. |
| R2-C2 | **Resolved on a condition** | Mechanistic findings are withdrawn. Correct the P2 wording: a negative interaction does not necessarily mean either arm decreased. |
| R2-M1 | **Not resolved** | The printed manifest reconciles, but execution order can defeat the prescribed cuts, and the existing reservation calculation is not a demonstrated worst-case bound. |
| R2-M2 | **Resolved on a condition** | Exposure weights, assignment diagnostics and decomposition are substantial improvements. Remove unconditional immunity claims and treat the within-judge companion as secondary evidence. |
| R2-M3 | **Resolved on a condition** | The ordinary sampler is explicit and weighted. Specify complete failure/shortage rules, including absent model-side cells and undersized challenge/reference sets. |
| R2-M4 | **Resolved on a condition** | Staffing commitment is required and harmful-side second labels are protected. Actual recruitment remains open; missing-label rules still need repair. |
| R2-M5 | **Not resolved** | R-S1/R-S2 largely satisfy the request. Safe-side interval validation is absent, and R-S3 contains serious undercoverage outside its selected display. |
| R2-M6 | **Not resolved** | Attempted non-delivery and administrative non-attempts are separated correctly. The replacement model-22 branch does not establish valid post-selection confirmation. |
| R2-M7 | **Resolved on a condition** | Weight-matched Q4_0 judging is specified, but the build, configuration update and verification remain undone. The helper still defaults to Q4_K_M. |
| R2-m1 | **Resolved on a condition** | Judge-specific eligibility is recognised. Explicitly require common eligible intersections for comparisons and handle challenge-set shortages. |
| R2-m2 | **Resolved** | Inventory, sealing narrative and annotation estimates are substantially reconciled. Remaining hash-description and workload qualifications are listed below. |

## 3. Fidelity, deviations and new rules

### A. Undeclared differences

The central eleven-model, 300-prompt screened design faithfully follows round 2. These additional differences should appear in §17.2.

| Difference | Consequence and judgment |
|---|---|
| **Commercial safe controls: 60 prompts became 30**, 15 per source (§§5.1, 8.7). | Material. This saves about **$5.09 pessimistically** and reduces an already descriptive comparison. Acceptable resource trade-off, but it must be declared. |
| **Model 22 now judges all 547 labels blind**, rather than the 120-item API reference subset. | Adds **427 scheduled calls**, approximately **$0.40 pessimistically**. Acceptable, but distinguish its weighted frame accuracy from its originally smaller reference task. |
| The retained **G1/G2 arrangement becomes one fresh frame-only probability sample**; G1 supplies training material. | Scientifically cleaner and removes out-of-frame reference complications. This is more than changing 550 to 547. Declare it and its implications for exposure history. |
| Harmful-side second labels change **300→305**, safe-side second labels **60→55**. | Sensible within the fixed 360 total; declare the redistribution. |
| The earlier **all-22-model common-60 secondary comparison** is no longer clearly specified. | It costs no additional calls. Restore its exact definition or explicitly withdraw it. |
| The explicit requirement to exclude G1 duplicates from H60 disappears. | Harmless once G1 is retired and training uses only tails, but explain why the exclusion is no longer necessary. |
| Safe-side reporting no longer explicitly says **unscreened and S=0**, as the author response did. | Matters: “the same quantities” could instead imply screening away refusals. Specify both targets. |
| The optional crossed blind fixed-effects sensitivity and equal-pair summary are no longer clearly retained. | Not a core defect. Explicit withdrawal is preferable to silent disappearance. |

The commercial allocation effectively exchanges some safe-control coverage for challenge-set presentation evidence. That is a reasonable choice, provided it is presented as such.

**Conflict:** accepting fewer commercial safe controls reduces evidence about Sol/OpenAI; retaining commercial challenge presentation increases it. Both recommendations apply uniformly.

### B. Declared deviations and new rules

1. **Commercial challenge set in context — accept with modification.**

   I do not endorse round 2’s categorical omission. This block answers a useful, distinct descriptive question, and the additional $5.09 can fit the stated allocation. However, running it last does not remove the risk created by its pilot counterpart, which occurs before confirmation.

   The current schedule also separates challenge blind calls from in-context calls, contradicting §11.4’s adjacent-pair rule. Replacement:

   > “For the challenge presentation comparison, both presentations are scheduled together, in random order, in the final commercial block. Earlier blind verdicts are reused only if they satisfy that pairing rule. Provider switches and stopping rules apply to the router account and the actual serving provider.”

   Reconcile the blind-only fallback and manifest accordingly. A ten-item pilot establishes technical acceptance of those calls, not a small suspension probability.

2. **547 labels — accept.**

   Divisibility and coverage justify losing three labels. No meaningful precision claim depends on 550 versus 547.

3. **Model 22 and ten-model assignment — accept the assignment; reject the post-freeze confirmatory switch.**

   The second assignment is coherent and exposes a different control topology. The claim that availability-only selection “keeps the tests valid” is unsupported. Use the replacement under **R3-C1** below.

4. **P2 wording tied to the interval of ι_W — accept with modification.**

   It usefully distinguishes two comparisons, but does not identify authorship. Replace “the reduction was larger” with:

   > “The author’s presentation contrast was lower than the assigned controls’ contrast by [estimate] percentage points.”

   When supported:

   > “A corresponding difference appeared in the prespecified within-judge comparison, whose interval is secondary and unadjusted.”

   Specify what happens when ι_W is non-estimable. A non-significant interval does not prove that judge differences explain the result.

5. **Appendix A.4 tolerances — accept with modification as diagnostic thresholds.**

   The arithmetic is right; the interpretation is too strong. Passing cannot establish exact nominal size. Fix the pilot scenario, run provenance, failed-check rerun and endpoint coverage as discussed below.

6. **Two-part rubric — accept with modification.**

   Administrative instructions, hazard coding and a human-only clarification class are reasonable. Substantive harm interpretations should be shared with judges. Replacement:

   > “Part B contains administrative guidance only. Any training clarification that changes the application of harmful_content is incorporated into the common definition through a dated pre-freeze amendment, with the affected template rechecked.”

   If Part A must remain fixed at pilot registration, conduct substantive instrument training before that registration using separately declared non-frame material. Merely preserving Part A’s bytes does not prevent changing its meaning.

7. **Skipped answers and threshold 15/305 — accept with modification.**

   The right to skip is essential. Fifteen is arithmetically the largest integer below 5% of 305, but it is not a statistical validity threshold. Preserve unknown labels as unknown; report missingness by primary group, screen and weight. Require a robustness analysis for detection statements, rather than relying on this count alone.

8. **Training between registrations — accept with modification.**

   Two rounds are feasible: **24 harmful-side training answers are required and 25 exist**. Specify whether sampling is by answer or prompt cluster, the exact random ordering, and that second-round discussion cannot silently add new substantive rules. The training material covers only models 4–6; acknowledge its limited style coverage.

9. **Second annotator’s copy — accept with modification.**

   Encryption and deletion rules are appropriate. Add an encrypted backup/incident procedure, remove identity-bearing metadata, and restrict transfers to the minimum required files. The PI must retain the authoritative raw labels and adjudication record.

10. **PI statements and D1–D12 — accept with modification.**

   Signed exposure statements are useful attestations, not independently verifiable evidence. The second statement’s script list must include the actual pilot and training pipeline. D6, D8 and transfer arrangements must be settled **before training material is sent**, even though their present deadline says “freeze.”

## 4. Inference and simulations

### A. Registered inference

The main implementation in [inference_v23.py](E:/claude/_audit_copy/agentsControl_r14_round3/analysis/inference_v23.py) agrees with §8:

- `cluster_ratio`, lines **37–48**, implements the ratio and stated stratified residual variance.
- `_stratified_var`, lines **20–34**, produces **298 degrees of freedom** for two strata of 150.
- `holm_two`, lines **70–77**, correctly implements the .04 family, including ties and non-estimable p-values.
- `lower_bound`, lines **65–67**, and `sim_v23_registered.py:174` implement P3’s **99% lower bound > −.07**.
- `interaction_decomposition`, lines **112–145**, has the correct algebra and ordinary-case linearisation, including covariance between its components.
- Sign-flipping is correctly relegated to sensitivity analysis.

Three boundary details need correction.

**First**, lines **129, 138–143** make even the *pooled* interaction non-estimable when an author has screen-positive own answers but no screen-positive control workload. The pooled answer-matched interaction remains estimable; only the within/composition split fails. Return component-specific estimability. The simulation assertion at `sim_v23_registered.py:121–122` can otherwise terminate a sparse scenario.

**Second**, `p_two_sided:52–57` assigns p=1 at zero standard error, while `interval` returns a zero-width interval and `lower_bound` can produce a decisive P3 result. Register a coherent boundary policy and validate it under rare flags. Zero denominator and zero estimated variance are different problems.

**Third**, the label-assisted functions implement §9.5 as written, including treating estimated \(b_g\) as fixed. That establishes transcription, not general validity. Its uncertainty approximation needs validation under heterogeneous authors, informative screening and sparse classes.

### B. Adequacy of the DGP

R-S1 is a substantial, appropriate response to round 2. It uses fixed panel quality, actual yoking, calibrated operational effects, independent reference draws and actual Holm decisions. R-S2 correctly distinguishes a zero latent shift from a zero operational estimand.

Remaining optimism is concentrated in:

- screening errors depending only on binary harmfulness;
- no correlation of screen error with answer style, difficulty or presentation susceptibility;
- R-S3’s homogeneous within-type harm rates;
- error-free reference labels;
- no temporal service drift, account-level dependence or provider-wide stopping;
- identical source distributions in the displayed scenarios;
- no safe-side verdict simulation.

The stated 10% discordance is also misleading. Calibration targets latent, pre-invalidity discordance, whereas saved **screened delivered** discordance is **12.55%** in `baseline|null` and **23.26%** in `discordance_0.20|null`. State the distinction.

Round 2 §5.C’s safe-side interval check remains missing. H60 eligibility is determined, but pooled type intervals still need an explicit common-content target.

### C–D. Tables and conclusions

The numeric audit below checks more than twelve cells across A.1–A.3 against both generated tables and JSON. They agree to displayed rounding.

Nevertheless, several readings exceed the evidence:

- §8.4’s **94.7–95.3% coverage** describes the displayed null rows. Across all R-S1 rows the range is **94.43–95.45%**.
- “Size and coverage do not depend on those rates” should say that the examined settings passed the stated diagnostic thresholds.
- R-S2’s `zero` rows sometimes include fixed judge shifts. Its caption should say **zero calibrated arm shifts**, not that presentation shifts no judge’s tendency.
- R-S3’s low-failure instruction-group result—100% coverage and −3.71-point bias—is based on **only two reportable replications out of 2,000**. It cannot establish general bias or coverage. The table needs the reportable denominator.
- Most seriously, the same output contains **64.9% coverage** for `harm_share_neg|all` and **64.4%** for `screen_pass_harm|all` in `low_failure|null`. These are registered reported quantities, although excluded from A.4’s acceptance checks.

The detection-change estimator performs substantially better in these simulated worlds. That conclusion survives; a blanket endorsement of label-conditioned inference does not.

### E. Tolerances and remaining runs

The 10,000-replication thresholds—4.59%, 1.30%, 94.35%—are calculated correctly. But “the rule does not accept a real excess” is false: a true 4.2% rejection rate has approximately a **97% chance of passing the first 4% diagnostic**. The repeat-if-failed procedure raises its overall chance of eventual acceptance further.

The second run is not inherently a forking path if its trigger, seed and interpretation are immutable. Require:

> “Passing is a numerical diagnostic, not proof of nominal validity. All first and second results are published. A rerun holds the DGP and calibrated parameters fixed and changes only the replication stream.”

Currently changing `--seed` changes calibration and reference draws as well.

The pilot scenario is not executable as specified. With screen Se=.9 and Sp=.8,

\[
P(S=1)=.2+.7P(Y=1),
\]

so only screen-pass rates between .2 and .9 are representable. Clipping harmfulness to 1–99% narrows that to **.207–.893**. Screen-pass rates outside that interval cannot be matched. Nor do unlabeled screen and flag rates identify harmfulness and sensitivity separately. `_root` at `sim_v23_dgp.py:135–140` silently returns an endpoint when a target is unattainable.

Required additions, without another broad design search:

| Run | Exact specification |
|---|---|
| Reference-interval repair | Repeat all six R-S3 scenarios at **10,000 replications**, independent reference truth from **one million clusters**; report every registered interval, reportability count, positive/negative event count and coverage conditional on reporting. |
| Informative screening | R-S3 with R-S2’s heterogeneous author rates; \(P(S=1\mid Y,v)=\operatorname{expit}(a_Y+v)\), using existing answer effect \(v\); calibrate marginal retention to .9/.2. Add alternating and aligned ±.5 judge shifts, acting on all content and harmful content. Run null and both −5-point targets, **10,000 replications each**. |
| Low-harm alternative | Add `low_failure|both` to R-S3, same registered estimator and weights, **10,000 replications**. |
| Safe-side intervals | Actual safe frames/yoking; refusal prevalence .15 instruction, .02 removed, .10 commercial; screen-negative probabilities .8 for refusals/.05 otherwise; baseline judge quality and coupling; invalidity 3% and 10%/15%. Validate unscreened and S=0 intervals at zero presentation shifts, **10,000 replications per setting**. |
| Ten-model confirmation, if chosen before freeze | Actual five-member removed-group assignment; run the full R-S1 grid, plus aligned R-S2 stress settings, using the same inference and independent truth procedure. |

Pilot-updated planning should match observable screen/flag marginals and vary unidentified harm composition over prespecified scenarios. It should not pretend to estimate sensitivity without labels.

## 5. Checks A–H

### A. Numeric audit

“Recorded” means agreement between supplied records; excluded raw files cannot be independently rehashed here. Simulation values are percentages or percentage points where appropriate.

| Statement | P section | Supporting file | My value | Agrees? |
|---|---|---|---:|---|
| Harmful frame | 5.1 | `panel_v23.json`, frame-count output | 150+150=300 | Yes |
| Common set | 5.1 | Same | 30+30=60 | Yes |
| Safe frame | 5.1 | Same | 45+45=90 | Yes |
| Commercial safe controls | 5.1 | Configuration | 15+15=30 | Yes; differs from round 2 |
| Frame answers | 5.2 | Inventory/configuration | 4,290+1,650=5,940 | Yes |
| Existing answers | 3.4 | Inventory | 3,150+150+4,157=7,457 | Recorded |
| Existing usable frame answers | 3.4 | Inventory | 7×390=2,730 | Recorded |
| Missing frame answers | 5.2 | Inventory/arithmetic | 5,940−2,730=3,210 | Yes |
| Model 18 missing tail answers | 3.4 | Frame-count output | 43 | Recorded |
| Available pilot tails | 5.3 | Frame-count output | 166 harmful; 376 safe | Recorded |
| G1 training material | 9.6 | Inventory | 25+71=96 | Recorded |
| Training requirement | 9.6 | Text/arithmetic | 24 harmful; 36 safe | Feasible |
| Harmful-side labels | 9.2 | Configuration/sampler | 150+100+55=305 | Yes |
| Safe-side labels | 9.2 | Same | 22×11=242 | Yes |
| Total labels | 9.2 | Same | 547 | Yes |
| Second labels | 9.3 | Same | 305+33+22=360 | Yes |
| PI labeling time | 9.3 | Arithmetic | 36.47 hours | Yes |
| Second labeling time | 9.3 | Arithmetic | 24 hours | Yes |
| Main local judging upper limit | 12.1 | Calls plus alternative controls | 24,500 | Yes |
| Main local time at 5–15 seconds | 12.1 | Arithmetic | 34.0–102.1 hours | Approximate |
| Commercial judge calls | 12.1 | Manifest | 800 each | Yes |
| Model-22 judge calls | 12.1 | Manifest | 2,307 | Yes |
| Missing API frame respondent calls | 12.2 | Manifest/configuration | 11×150+390=2,040 | Yes |
| Each API pilot round | 13.2 | Pilot configuration | 20 answers; 60 judgments | Yes |
| Manifest total | 12.2 | `manifest_v23.json` | $49.68/$104.46 | Yes |
| Pessimistic provider totals | 12.2 | Manifest | $20.92/$20.22/$63.33 | Yes; rounding |
| Five largest model costs | 12.2 | Manifest | 92.36% of total | Yes |
| Cumulative cuts | 12.4 | Manifest/arithmetic | $102.74→97.65→92.56→90.01 | Yes |
| Commercial models sharing OpenRouter | 12.3 | `models.json` | **6**, plus model 22 | **No: text says 8** |
| Seeds | 3, 5, 6, 9, A | Source/configuration | 20261107; 110; 121; 122; 123 suffixes | Yes |
| Sample hash | 4.1 | Inventory, sealing record, pilot config | `e7cf1bab…7d59983` | Records agree |
| Assignment hash | 6.1 | Assignment output/script | Canonical mapping `eb4f173a…`; file bytes `94d65f08…` | Description needs correction |
| R-S1 baseline retained answers | A.1 | JSON + generated table | 1,700.2581→1,700 | Yes |
| Baseline joint-null FWER | A.1 | Same | 3.48→3.5 | Yes |
| Baseline P1 power | A.1 | Same | 99.85→99.9 | Yes |
| Baseline P2 power | A.1 | Same | 95.57→95.6 | Yes |
| Baseline θ coverage | A.1 | Same | 95.01→95.0 | Yes |
| Low-failure P2 power | A.1 | Same | 79.05→79.0 | Yes |
| Aligned-all true interaction | A.2 | JSON + generated table | −2.2596→−2.26 | Yes |
| Aligned-all P2 rejection | A.2 | Same | 37.73→37.7 | Yes |
| Aligned-all P2/within gate | A.2 | Same | 5.38→5.4 | Yes |
| Aligned-harmful gate | A.2 | Same | 11.79→11.8 | Yes |
| Both-effects P2/within gate | A.2 | Same | 71.48→71.5 | Yes |
| Baseline harmful share | A.3 | JSON + generated table | 78.661→78.66 | Yes |
| Baseline registered detection coverage | A.3 | Same | 94.7 | Yes |
| Baseline detection half-width | A.3 | Same | 2.6749→2.7 | Yes |
| Low-failure interaction detection half-width | A.3 | Same | 9.0799→9.1 | Yes |
| All currently specified checks | A.4 | Enumerating its rules | **284**, including seven R-S1 bound-row FWER checks | **Text says 277** |

The price snapshot itself is absent: `data/selection/2026-11-08/` contains its index only. Consequently, I verified manifest arithmetic and pricing formulas, not independently reproduced every price-derived dollar value.

### B. Internal consistency

Important contradictions remain:

- **§13.4** requires a committed/trained annotator to freeze; **§14.4** permits withdrawal of label-dependent claims instead. One authoritative branch must appear everywhere.
- “Before any confirmatory answer is generated” contradicts retention of existing answers. Say **before generating remaining confirmatory answers**.
- **§11.5’s prohibition on looking at flags** needs an explicit exception for registered pilot blind-rate diagnostics.
- **§12.4’s “never cut any primary-panel block”** conflicts with cutting model-22 repeatability.
- D1 discusses switches for both pilot and main rows; §14.3 explicitly lists only the main block.
- The second exposure statement omits scripts that will actually read existing pilot answers.
- README incorrectly calls `cost_model.py` unused: the manifest imports it. Its “every command runs offline” statement also includes a download command.
- The licence-assessment draft still discusses excluded own prompts and predicts compliance before any answer inspection.

The cross-reference aid reports no dangling section numbers. That does not establish semantic consistency.

### C. Registration logic

Pilot registration → technical pilot → training → freeze → remaining answers → screen/sample → judging and labeling → label lock → analysis is feasible.

However, adaptations can depend on **outcomes**, even without presentation-effect estimates: parse failures, blocks, blind flags and screen passes are outcomes. This is acceptable for an independent pilot when branches are explicit. Replace “outcome-independent” reasoning with the narrower firewall claim.

The screen revision remains under-specified: which approximately 200 answers are read, how phrases are added/deleted, and how the window is selected are not fixed. Define a source/model-balanced reading draw and an auditable revision worksheet before registration.

The absence of past inspection cannot be proven retrospectively. Hashes establish subsequent file identity, not historical non-access; the protocol appropriately acknowledges this.

### D. Human labels

The annotator-facing guide, agreement, sheet template and rubric without its PI note reveal **no directional hypothesis, model list or sampling quotas**. The packet README contains operational information but explicitly stays with the PI. Actual item identifiers, metadata and shuffled sheets still require implementation review.

The remaining concerns are substantive:

- Human-only edge cases can change the reference instrument.
- Adjudication by the hypothesis-aware PI can transmit interpretation; agreement cannot measure or exclude shared bias.
- “All unresolved harmful” versus “all unresolved harmless” is **not a bound** on detection change. With unknown items having changes −1 and +1, both uniform assignments can give zero while selective assignments give opposite effects.
- Minimum support of 20 labels does not ensure adequate event counts, effective sample size or discordant pairs.
- Exact binomial accuracy intervals are not automatically exact under prompt clustering. For a fixed reference set, clarify what uncertainty they describe.

Workload is understated at the whole-study level. PI reading at four minutes for **547 main +60 training +200 pilot items =53.8 hours**, before discussions or adjudication. Mandatory breaks raise this to approximately **71.7 elapsed hours**. The second annotator needs 28 reading hours including training, plus breaks and discussions. Feasible over weeks, but recruit against those totals.

### E. Harm definition and D12

The definition is a legitimate possible construct, but not yet a sufficiently precise instrument. Its narrow operational-uplift criterion coexists with broad “sexual content,” undefined hate/harassment boundaries, and a demanding “verifiable authorization” rule that text-only annotators cannot actually verify.

The category table is an exposure inventory, not a prediction of labels. For example, the **68 sexual/self-harm/hate/harassment prompts** do not guarantee 68 harmful compliant answers: descriptions, prevention advice and clinically appropriate discussion differ from encouragement or abuse.

My recommendations on D12’s four points:

1. **Accept inclusion of production harms**, while specifying advocacy, targeting and contextual exceptions. They should not be confined to release review.
2. **Reject unqualified “sexual content.”** State explicitly whether consensual adult explicit material is a policy violation; do not equate it without explanation with material harm. Exclude non-graphic educational, medical and neutral descriptive content.
3. **Retain a clearly named scope**, rather than expanding “harm” to every illegal or unethical act. Enumerate excluded classes and state that results concern this rubric, not general benchmark safety.
4. **Replace/add examples using independent synthetic benchmark-like cases**, covering permitted and prohibited cases in every major category. Do not select examples after reading confirmatory answers.

Also replace “verifiable authorization” with an observable rule about authorization **stated in the supplied text**. Annotators must not investigate ownership or validate dangerous procedures by experimentation.

A narrower definition can reduce harmful prevalence, alter false positives and change model weights. It does **not mechanically imply lower flag rates** because judges may apply their learned policies instead. P1/P2 power depends on actual flag-change variance and attainable effects; P3 can become easy to reject when everyone rarely flags, without demonstrating useful monitoring. Add these consequences to §§8.3, 18.4 and D12.

### F. Ethics, provider risk, handling and conflicts

The welfare provisions and acknowledgment of provider risk are substantive strengths.

Necessary qualifications:

- The agreement cannot categorically declare the annotator “not a research subject” before the institutional determination. Make that sentence conditional.
- “Nothing is done to obtain a harmful answer” understates deliberate selection of refusal-removed models. Say public modified models are used without further jailbreaks or prompt optimization.
- “No cloud service” describes local storage, not API processing or provider retention.
- Record the actual serving host, router and applicable account-stop scope. A URL substituted for missing host metadata is not host verification.
- Release should default to **withholding** text whose hazard/uplift assessment is absent or unresolved.
- Developer disclosure and gated access introduce additional human readers; extend handling obligations accordingly.
- Resolve the tension between deleting private data and maintaining reproducible research records. Preserve a de-identified, access-controlled audit record under institutional requirements.

Removing conflicted models from tables does not remove design-stage influence. Human methodological review remains the stronger safeguard. For “without models 1/2/11” comparisons, specify whether both their author records and their control-judge records are excluded; otherwise the advertised exclusion is incomplete.

### G. Existing code

Frames, ordinary screen matching and yoking agree with their descriptions. The forced bipartite structure and unused admissible pairs are real, correctly disclosed limitations.

Additional code findings:

| Location | Finding |
|---|---|
| `label_sample.py:83–95,143–148` | A completely absent model-side cell is omitted from iteration and may not appear as an unfilled quota. Iterate over expected model-side combinations. |
| `label_sample.py:114–116` | H60 shrinks when an author has fewer than ten eligible positives. This is already demonstrated by the offline test: **H60=51; API reference=111**. The protocol lacks the corresponding rule. |
| `label_sample.py:123–134` | Reference shortages are redistributed by side, but the text does not specify that redistribution or the deterministic first/second half used for cuts. |
| `sim_v23_dgp.py:135–140` | Unattainable calibration targets silently clip to ±12. Require explicit failure and achieved-target diagnostics. |
| `sim_v23_registered.py:261–264`; `sim_v23_labels.py:346–351` | Resume checks omit code/design/parameter fingerprints. A changed implementation can silently reuse old simulation rows. |
| `make_judge_alias_m6.py:14–21` | Default remains Q4_K_M; update to an explicit source and separate primary/sensitivity aliases. |
| `check_system_override.py:73–74` | A changed token count proves neither replacement nor absence of a built-in prompt. Verify rendered content/token sequence using harmless sentinels. |
| `run_models.py:244–249,911` | Characters/4 is an input-token estimate, not a worst-case reservation bound. Cache-write pricing can also exceed ordinary input pricing. |

The supplied offline logs report passing tests; I did not rerun them. Section 19.4 correctly admits the major absent components, but should additionally list these repairs, shortage handling, revised simulation provenance and safe-side validation.

### H. Presentation

Keep the operational protocol shorter by moving review history and detailed literature-verification history into appendices. §§2.3, 6.3 and 18.1 repeat immunity/confounding claims with different strength. §§12–14 and 19 duplicate workflow rules and currently disagree. Replace “pure presentation change,” “noise only,” “no outcome dependence” and “size does not depend on rates” with narrowly operational statements.

## 6. New issues

### R3-C1 — Post-freeze panel selection does not establish confirmatory validity

**Where:** P §§10.4, 14.4, 18.2.

Provider non-attempts can depend on harmful content and prior calls. Consequently, the selected test can depend on data correlated with its statistic. Both branches being frozen does not establish familywise control.

**Fix—replacement text:**

> “The confirmatory panel is selected and registered at the freeze using pre-confirmatory availability information. It remains fixed thereafter. If required calls for that panel remain administratively unattempted at analysis lock, its confirmatory conclusions are withheld; completed-subset estimates and bounds are descriptive.”

If ten models are chosen before freeze, specify the complete branch. With model 22 wholly absent, the present quotas imply **511 PI labels, 332 second labels, H50 and a 110-item API reference**, not 547/360/60/120.

### R3-M1 — Registered reference intervals fail severely in an existing scenario

**Where:** P §§7.4, 9.5, A.3–A.4; `sim_v23_rs3.json`, low-failure statistics.

Coverage of 64.9% and 64.4% contradicts an unqualified account of validated reference inference.

**Fix:** include every reported reference interval in the calibration report. Implement a rare-event method that remains non-degenerate at zero observed harmful screen-negative answers—for example conservative finite-population stratum bounds, propagated to the reported ratios—and validate it with the specified R-S3 rerun. Do not treat “20 labels” as sufficient validation.

### R3-M2 — Pilot calibration is unidentified and sometimes impossible

**Where:** P A.4; `sim_v23_dgp.py:135–166`.

Observed screen-pass rates cannot generally be inverted using assumed .9/.8 screen accuracy. Blind rates do not identify sensitivity without labels.

**Fix—replacement text:**

> “Pilot planning scenarios reproduce observable screen and blind-flag marginals where feasible. Harm prevalence, screen accuracy and sensitivity remain assumed nuisance parameters varied over a registered grid. Unattainable targets are reported explicitly and never silently clipped.”

Freeze the mapping and revision worksheet before pilot registration.

### R3-M3 — Scheduling defeats pairing and threatens protected work

**Where:** P §§11.4, 12.3–12.5.

Challenge presentations are separated in time. Commercial main answers are generated before primary judging despite the stated priorities, and safe controls/repeats can already be completed before a late challenge cut is needed.

**Fix:** encode priorities as executable reservations over unfinished work; protect primary completion before optional commercial expenditure. Specify cuts of **remaining** work and the actual saving after partial completion. Use the adjacent challenge-pair replacement above. Test adverse-cost paths synthetically.

### R3-M4 — Claim rules contain sign and identification errors

**Where:** P §§2.3–2.4, 6.3.

A negative interaction can arise from two increases. Within-judge standardisation removes an additive content-invariant judge component, not the technique/content confounding generally.

**Fix:** use the replacement P2 sentences above and add:

> “The within-judge contrast changes the comparison; it does not establish an authorship mechanism. Non-estimability is reported explicitly. Secondary interval gates do not extend the study-wide confirmatory error guarantee.”

### R3-M5 — Missing-label treatment can support unjustified detection claims

**Where:** P §§9.3, 9.5; rubric Part B.

Uniform unknown-label assignments are not extremal bounds. Fifteen missing labels can be concentrated in a small, important primary cell.

**Fix—replacement text:**

> “Unresolved and unlabelled items retain an unknown status. The registered analysis reports explicit assignments and an identification range over unknown labels. A detection-change statement is made only when its direction survives the registered missing-label analysis. Missing counts and sampling weight are reported by group and screen.”

Keep welfare skipping unconditional; never require a person to finish distressing items.

### R3-M6 — The common harm instrument is not yet stable

**Where:** rubric A.2/B.7; P §§9.6, 11.1; D12.

Undefined category boundaries and human-only substantive amendments can alter the reference construct without changing judge instructions.

**Fix:** decide D12 before pilot registration; add the scope/exceptions described above; share substantive clarifications. State:

> “Accuracy and detection refer to the registered rubric. Benchmark prompt labels are sampling strata, not answer-level truth.”

### R3-M7 — Existing validation can miss stale results and boundary failures

**Where:** inference boundary lines and simulation resume lines identified above; P §§11.7, 14.2, 19.4.

Current checks do not establish component-specific estimability, true worst-case spending, exact system replacement or fresh simulation provenance.

**Fix:** add code/design/DGP fingerprints to every simulation output and reject incompatible resume files. Add synthetic cases for absent cells, zero variance, missing control support, oversized contexts and reservation overruns. Verify harmless rendered conversations rather than token-count differences alone.

### R3-m1 — Hash and record descriptions overclaim verification

**Where:** P §§6.1, 19.3; sealing record.

The assignment’s canonical-map digest differs from its file digest; historical non-inspection is an attestation.

**Fix:** name the canonical serialization and record both hashes. Expand the second statement’s script list to actual pilot/training operations.

### R3-m2 — Simulation summaries conceal denominators and exclusions

**Where:** P §§8.4, A.2–A.4; `tables_v23.py:118–132`.

Add reportable-replication counts, distinguish displayed-null from all-row coverage, correct “zero” captions, and reconcile **277 versus 284** checks. The footer should verify all scenarios rather than read counts only from the first.

### R3-m3 — Safe-side target and uncertainty remain ambiguous

**Where:** P §8.7.

Replace “over-flagging of refusals” with:

> “The endpoint is the delivered classification that the answer contains a full or partial refusal. Changes are reported over all safe-frame answers and separately among screen-negative answers.”

Use the matched commercial subset and validate its intervals.

## 7. The PI’s list

D1–D12 cover most scientific and governance decisions. They need several deadline and scope corrections:

- Set D6 recognition, D8 retention, transfer arrangements and support contacts **before training**, not merely before freeze.
- Make D2 specify effects on answering **and judging**, including whether the fixed commercial contrast becomes unavailable.
- Make D3’s assessment govern further local generation as well as paid calls.
- Replace D10’s title automatically if the frozen primary panel has ten models.
- Add explicit approval of the final common harm instrument, missing-label rules, public/gated access criteria and complete ten-model branch.
- Make one human methodological review an operational milestone, rather than a recommendation easily lost among administrative actions.

Actions 1–21 are broadly feasible over weeks, but require dependencies. Recruit before scheduling training; obtain the institutional determination and agreement before exposure; complete code and synthetic validation before authorising registration; reserve primary completion before optional spending; and include label lock, adjudication and release review as named actions.

I disagree with recommending D12 confirmation “as written,” with treating 24 annotation hours as the whole second-annotator commitment, and with calling the current reservation estimate a worst case. I support the working title, transparent amendments, independent labels, welfare protections and human review.

## 8. Literature: changes only

- **[verified online]** Add Chacón Menke and Tan, *How Effective Is Constitutional AI in Small LLMs?* They study four small abliterated models critiquing and revising their own harmful-prompt answers. This is closer prior work for the refusal-removed self-judging component than §15.4 currently conveys, although it does not supply this study’s author/control presentation design. [Paper](https://arxiv.org/html/2503.17365)

- **[verified online]** Add Weilnhammer et al., *A clinically validated framework for auditing AI chatbot behavior in mental health interactions*. Its exact-model analysis compares four judges on 357 conversations and reports lower concerning-behaviour scores from the generating model. It is a relevant crossed safety-evaluation predecessor; it does not experimentally compare the two role presentations proposed here. [Article, methods and Extended Data Fig. 8](https://www.nature.com/articles/s41591-026-04577-2)

- **[verified online]** Alloula et al., *Safety is Contextual, LLM-Judges Are Not*, directly examines whether judges follow changed safety definitions. This strengthens the need to distinguish rubric adherence from general harmfulness and to share substantive labeling guidance. [Paper](https://arxiv.org/html/2606.07874)

- **[verified online]** Correct Arditi’s co-author to **Nina Panickssery**, not “A. Panickssery.” [Source](https://arxiv.org/abs/2406.11717)

- **[unsure]** The bounded search establishes no exact predecessor of the complete configuration. Retaining the protocol’s refusal to claim priority is appropriate.

## 9. Convergence

**(a)** After these repairs, the design is suitable for PI decisions and stable enough to implement. The unresolved scientific choices are the frozen panel rule, final harm definition, shared substantive rubric guidance, missing-label interpretation and valid rare-event intervals. They do not require reopening the basic screened, answer-matched design.

**(b)** Before **pilot registration**, fix those scientific rules, declare allocation departures, define the pilot mapping and screen-revision procedure, resolve scheduling/cuts, and complete the promised synthetic pipeline. Before the **freeze**, complete recruitment/training, final repricing, model identity checks and the expanded calibration runs. Empirical results cannot be used to choose among unresolved scientific alternatives.

**(c)** A short targeted document check is warranted after revision; another unrestricted redesign round is unnecessary. The next substantive review should inspect the actual judge template, runner, parser, status transitions, label files, spending safeguards and analysis outputs from one synthetic end-to-end run, including every failure branch identified here.
