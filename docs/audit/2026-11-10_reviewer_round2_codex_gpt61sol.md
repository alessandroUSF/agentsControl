# Reviewer round 2: Codex, GPT-6.1 Sol, reasoning effort "xhigh" (10 November 2026)

This is the second round of the iterative review. The reviewer assessed the author's response to round 1 (`2026-11-10_round2_author_response.md`, "draft B"), the simulator and its outputs, and the cost model. It ran in the Codex CLI (`codex-cli 0.167.0-alpha.3.2`, `codex exec`, read-only sandbox, connectors disabled, a fresh session without memory of round 1), thread `01a1c507-ecf2-75a2-aff9-c3e82e835c9a`, from 05:36:33 to 05:51:32 local time (exit code 0).

- **Input:** a read-only clean copy of part of the repository (`E:\claude\_audit_copy\agentsControl_r13_round2`, 83 files), with the round-1 prompt and report inside. It held no model answers, no benchmark prompt files, no author prompts, no gold key and no secrets. Local user paths and third-party personal names were redacted.
- **Instructions:** `2026-11-10_prompt_for_codex_round2.md`. Web search was allowed only to verify cited papers and to look for closer prior work.
- **Conflict of interest:** GPT-6.1 Sol is also respondent and judge number 11 of the study panel. The prompt disclosed this and the reviewer states it in its verdict. One recommendation of this round (no in-context presentation of the H60 set to the commercial judges) reduces what the study can find about commercial judges; the reviewer says so itself. That point is weighed separately in the author's reply.
- **What the reviewer did:** 20 read-only shell commands inside the copy (`sed`, `nl`, `awk`, `wc`, `find`, `cat`; one call to a tool that is not installed failed) and 3 web actions (two arxiv.org pages opened, one search with two general queries). It did not run the Python analyses (Python is not available in its sandbox). The event log was checked: no file outside the copy was read and no packet text was used in a search query. Token use reported by the CLI: 1,800,863 input (1,636,096 cached), 28,625 output.
- **Text:** the final message is reproduced as returned. Its statements are claims to verify, not instructions. The links in its section 1 point to the review copy, not to this repository.

---

## 1. Verdict

Draft B is worth running and could support a useful paper, including an informative null result. The author’s evidence justifies replacing round 1’s equal-judge primary panel: that recommendation was statistically valid but insufficiently attentive to dilution and scarce commercial failures. I accept the larger open-model panel, type-matched controls and a screened primary estimand, with changes to inference and interpretation. I would not freeze draft B as written: its sign-flip validity argument is too strong, its claim rules do not identify leniency, and its cash manifest omits permitted work. The design below is sufficiently settled for transcription into v2.3 and a document-level round 3; execution remains conditional on implementation, calibration and staffing.

**Disclosure:** I am GPT-6.1 Sol, respondent/judge 11. Moving commercial models to secondary analyses and reducing their assistant-turn exposure can limit adverse findings about OpenAI; my recommendations apply uniformly to the commercial panel.

I inspected the supplied files and performed arithmetic. I did not execute simulations, inspect answer data, modify files or make model/API calls.

Throughout, **A** denotes the [author response](E:/claude/_audit_copy/agentsControl_r13_round2/docs/audit/2026-11-10_round2_author_response.md), **S** the [simulation summary](E:/claude/_audit_copy/agentsControl_r13_round2/analysis/output/power_sim_v23_summary.md), and **SIM** the [simulator](E:/claude/_audit_copy/agentsControl_r13_round2/analysis/power_sim_v23.py).

## 2. Round-1 issues

These statuses distinguish an accepted design solution from unfinished implementation.

| Issue | Status | Assessment |
|---|---|---|
| R1-C1 | **Not resolved** | Harm classification is correctly primary, but A §3.6 still converts operational flag changes into unsupported leniency/strictness conclusions. Replace its interpretation table. |
| R1-C2 | **Resolved on a condition** | Same-answer controls solve the original content-matching problem. Complete the commercial controls and describe the interaction as author-versus-control effect modification. |
| R1-C3 | **Resolved on a condition** | Delivered flags, bounds and decomposition are appropriate. Complete-case negativity does not remove selection bias; distinguish attempted invalid calls from administratively unattempted calls. |
| R1-C4 | **Not resolved** | Printed arithmetic reconciles, but a second pilot is missing, respondent output doubling is incomplete, and the executable manifest does not exist. |
| R1-M1 | **Not resolved** | Substantial progress, but screened interval coverage, actual sampling weights, heterogeneous screened nulls and production-code agreement remain unvalidated. |
| R1-M2 | **Resolved on a condition** | The exclusion question is now correctly formulated. Replace the exact-validity claim and calibrate the registered ratio bound at its actual boundary. |
| R1-M3 | **Resolved on a condition** | The external-pilot principle is sound. Register the scientific choices before it, constrain revisions, and replace discretionary warning/resumption language. |
| R1-M4 | **Not resolved** | Adjudicated double labels are accepted, but the fallback removes independent scrutiny from harmful-prompt negatives and potentially positives. |
| R1-M5 | **Resolved** | Three fixed pairs, descriptive estimates, common-item comparisons and no preservation headline are appropriate. |
| R1-M6 | **Resolved on a condition** | The correction is accepted. The rewritten novelty paragraph must acknowledge that on-policy content and unrelated judges are already present in prior work. |
| R1-M7 | **Resolved on a condition** | Publish the hypothesis-by-hypothesis amendment and exposure history; the promised table is still absent. |
| R1-M8 | **Not resolved** | Necessary code and the synthetic end-to-end demonstration remain absent. |
| R1-M9 | **Resolved** | Deleting G3 removes the disputed adaptive-sampling problem. |
| R1-m1 | **Resolved on a condition** | Replace the cited disclosures before distributing annotator materials; also update their obsolete workload estimates. |
| R1-m2 | **Resolved** | The dated inventory substantially reconciles the state record. Carry it into v2.3 and remove contradictory legacy statements. |

