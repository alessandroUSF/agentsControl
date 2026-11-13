## 1. Correctness

**One major validation issue remains. No critical issue was found.**

The round-11 corrections generally work as specified:

- Fragility counts now apply D20 to the original data and hypothetical additions, with separate denominators where necessary. Unavailable or unrejected tests receive zero; run (j) explicitly preserves the earlier rule.
- Disclaimer flag rates now divide by every final verdict. Calls without a final verdict remain excluded. A separate descriptive-count bug remains below.
- Context-fit failures and missing token counts prevent an affirmative fit result; overflows produce `False`, empty measurements produce `None`. Both round filters are connected correctly.
- Reconstruction now tests shortened whitespace. Both supplied model-6 records establish complete reuse—185/185 tokens—after changing three newlines to two.

The crossed filter matches `panel_v23.json` and the control rule for **distinct models**: 15 unordered non-sibling related pairs, recognized in both directions. Own cells and the three sibling pairs remain. Filtering precedes fitting, influence aggregation and degrees-of-freedom calculation. If every cell is removed, the inspected path returns zero observations, unavailable coefficients and `df=1`. Attempted, undelivered verdicts retain their prescribed scores; unattempted cells are omitted.

Run (k)’s P1/P2 categorical draws have the stated zero expectation and use production decisions. Its P3 background draws and low-discordance validation have defects listed below.

The parser accepts JSON booleans and rejects quoted booleans and numeric substitutes. Its tolerance of surrounding text, optional confidence and unrestricted reason length follows Section 11.5’s validity rule; those fields are not additional validity conditions.

**Conflict disclosure:** I am commercial-panel model 11, developed by OpenAI. The disclaimer and pilot-status findings also affect OpenAI models 3, 9 and 11. The simulation and crossed-fit findings concern the primary panel; the relation generator also correctly includes OpenAI’s same-developer pairs.

## 2. The tests

The supplied logs report **183 passing tests in eleven files, plus the passing synthetic end-to-end run**. I independently counted 183 declared test functions.

The changed assertions would detect reverting the fragility decision, flag-rate denominator, context-fit failure handling, round filters and related-cell exclusion. The reconstruction test exercises expected spans and the whitespace helper, although it does not exercise their integration through `examine()`.

Coverage gaps explain the remaining findings:

- **No test references `sim_v23_tails.py`.** Consequently neither invalid P3 support nor discarded calibration diagnostics is checked.
- `test_disclaimers` checks content counts and flag rates, but never asserts the screen-positive counts. Its added miniature fixture uses boolean screens, unlike production’s strings.
- Crossed tests cover unidentified and zero-variance fits, but not removal of every observation.
- Parser tests reject quoted `"false"`; no assertion protects the newly explicit template wording.

Add deterministic regression cases with each correction below. In particular, constant nonzero totals must distinguish “dense” from “test carried out,” and disclaimer fixtures must contain both `"positive"` and `"negative"`.

## 3. Consistency

The template’s recomputed SHA-256 is:

`c8fc4cc43044baeb85abe635a56df2e97e15890887c120856c24a776c7d70e2a`

It matches the protocol and summary. Its rubric section equals Part A after the specified trailing-newline removal. The control-assignment byte hash remains `b18714d2…b7ada41`.

Stored manifest totals agree with the documents: **US$56.67 expected and US$101.34 pessimistic**. Run (i)’s twelve coverage results agree with the text: **94.53%–95.38%**, all passing. Run (k)’s quoted figures match its JSON numerically, but that does not validate the scenarios generating them.

All eleven supplied rendering records report `pass_v23=true`; the cross-reference log reports **778 references, zero dangling references**.

The exposure-history additions agree across the protocol, inventory and D22. Remaining document and generator inconsistencies appear below.

## 4. Fingerprints

**No fingerprint input for stored runs (a)–(g) changed in the supplied diff.**

I checked the fingerprint constructors: the inference, DGP, registered/label/safe simulation modules, frame, yoking and label-sampling code are unchanged. Panel configuration and control assignment are also unchanged. The changed density and fragility modules are outside those stored-row fingerprints.

This confirms unchanged inputs relative to the supplied diff; it is not a complete recomputation of stored row fingerprints.

## 5. Verdict

**Not ready for pilot-registration sign-off yet. One major issue and the following minor corrections remain.**

