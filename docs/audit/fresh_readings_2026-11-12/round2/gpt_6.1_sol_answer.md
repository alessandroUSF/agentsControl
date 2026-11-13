The study has a defensible core and could produce a useful paper. **I would not register or run it as written yet.** The main remaining problem is substantive: the statistical validation misses a sparse-change setting in which the confirmatory tests can reject far too often.

The strongest features are the comparisons on identical answers, the separation of delivered flags from judgments, the human reference sample, and the restrictions on mechanism claims. Those choices support a study of conversational presentation. They do not establish self-recognition or self-preference, and the protocol generally handles that distinction well.

I would require the following before pilot registration.

1. **Revise the validation and handling of sparse presentation changes.**

   Run (h) retains the baseline background discordance between presentations. Run (e) makes screen-positive answers rare. Neither adequately addresses **many screen-positive answers with very few presentation changes**—a relevant possibility for deterministic judges.

   Here is a concrete counterexample to the registered inference. Suppose every prompt has six screen-positive answers, and the controls’ presentation change is always zero. Let the author’s total change, summed over those six answers, follow this distribution independently across prompts in both sources:

   | Author’s total change on a prompt | Probability |
   |---|---:|
   | +6 | 1/150 |
   | −1 | .04 |
   | 0 | Remaining probability |

   Its expectation is zero: \(6/150-.04=0\). Thus **both P1 and P2 nulls hold**. There are 1,800 screen-positive answers, and D19 still assigns 298 degrees of freedom.

   Nevertheless, in about 13.4% of studies, none of the rare positive prompts appears. Those studies usually contain enough small negative changes for both t tests to reject. Using the protocol’s variance formula and Holm rule, a subset of these events alone gives a false rejection probability of **about 13.2%**, against the nominal family level of 4%.

   This is a constructed stress case, not a prediction of the results. But it demonstrates a material failure in a setting the study could encounter. Printing influence diagnostics or calling the level “nominal” does not repair it.

   Before registration, add simulations with common screen-positive answers, zero or very low background discordance, and asymmetric, clustered changes. Then register a justified inference procedure or an explicit descriptive-only fallback for the problematic setting. Simply changing the degrees of freedom again is not necessarily sufficient.

   Also correct the Bahadur–Savage argument. As stated, the impossibility claim is too broad for this study: its cluster contributions have known finite bounds. Distribution-free inference for bounded means exists, although it can sacrifice considerable power.

2. **Obtain a statistical justification for the human-label inference.**

   Section 9.5 combines a complete frame of verdicts with a stratified subsample of labels. That is a two-phase estimation problem. Reusing `cluster_ratio` does not, by itself, establish that its variance captures both prompt sampling and label sampling.

   The required D7 reader should specifically examine:

   - sampling without replacement within model, source and screen cells;
   - the variance of the label-assisted numerator and its ratio denominator;
   - the estimated \(b_g\);
   - sparse label classes and the effective-number intervals.

   Treating an estimated calibration coefficient as fixed can be justified in some survey estimators. I would therefore **not declare the estimator invalid merely because \(b_g\) is estimated**. But the justification and its conditions need to be supplied. Agreement between analysis and simulation code establishes implementation consistency; it does not independently validate their shared statistical assumptions.

   This review is already a registration condition. It should remain a substantive requirement.

3. **Resolve the crossed-subset scoring ambiguity.**

   Section 8.8 says it uses delivered-flag scoring, under which an attempted but invalid verdict contributes zero. Yet its identification example refers to having “no sibling cell with a delivered verdict,” and its simulation introduces cells “without a verdict.”

   These descriptions leave unclear whether unsuccessful attempted calls remain as zero-valued observations or are removed from the regression.

   That choice changes the estimand and can introduce selection by delivery. It also changes identification: if unsuccessful calls remain as zeros, the absence of a valid sibling verdict does **not** necessarily remove variation from the sibling regressor.

   Specify separately how valid, unsuccessful attempted, and genuinely unattempted calls enter the fit. Make the simulation follow that rule, and check cases where delivery depends on presentation, harmfulness or the own/sibling relationship.

4. **Make the rubric and conclusion templates unambiguous.**

   The sexual-content rule requires lack of authorization for explicit content about a real person. Its example, however, labels an explicit story about a named real actor harmful without stating the authorization condition. The reading rule prohibits looking anything up, and no default is given for unknown authorization.

   Decide what labellers and judges should do when authorization is unstated, then align the condition and example. This is a measurement decision, not merely copyediting.

   I would also clarify that ignoring disclaimers applies to the **harm label**; behaviour classification still needs to distinguish a warning from an actual refusal.

   Two reporting rules need correction:

   - The P3 crossed-companion sentence cannot simply inherit the P2 wording about a “corresponding difference.” P3 excludes a specified deficit; it does not establish a directional difference. Give \(\delta_{\text{blind}}\) its own reporting rule.
   - Replace the required assertion that “most screen-positive answers come from refusal-removed builds” with a requirement to report the **observed proportion**. A registration should not require an empirical prediction to be stated regardless of the results.

5. **Reconcile the executable specification across the documents.**

   Several discrepancies remain:

   - The summary says the 12 November additions are unfinished and reports 158 tests; the full protocol says they are implemented and reports 173 tests plus the complete synthetic run.
   - The template’s ABOUT section describes a system-message exception for model 6 but omits the retained built-in prompts of models 20 and 21.
   - Some historical descriptions of “exact” intervals and unfinished work remain alongside their replacements.
   - The assertion that every primary answer fits every local judge rests on a 25% allowance between tokenizers. That allowance is an assumption, not a bound.

   Produce one synchronized registration snapshot and regenerate its hashes. Verify the actual rendered messages, including built-in prompts and model-specific additions. Treat context fit as something measured, with the registered overflow procedure governing exceptions.

   Also distinguish “the estimate could not be computed” from “an interval was unavailable or withheld.” The current claim templates sometimes describe the latter as non-estimability.

6. **Complete the existing registration conditions.**

   The documents themselves show that registration prerequisites remain open: independent human methods review, provider-policy records, the Llama licence assessment, welfare arrangements, disclosures, and the signed exposure statement. Annotation also requires the stated institutional determination and agreements before answers are shown.

   The provider review should assess the actual calls, including inserted assistant turns. Describing them as classification does not itself establish their contractual treatment. Whether notice or permission is necessary should follow the applicable terms.

The hosted-panel rule is operationally brittle: one unfinished required call can eliminate all confirmatory conclusions. It is nevertheless a coherent choice if fixed beforehand and knowingly accepted. I would not require another panel redesign solely to remove that risk. Likewise, the screen and the seven-point P3 margin are defensible as explicitly limited operational choices.

**My recommendation is a focused revision, followed by the already-required independent statistical review.** The presentation experiment is worth carrying out. The sparse-change inference problem should be resolved before registration, rather than left as a limitation discovered after the results.

This assessment concerns the supplied documents and the counterexample calculation; I have not independently audited the repository, external policies, or cited literature.