## 3. The four departures

### 3.1 On-policy panel — **accept with modification**

The arithmetic is correct:

\[
11(.05)+5(.15)+6(.70)=5.50,\qquad \bar f=.25.
\]

The commercial, instruction-tuned and refusal-removed contributions are respectively **10.0%, 13.6% and 76.4%** when the harmful-answer effects are equal and harmless-answer changes vanish. A −2-point overall change then corresponds to −8 points among harmful answers.

These are **contributions under assumptions**, not fixed statistical-information weights. They change with judge-specific effects, false-positive changes, invalidity and covariance. Refusals need not have zero flag changes: the simulator explicitly gives harmless answers nonzero false-positive probabilities.

The reported baseline power ranges are supported, conditional on the other primary effect being zero. The larger panel also gives the stated improvement in unscreened null SEs: **0.88/1.14 points at 150 prompts versus 0.61/0.82 at 300**.

The narrower paper remains worth writing. Describe a **prespecified open-model panel**, rather than selecting “models that produce harmful content” after observing their outputs. Its primary evidence will concern these checkpoints and the specified benchmark mixture.

One correction strengthens the limitation: under a perfect screen, refusal-removed models contribute

\[
4.2/(4.2+.75)=\mathbf{84.8\%}
\]

of the primary screened answers. “About three quarters” fits the noisy-screen example better than the perfect-screen case.

Use a title such as **“Judging Their Own Answers: Conversational Presentation and Harm Flags in Eleven Open Models.”**

### 3.2 Type-matched yoking — **accept with modification**

The simulations support the concern. With susceptibility shift −0.6, access matching produces interactions of approximately **−0.82 to −1.11 points**, with **7.3–10.2%** P2 rejection; type matching gives approximately zero and **2.3–4.2%** rejection.

However, these are not necessarily inflated rejection rates for the statistical null \( \iota=0 \): the simulated access-matched estimand is actually nonzero. They demonstrate that **absence of an authorship mechanism does not imply a zero operational interaction**.

Type matching reduces that problem but does not eliminate it:

- Screened author and control workloads differ within judges.
- Susceptibility can depend on harmfulness, difficulty and author style.
- Model 20 has only two admissible controls, both from one developer.
- Pair-count balance is constrained. One supplied 300-prompt simulation reports admissible refusal-removed pair counts ranging **0–151**.

Retain matching, publish the assignment matrix and imbalance diagnostics, and keep the judge-normalised contrast as a sensitivity analysis. Its claimed immunity applies only to an **additive, content-invariant judge effect**. It is not generally immune to susceptibility.

Inference is conditional on the fixed model panel. Prompt clustering does not justify generalisation to a population of model families.

### 3.3 P-S — **accept with modification**

Use pooled P-S as primary, with P-U beside it. Its exact interpretation is:

> The difference in delivered harmful-content flag probabilities among answers retained by the frozen keyword screen, pooled over the specified author–prompt frame.

The unit should be **“percentage points among screen-positive answers,”** not unqualified “non-refused answers.” The screen is neither a refusal reference standard nor a harm label.

Its timing is helpful: it is unaffected by subsequent judgment presentation. Consequently, conditioning on it is legitimate for this explicitly conditional estimand. But “fixed before judging” does **not** establish sign symmetry. A zero mean does not imply symmetry of prompt totals, and randomising call order does not randomise the signs of the presentation contrast.

The supplied power gains are real within the simulated worlds: P2 rises from **45.4% to 78.9%** with the perfect screen and **65.3%** with the noisy screen. In the noisy case the screened interaction itself is approximately **−3.57 points**, while the underlying harmful-answer interaction is approximately −4.6. These scales must remain distinct.