1. **Major — discarded calibration failures invalidate the claimed low-discordance check.**  
   [analysis/sim_v23_tails.py:121](E:/claude/_audit_copy/agentsControl_r23_round12_code/analysis/sim_v23_tails.py:121) discards `diag`. `calibrate()` clips unattainable discordance targets and explicitly reports them through `unreached`. With the retained nonzero shocks, `q0=0` is unattainable; existing baseline calibration records show a floor around **0.041**, also above 0.025. Nevertheless run (k) retains the requested labels without reporting achieved values, and Section 17.1 claims it checked a clean effect. Preserve `rho`, the floor and `unreached` in every row; identify unattainable targets explicitly and correct Sections 8.1, 17.1 and A.4. These results cannot establish behavior at zero background discordance.

2. **Minor — two P3 scenarios generate impossible totals.**  
   [analysis/sim_v23_tails.py:69](E:/claude/_audit_copy/agentsControl_r23_round12_code/analysis/sim_v23_tails.py:69) can add −1 to a saturated −6 deficit while keeping `N=6`. The resulting −7 violates `|X_p|≤N_p`. For example, sample saturated deficits and symmetric background changes as disjoint outcomes with probabilities `pi`, `bg/2`, `bg/2`; retain the stated mean, document the probabilities and assert the support bound. Rerun and update the affected figures. The no-background P3 counterexample remains valid.

3. **Minor — density is reported as test availability.**  
   [analysis/sim_v23_tails.py:141](E:/claude/_audit_copy/agentsControl_r23_round12_code/analysis/sim_v23_tails.py:141) counts `p*_dense` into `carried_out_share_d20`. A dense statistic can have zero variance and no test. Count `p*_carried_out`; retain density separately if wanted. Test constant `X=1`, `N=6` across 300 prompts: density is one, availability is zero.

4. **Minor — disclaimer screen-positive counts include screen-negative answers.**  
   [analysis/analyze_v23.py:853](E:/claude/_audit_copy/agentsControl_r23_round12_code/analysis/analyze_v23.py:853) tests string truthiness. Both `"positive"` and `"negative"` pass. Replace it with `a.get("screen") == screen_mod.POSITIVE` and assert both screen-positive counters using production-shaped fixtures.

5. **Minor — pilot `declined` rules disagree with the clarified text.**  
   `docs/STUDY_PROTOCOL_v2.3.md:826` specifies the initial list throughout the pilot, whereas [src/run_judges_v23.py:483](E:/claude/_audit_copy/agentsControl_r23_round12_code/src/run_judges_v23.py:483) loads the active configuration, including a revision before round 2. To implement the text literally, use frozen initial rules for pilot status classification, separately from revised answer screening. Test a phrase added after round 1.

6. **Minor — regenerating the inventory restores superseded reuse claims.**  
   [scripts/data_inventory.py:213](E:/claude/_audit_copy/agentsControl_r23_round12_code/scripts/data_inventory.py:213), `:218` and `:242` still subtract sealed answers from generation requirements and say frame answers come from `full`. Implement D18 in the writer: every primary model needs 390 new frame answers, all frames need 6,180, and sealed answers supply none.

7. **Minor — synchronize remaining document copies.**  
   `docs/REGISTRATION_v2.3.md:221` still says every final crossed cell enters; add the related-cell exclusion. `docs/PI_DECISIONS.md:67` lacks “and commands” from the updated signing text; synchronize it. Its status and prerequisite lines `:5` and `:8` also omit later decisions and place D7 only at the freeze. Finally, clarify the historical 4,500-token endpoint-selection figures at protocol `:240` and decisions `:241`, which currently refer to the now-4,700-token pessimistic assumptions.

To recover run (k)’s omitted calibration evidence, the author can run this **without model calls or file writes**:

```bash
python -I -B - <<'PY'
import sys
sys.path[:0] = ["analysis", "src"]
import sim_v23_tails as T
D = T.dgp.design()
for name, kw in T.RS1.items():
    sc = dict(T.dgp.BASE, **kw)
    rng, _, _ = T.SR.streams("tails_" + name, T.SEED)
    _, rho, diag = T.dgp.calibrate(
        rng, D, sc, T.dgp.panel_quality(D, sc), 1000)
    print(name, rho, diag["q0_floor"], diag["unreached"])
PY
```

Expected: the zero-target rows report `rho=1`, a positive floor and an unreached `q0` target. Inspect the 0.025 rows likewise.

**Could not check:**

- Python execution, mutation testing or complete fingerprint recomputation.
- Live rendering, reconstruction or provider behavior.
- The underlying exposure events beyond the supplied records.