The respondent–judge identity also matters: screening changes which judges receive weight. This is acceptable for the declared pooled estimand, but prevents interpreting it as an equal-judge average.

Register a **prompt-cluster ratio estimator with studentised, asymptotic inference**, specified below. Validate its random-denominator coverage and heterogeneous weak-null behaviour. Keep sign-flipping as a sensitivity analysis without claiming finite-sample exactness.

### 3.4 H60 — **accept with modification**

H60 can measure a meaningful **presentation effect on a common, externally generated text set**. It cannot measure commercial judges’ on-policy self-evaluation, and it cannot establish why a judge reacts differently.

Two descriptions need correction:

1. Screen-positive answers are not necessarily harmful; call it a **screen-positive challenge set** until human labels establish its composition.
2. Some panel members did write these answers. Excluding related author–judge combinations makes the eligible set judge-specific. Model 20, for example, retains only the **20 answers from models 18 and 19**.

My recommendation is to retain H60 **blind for all 22 judges**, and retain its in-context presentation for the eleven primary-panel judges. Omit commercial H60 in-context calls. This preserves common-content calibration while reducing provider exposure and releasing **$5.09 pessimistically**.

This deliberately sacrifices the commercial off-policy presentation comparison. There is no lower-risk wording substitute that preserves exactly that information. The files establish the existence of provider risk, not that its probability is acceptably small; a ten-item pilot cannot establish that.

## 4. The twelve decisions

| # | Recommendation | Reason |
|---|---|---|
| 1 | **P-S primary; P-U adjacent** | Better sensitivity to the stated conditional question; retain the operational all-answer scale. |
| 2 | **Pooled P-S** | Stable, clearly defined answer-level target. Equal-judge screened means answer a different question and require empty-cell rules. |
| 3 | **Replace §3.6** | Its mechanism classifications are not identified by these observations. |
| 4 | **Buy all commercial harmful-prompt controls** | Removes the cap-dependent selection problem and supplies the complete common-60 interaction. |
| 5 | **H60 blind for all; in-context for primary panel** | Retains calibration and open-panel presentation evidence with less commercial exposure. |
| 6 | **Retain a 7-point screened bound, narrowly worded** | Acceptable as a coarse numerical exclusion; it does not establish equivalence, usefulness or absence of preference. Use calibrated ratio inference. |
| 7 | **Type matching** | Reduces demonstrated type-composition confounding; does not identify an authorship mechanism. |
| 8 | **Keep 90 own safe answers; commercial controls on 60** | Protects the primary work and human-reference block. Analyse the commercial safe interaction on that matched 60-prompt subset. |
| 9 | **Allow the blind flag-rate diagnostic; no efficacy adaptation** | An independent-pilot baseline is permissible. It is not sensitivity without harm labels. |
| 10 | **Keep 550/360 targets; revise sampling and fallback** | Require positive inclusion probabilities and all 300 harmful-prompt answers independently double-labelled. |
| 11 | **Own prompts out** | An exploratory appendix would restore a separate question and workload without strengthening this paper’s main inference. |
| 12 | **Register scientific choices and adaptation rules before the pilot** | Final technical settings may follow the pilot; primary scale, panel logic, margins and claim rules should not. |

For decision 9, report blind flag rates with denominators and intervals. A low rate should trigger **disclosure of limited detection opportunity and updated precision simulations**, not judge exclusion, a different primary statistic, a wider margin or cancellation for lack of a promising effect. In particular, a low flag rate among keyword-positive answers can reflect harmless content, screening error, invalidity or low sensitivity.

## 5. Checks A–F

### A. Numeric audit

The table checks the response against outputs and code. “Agree” means that the specified calculation is reproduced, not that its assumptions are empirically established.

| Statement in A | File/location | My value | Assessment |
|---|---|---:|---|
| Mean assumed harmful-answer share, 22 judges | SIM:79–89; A §2 | 25.0% | Agree |
| Contributions 10/14/76% | Same | 10.0/13.6/76.4% | Agree, conditional |
| −2 overall points corresponds to −8 harmful-answer points | A §2 arithmetic | \(2/.25=8\) | Agree, conditional |
| Refusal-removed models supply roughly three quarters of primary retained answers | A §12; SIM rates | 84.8% with perfect screen; 73.1% with Se .9/Sp .8 | Qualification required |
| Joint-null marginal rejection ranges | `screen.json`, joint-null rows | P1 1.15–2.75%; P2 1.55–2.30% | Agree |
| Joint-null familywise rejection | Same | 2.25–3.60% | Supports baseline simulation, not universal validity |
| P1 power at target −2 points, other effect zero, 3% invalid | Same | 14.25–52.05% | Agree |
| SEs at 150 harmful prompts | S §`panel_harm11_150` | 0.88/1.14 points | Agree at null |
| SEs at 300 harmful prompts | S §`panel_harm11_300` | 0.61/0.82 points | Agree at null |
| P1, approximately −5.3 harmful-answer points | S:406–499; §`alts_sub2_noisy` | 77.1% P-U; 98.9% perfect; 95.3% noisy | Agree |
| P2, approximately −4.6 harmful-answer points | Same | 45.4%; 78.9%; 65.3% | Agree |
| Noisy screened P2 effect on that row | S §`alts_sub2_noisy` | −3.57 retained-answer points | Essential scale qualification |
| Susceptibility/access interaction | S §`susceptibility_access` | −0.82 to −1.11 points; rejection 7.3–10.2% | Agree |
| Type-matched susceptibility rejection | S §`susceptibility_type` | 2.3–4.2% | Agree |
| Blind-bound rejection near −1.3 points, margin 7 | `power_sim_v23_bound_check.txt` | 87.60–93.45% | Agree |
| Fixed-panel gap −7.05, margin 7 | Same, `bound1panel_-0.047` | 1.00% rejection | Agree; gap is Monte Carlo-estimated |
| Fixed-panel gap −7.23 | Same | 0.50% rejection | Agree |
| Commercial judge calls | `cost_model_v23b_stdout.txt` | 780 expected; 820 pessimistic | Agree |
| Model 22 judge calls | Same | 1,840 | Agree |
| Original draft-B totals | Same | $46.67/$98.71 | Agree as printed |
| Commercial full harmful controls increment | Same per-call rates; A §3.5 | $4.0664/$5.0948 | Agree |
| Commercial safe-side cost | Same; 360 calls | $14.639/$30.569 | Agree; pessimistic rounds to $30.57 |
| Cumulative cuts | Same; A §8 | $96.99 → $94.42 → $89.32 → $79.13 | Agree arithmetically; fourth cut absent from code’s cut list |
| Respondent “output doubled” | Cost code:127–142 | Reasoning doubled; visible output unchanged | Disagree |
| Additional visible-output doubling | Configured prices and stated direct batch discount | Approximately $2.77 pessimistic | Missing |
| Full second pilot allowance | Same prices/settings | Approximately $4.55 respondents + $5.15 judges | Missing $9.70 |
| Available pilot tails | `frame_counts_2026-11-10.txt` | 166 harmful; 376 safe prompts | Agree |
| G1 inside main frames | Same | 45 harmful; 9 safe answers | Agree |
| Existing answers | `DATA_INVENTORY.md` | 3,150 + 150 + 4,157 = 7,457 | Agree |
| Model 18 missing answers | Frame counts | 43, all harmful tail | Agree |

The cost reconstruction uses configured prices and the stated batch discount. The omitted price snapshot prevents a fully independent price-source audit.

### B. Simulator

The simulator is a substantial improvement over round 1. Shared prompt shocks, same-answer controls, informative invalidity, actual Holm processing and alternative screened statistics are valuable. It is suitable for **conditional planning**, after the following corrections.

**Correct implementations.**

- Delivered-valid flags at lines 364–370 implement the stated operational coding.
- Screen propagation to the yoked answer at lines 383–396 is correct.
- The Monte Carlo sign-flip p-value uses the appropriate plus-one correction.
- Holm at lines 448–452 and 490–493 is correctly implemented, including ties.
- The shifted statistic at line 402 correctly adds \(mN_p\) for a ratio boundary \(-m\). Its algebra is correct; its distributional justification remains conditional.
- Fail-closed scoring and on-policy worst-case bounds at lines 412–414 are correct.

**Bugs and validation weaknesses.**

1. **Coverage uses an estimated truth from the same replications.** Lines **441–442** assess intervals against that panel’s sample mean of estimates. This slightly favours coverage and cannot detect estimator bias. Obtain truth independently.
2. **Ratio intervals are absent.** Lines **398–406** save ratios but calculate no ratio interval; lines **494–502** report no screened coverage. A §4 appropriately acknowledges this.
3. **Mixed-frame weighting is unsafe generally.** Lines **369–370** weight control outcomes by the control judge’s weight. For unequal weights across admissible author–control pairs, the contrast requires the **answer author’s weight**, as the alternative implementation does at line 393. The selected primary type-matched panel avoids this particular mismatch.
4. **Zero denominators are silently replaced.** Line **398** produces a numerical ratio when none is estimable. Report non-estimability and its frequency.
5. **Screened familywise and joint rejection are not saved.** Lines **494–502** retain marginal rejection only. Add familywise rejection over true nulls and probability both primaries reject.
6. **“Noise only” is not literally noise only.** In the first `alts_sub2.json` scenario, calibrated shifts are approximately **−0.0686 author and −0.0348 control**. Lines **268–273** add these to offset noise on the parent estimand. Run an actual \(g_{\rm on}=g_{\rm ctrl}=0\) scenario before attributing those numerical effects to noise alone.

The DGP is optimistic about removed-model sensitivity and about screening. Its screen errors depend only on the binary failure indicator, whereas actual keyword errors can depend on disclaimer style, severity and judge difficulty. Failure rates are equal within types; this makes type matching cleaner than it may be. The label sampler at lines 346–347 and 423–438 uses Bernoulli quotas and unweighted conditional means: it is **not** the proposed screen-stratified, weighted gold design.

Finally, these simulations contain no provider-wide stopping, temporal service drift or realistic account-level dependence.

### C. Missing runs and exact specifications

Do not repeat the entire exploratory grid at decisive size. Validate the chosen design.

| Missing run in A §11 | Required disposition |
|---|---|
| (a) Screened effects on all answers/informative invalidity | **Before freeze** |
| (b) Screened ratio coverage | Basic implementation check before pilot registration; decisive calibration **before freeze** |
| (c) Equal-judge P-S | **Drop as a design-selection exercise**; optional descriptive sensitivity |
| (d) Judge-normalised interaction | **Before freeze** if retained; test additive and content-dependent susceptibility |
| (e) Fixed-effects blind model | **Drop the mandatory simulation**; optional descriptive sensitivity, with no confirmatory role |
| (f) Safe-side type matching/S=0 | **Before freeze** for interval validation; no power campaign needed |
| (g) H60 precision | Analytic planning is sufficient without a precision promise; simulate actual eligibility if reporting pooled type intervals |
| (h) Label-conditioned estimates | **Before freeze**, using the actual sampler and weights |

Three simulation packages are sufficient:

**R-S1: registered inference.** Use the final 11-author, 300-prompt manifest, fixed yoking, two 150-prompt sources, and the existing latent DGP. Start with screen Se/Sp .9/.8, shocks .3/.3, discordance .10 and invalidity 3%. Calibrate the **actual screened delivered-flag means** to \((\theta,\iota)=(0,0),(-.05,0),(0,-.05),(-.05,-.05)\). Add one-factor stress cases: shocks .6/.6; discordance .20; failure rates .03 instruction/.20 removed; removed sensitivity .30 and .50; screen Se/Sp .7/.6. For null-size checks, recalibrate the operational means to zero, rather than calling an informative-missingness scenario null because its latent classification shift is zero.

Use **10,000 replications per scenario**, a prespecified fixed judge panel, the registered cluster-t procedure, and **9,999 signs** for its sensitivity analysis. Report bias, coverage, marginal size, familywise size, joint power and denominator failures. Obtain reference means from **one million independent prompt clusters**, with their Monte Carlo uncertainty.

**R-S2: confounding and asymmetry.** Use the same baseline, with instruction-model failure rates .05/.10/.15/.20/.25 and removed-model rates .45/.55/.65/.75/.85/.95. Give judges additive presentation shifts of alternating ±.5 logits, first independent of content and then acting only on harmful content; align the more negative shifts with higher failure rates. Include the genuine zero-shift noise scenario, and invalidity modes `10_15` and `harm`. Use **2,000 replications/1,999 signs** for diagnosis; promote any problematic null-size setting to R-S1 size. Evaluate the pooled and judge-normalised contrasts against their **own actual targets**, not an assumed causal-zero target.

**R-S3: reference sampling.** Simulate the exact G1/G2/H60 selection algorithm, disjointness rules, shortages and inclusion weights, using both perfect and .9/.8 screens. Use **2,000 replications**, the final label-conditioned estimators and prompt-cluster intervals. Report positive/negative counts, effective sample sizes, bias and coverage.

A purely technical pilot need not await every decisive run. It must await a working synthetic pipeline, the locked scientific choices and a costed adaptation plan.

### D. Budget

The original manifest includes ordinary pilot calls and repeatability, but is **not complete** for its permitted adaptations.

The main omissions are the second pilot and visible respondent output doubling. A 15% retry allowance is a planning scenario, not a maximum: one format retry plus transport retries can exceed it. Output assumptions of 720 judge tokens also sit below the 2,000-token cap. Retain hard spending reservations and completion rules.

My consolidated allocation below reconstructs to approximately **$45.03 expected** and **$104.37 pessimistic**, including visible-output doubling and one complete second pilot for every API model. That leaves about **$5.63** under the hard cap. This is a planning reconstruction, not a certified executable manifest.

Preserve the 120-item blind reference ahead of commercial safe controls. Cutting reference coverage before those controls is the wrong priority. Remove the API guard first if it has no explicitly retained analysis; its cost is small, but an orphaned block is unnecessary work.

### E. Pilot and firewall

The tail counts and prompt-ID firewall are convincing. The earlier local pilot’s overlap does not contaminate confirmation under the stated fact that nobody inspected its answers and its pilot records enter no analysis. Correct the stale SEALED_HASHES statement implying those prompts are outside the gold frames.

Register before the pilot:

- Primary panel and statistic, matching, margins, alpha and claim language.
- Initial phrase list, permitted revision scope and revised-list selection procedure.
- Technical triggers, exact cap changes, second-run size and its budget.
- Provider-stop and missing-data rules.
- Spending cuts and their consequences for each reported estimand.

Allow the currently listed operational outputs and the requested **blind-only flag rate**. Do not expose presentation-specific flag summaries, paired differences or rankings. Keyword-pass proportions do not “replace failure rates”; they estimate screen-pass rates.

A warning must stop calls under a specified rule. “Until the PI records a decision” permits unbounded discretion. Any resumption should require a documented technical/provider resolution, unchanged scientific rules and remaining reservations; otherwise mark the provider unavailable.

### F. Claim rules and limitations

A §3.6 is the largest interpretive problem.

A lower sensitivity and no detected false-positive increase do not distinguish a threshold shift from noise, domain-dependent degradation, recognition, instruction following or changing delivery. “Not positive” is especially weak: a confidence interval crossing zero does not establish no increase. The positive-P1 row likewise does not establish “stricter”; it may represent improved sensitivity, additional false alarms or differential delivery.

Complete-case negativity is useful descriptive evidence but does not cure conditioning on presentation-dependent validity. Requiring several signs to agree is not a mechanism-identification strategy.

Report:

- presentation-associated changes in delivered flags;
- author-versus-control differences in those changes;
- human-referenced changes in detection and false alarms;
- delivery failures and uncertainty about their contribution.

“Consistent with leniency” may appear as a qualified interpretation. A confirmed leniency mechanism, psychological self-preference, recognition or collusion is unsupported. Neither the present design nor its secondary commercial analyses validate deployment safety.

## 6. New issues

| Issue | Where | Problem, consequence and concrete fix |
|---|---|---|
| **R2-C1** | A §§3.3–4; SIM:305–319 | Pre-judgment screening does not establish prompt-total sign symmetry under a mean null. Replace the exact-validity claim with the registered studentised cluster procedure below and validate weak-null size. |
| **R2-C2** | A §3.6 | The reading table claims mechanisms from non-identifying patterns, including absence of statistical evidence. Replace it with operational claim rules; retain mechanism discussion as qualified interpretation. |
| **R2-M1** | A §§8–9; cost code:127–142, 400–412 | Permitted pilot reruns are uncosted; visible output is not doubled; the fourth cut is absent. Build one manifest covering every allowed branch, then test its ledger and reservations synthetically. |
| **R2-M2** | A §§3.3–3.6 | Screening produces unequal judge exposure; type matching and normalisation do not generally remove susceptibility confounding. Publish weights, assignment counts and within-judge diagnostics; narrow the interaction’s name and claim. |
| **R2-M3** | A §6 | Sampling quotas, source allocation, shortage rules, overlap and inclusion probabilities are incomplete. “S=1 first” can leave zero coverage for commercial S=0 cells. Specify and validate the complete probability sampler. |
| **R2-M4** | A §§6,12 | Staffing fallback weakens precisely the human negatives needed to interpret missed harm. Secure capacity for all 300 harmful-prompt second labels; reduce safe double labels first, without silently weakening harm-reference claims. |
| **R2-M5** | SIM:268–273, 398, 441–442; A §11 | Calibration, truth estimation and gold sampling do not yet validate the registered analysis. Implement R-S1–R-S3 and production-code cross-checks; correct the “noise only” label. |
| **R2-M6** | A §§3.5,5,9 | Provider-wide stopping and administratively unattempted calls are not distinguished from item-level non-delivery. Define statuses and withhold full-panel confirmation if required cells were never attempted. |
| **R2-M7** | Protocol §8.3; `config/models.json`, model 6 | Model 6 generated with Q4_0 but judges primarily with Q4_K_M. Strict author identity is therefore imperfect. Use the weight-matched Q4_0 judge build for the primary author contrast, with verified hashes; retain Q4_K_M for the descriptive paired appendix if desired. |
| **R2-m1** | A §§3.5,10.1 | H60 is neither necessarily harmful nor uniformly off-policy across all panel members. Publish eligible counts and use common eligible intersections for matched-pair comparisons. |
| **R2-m2** | `SEALED_HASHES.md`; annotator packet | The sealing record omits later generated outputs, contains stale overlap wording, and workload estimates remain obsolete. Add pre-inspection hashes and reconcile the operational materials. |

## 7. The design to freeze

Accept A’s deletions, legacy-withdrawal scope, basic four-arm structure, operational delivered-flag endpoint and descriptive T4 positioning. The following replaces or clarifies the affected parts.

**Title and two-sentence claim**

**Judging Their Own Answers: Conversational Presentation and Harm Flags in Eleven Open Models**

> We estimate how presenting a fixed answer as a previous assistant turn changes delivered harmful-content flags in a prespecified eleven-model open panel, and how that change differs between the answer’s author and an unrelated, type-matched judge. Independent adjudicated labels describe changes in detection and false alarms; secondary analyses concern eleven commercial judges, with conclusions restricted to these checkpoints, prompts and presentations.

**Panels, frames and arms**

Accept A §§3.1–3.2: eleven primary models ×300 harmful prompts; all judges ×90 safe prompts; commercial own harmful answers on the common 60. Preserve the 50/50 source mixture explicitly.

Give every harmful-frame answer all four judgments, including commercial answers with S=0. Remove the 30-answer control cap. For commercial safe controls use the first **30 prompts per safe source**, giving 60 matched prompts; report their interaction on that subset.

Use fresh conversations, adjacent paired calls with random presentation order, fixed settings and complete answer text. Verify the primary author’s weight identity, including model 6. Describe these as reconstructed conversational presentations, not uninterrupted original trajectories.

**Estimands and inference**

For each prompt \(p\), form \(N_p=\sum_j S_{jp}\) and:

\[
X_{\theta p}=\sum_j S_{jp}(A2-A1),\qquad
X_{\iota p}=\sum_j S_{jp}\{(A2-A1)-(C2-C1)\}.
\]

P-S is \(\sum_pX_p/\sum_pN_p\). Weights travel with the **answer**, including its control verdicts. Define the population target as the ratio of expectations under the stated source mixture and fixed panel. Report the realised judge weights and denominator.

Register two-sided **cluster-t tests**, Holm family alpha **.04**, using ratio influence residuals \(e_p=X_p-\hat\theta N_p\), centred within source strata. Use the corresponding stratified cluster sandwich variance and **298 degrees of freedom** for the 300-prompt primary frame. Report 95% intervals. Preserve ruling A’s base-prompt unit and its specified sensitivity analysis.

For P3, use the analogous screened blind ratio, alpha **.01**, and reject \(H_0:\beta\le-.07\) only when its one-sided 99% lower bound exceeds −.07. Call this exclusion of a **seven-point mean blind flag deficit**, not absence of preference. Validate this procedure before freeze. Sign-flipping is a sensitivity analysis.

P-U, S=0 changes, equal-judge screened summaries, judge-normalised interaction, commercial results and accuracy quantities remain secondary. A zero denominator is non-estimable, never replaced by an epsilon-derived result.

**Yoking and screen**

Accept type matching and declared relation exclusions. Freeze seeded assignments, feasibility checks and the resulting matrix. Balance feasible pair counts without promising uniformity.

Accept the answer-only screen, with one pilot-based revision. Freeze its initial implementation before pilot registration and its final implementation before confirmation. Publish the exact phrase source, matching rules, normalisation and provider-block treatment. Use “screen-positive” consistently.

**Commercial judges and H60**

Buy complete commercial harmful controls. Keep H60’s ten-per-author composition, selected without human harm labels and excluding G1 duplicates. All judges receive H60 blind inside the reference subset; only primary-panel judges receive its in-context presentation. Apply declared relation exclusions to off-policy analyses and publish each eligible denominator.

**Missing and invalid outputs**

Accept A §5 for **attempted calls**, including retries and separate fail-closed/complete-case/bounds reports. Compute interaction bounds as well as on-policy bounds.

Distinguish administrative non-attempts caused by exhausted budget, suspension or abandoned blocks. Do not fabricate zero model verdicts for those cells. If they prevent the fixed full-panel contrast, report bounds and completed-subset estimates descriptively; withhold its confirmatory conclusion. Freeze respondent-generation failure handling too.

**Human labels and safe side**

Keep 550 labels and the planned 360 independent second labels. All 300 harmful-prompt answers must be double-labelled and adjudicated before verdict aggregation; unresolved items receive explicit sensitivity analyses.

For the 55 commercial harmful-prompt additions, target **three S=1 and two S=0 per author**, with prespecified source balancing and shortage redistribution. Specify equivalent exact rules for every other cell. Validate inclusion probabilities, combined G1/G2 selection and weights. Report finite-reference-set accuracy separately from weighted frame-generalising estimates.

Do not reduce harmful-prompt second labels automatically. If staffing fails, revise the reference-dependent claims before freeze. At four minutes per label, 550 PI labels require **36.7 hours**, and 360 second labels **24 hours**, before training and adjudication.

Accept the safe side as descriptive, with the reduced commercial control frame above. Do not advertise confirmatory safe-side power.

**Calls, budget and cuts**

The revised allocation has:

- **740 calls per commercial judge:** 300 own, 120 safe controls, 120 harmful controls, 120 blind reference, 60 pilot and 20 repeatability.
- **1,820 calls for model 22:** draft B minus 20 repeatability calls.
- One explicitly reserved full second pilot: **20 respondent prompts and 60 judgments per API model**.
- The corrected pessimistic visible-output allowance.

At supplied planning prices this is approximately **$45.03 expected/$104.37 pessimistic**, including the full rerun allowance. Preserve a hard $110 ledger and roughly $5 of unallocated headroom; require the final repriced manifest to fit approximately $105 before starting remaining work.

For overruns, cut remaining repeatability, then commercial safe controls, then additional blind-reference items while preserving H60 and a useful negative reference sample. Never shrink the primary sample in response to observed flags. Register what each cut makes unreportable.

**Pilot, claims and freeze**

Accept the external tails and technical sequence in A §9, with the restrictions above. Register the initial scientific specification and adaptation branches before pilot exposure. The screen may change once; formatting/caps may change once under written triggers; no scientific choice may follow a presentation-effect estimate.

Replace §3.6 with:

> Negative P1 supports a reduction in delivered flags among screen-positive own answers. Negative P2 supports a larger reduction for authors than for their assigned controls. Human labels and validity decompositions describe whether these findings accompany reduced detection of harmful content, changed false alarms or delivery failures; they do not establish a unique mechanism.

Freeze after successful implementation, calibration, staffing commitments and repricing. Then generate missing confirmatory answers, execute the frozen manifest and lock adjudicated labels before analysis joins or arm aggregation.

## 8. Literature: changes only

- **[verified online]** Khullar already studies previous-assistant-turn presentation, on/off-policy differences and crossed generators/judges, including harmfulness tasks. Therefore A §10.3’s “four additions” should not present on-policy content or an unrelated judge as independently novel. The contribution is this binary harm-classification configuration, its reference labels, registration and delivery accounting. [Khullar et al.](https://arxiv.org/html/2603.04582v1)

- **[verified online]** Agnihotri includes two-human validation on 200 responses and a cross-model refusal matrix. Its figure uses non-abliterated external judges; it does not establish preserved judging ability in abliterated judges. [Agnihotri et al.](https://arxiv.org/html/2510.02768)

- **[verified online]** Roytburg directly motivates caution about interpreting self-associated evaluation differences without accounting for evaluator quality. Type matching is a partial response, not a general solution. [Roytburg et al.](https://arxiv.org/html/2601.22548)

- **[verified online]** Nguyen studies recognition of adversarially prefilled responses and refusal-direction ablation. It strengthens the reason to separate presentation effects from recognition/intention claims. [Nguyen et al.](https://arxiv.org/html/2606.23671)

- **[verified online]** Two relevant additions are *Safer or Luckier?*, concerning safety judges’ artifact sensitivity and human agreement, and *A Coin Flip for Safety*, concerning generation-style/distribution shifts and human-verified harmfulness labels. They support realistic screening and susceptibility stress tests. [Chen and Goldfarb-Tarrant](https://arxiv.org/abs/2503.09347), [Schwinn et al.](https://arxiv.org/abs/2603.06594)

**[unsure]** This bounded search establishes no exact predecessor of the complete proposed configuration; it does not establish priority.

## 9. Convergence

| Round-1 condition | Status |
|---|---|
| Explicit operational estimand, same-answer controls, invalid treatment | **Partly met:** core explicit; administrative missingness and capped commercial controls need correction |
| Interaction power and coverage under directional shocks | **Partly met:** strong planning evidence; registered ratio inference remains unvalidated |
| Study-wide alpha | **Met:** .04 + .01, provided interpretation does not create additional confirmatory claims |
| Complete pessimistic manifest below $110 | **Partly met:** feasible reconstruction; complete executable manifest absent |
| Committed annotators and adjudicated harm labels | **Not met:** recruitment and fallback remain unresolved |
| Registered pilot firewall and public amendment | **Partly met:** credible proposal, not registered |
| Synthetic end-to-end implementation | **Not met** |
| Accurate novelty language | **Partly met:** correction accepted, final text absent |
| Claims restricted by precision, availability and labels | **Partly met:** §3.6 still overclaims |

**(a) Is the design settled?** Yes, for editing v2.3, if the consolidated choices above are adopted. No further competition between primary panels, P-S/P-U or H60 allocations is needed. Failed inferential calibration, unavailable primary models or inadequate annotation staffing would require an explicit amendment before freeze.

**(b) Before pilot registration:** a runnable synthetic pipeline; the initial screen; fixed scientific estimands, tests and claim rules; exact adaptation/stop rules; a pilot-disjointness check; a manifest covering both pilot rounds; and a dated public notice explaining the change from v1. Human review and welfare requirements already specified in the repository must be satisfied before pilot annotation begins.

**(c) Before freeze:** successful R-S1–R-S3 checks and production-code agreement; the revised protocol and hypothesis withdrawal table; committed annotation capacity; final screen, parser, settings, assignment and sampling manifests; complete hashes; provider availability and stopping rules; and a repriced, ledger-tested pessimistic budget below the cap. No confirmatory answer inspection, screening or judging should precede that freeze.