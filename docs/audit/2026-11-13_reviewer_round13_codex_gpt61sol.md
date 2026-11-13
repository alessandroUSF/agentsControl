## 1. Correctness

**No critical or major issue remains. The round-12 code corrections work as specified. One minor wording correction remains.**

**Conflict disclosure:** I am commercial-panel model 11, developed by OpenAI. The disclaimer and pilot-status corrections also affect OpenAI models 3, 9 and 11. The finding below concerns the primary-panel crossed comparison.

Run (k)’s nine R-S1 rows all record `unreached: []`. Independently calculating `(1−rho) × q0_independent + rho × q0_floor` from each stored calibration reproduces its target, with maximum rounding discrepancy below 3×10⁻¹⁷:

| Target q0 | Both shock SDs | Recorded floor | P1 power under θ = −0.05, with D20 |
|---|---:|---:|---:|
| 0 | 0 | 0 | 0.926 |
| 0.025 | 0.1 | approximately 0.0136 | 0.9975 |
| 0.05 | 0.3 | approximately 0.0408–0.0409 | 1.000 |

`calibrated()` checks the complete `unreached` list, including effect targets, and raises before simulating an unsuccessful row. An exception also prevents writing the final output file.

The P3 draw is now a valid categorical distribution for every configured row: probabilities π, bg/2, bg/2 and 1−π−bg produce totals −m, +1, −1 and 0. Its expectation is −mπ = −0.42, giving β = −0.07 with N = 6; every total satisfies |X|≤6.

`d20_counts()` correctly separates tests carried out from density. Its first counter reads `p*_carried_out`, incorporating positive variance as well as density; both shares reach the JSON output.

The disclaimer correction compares with `screen.POSITIVE`. Negative, absent and `"none"` screen values no longer count as positive.

The revised `declined` text matches the runner: each session loads the active screen configuration and passes it to status classification. Round 2 therefore uses the revised list when a revision occurred.

The inventory writer now implements D18 in the changed portions: 390 new frame answers per primary model, 4,680 primary answers, 1,500 commercial answers and 6,180 overall. Sealed answers reduce none of these requirements. The pilot and G1 notes also match the inventory’s D18 wording.

## 2. The tests

I counted **186 declared tests** in the eleven files and **186 named passing results** in the supplied log. The twelfth file’s synthetic end-to-end run also passes.

The changed tests exercise the intended regressions:

- `test_tails_p3_support` checks every configured P3 row’s support, approximate mean and categorical outcomes, plus rejection of excessive probability mass. Restoring additive background draws introduces forbidden outcomes.
- `test_tails_carried_out_not_dense` uses constant nonzero totals: density is one, variance is zero, and availability is zero. Counting density as availability fails its assertion.
- `test_tails_rs1_targets_reached` checks two representative corrected rows and rejects baseline shocks at q0 = 0. Reverting either the shock correction or failure guard breaks these checks.
- `test_disclaimers` checks both positive counters using string-valued screens. Restoring truthiness produces incorrect counts.

These are useful unit regressions. The calibration test covers two of nine rows; inspection of the stored output supplies the nine-row check. I did not execute mutations.

## 3. Consistency

The figures in Sections 8.1, 17.1 and A.4 match the second-run JSON at their stated precision, including:

- P3 rejection rates of 2.1%, 2.4%, 2.3%, 1.6%, 1.6% and 1.8%.
- P1/P2 rates up to 5.4% with twelve answers and 2.6% with six.
- P1 power falling to 0.926 and 0.998 under D20.
- The reported null rejection and test-availability ranges.

The second-run log agrees with the JSON. The first run is retained and explicitly described as superseded.

D5’s signing text, D7’s timing, the decision-status lines and registration prerequisites are synchronized. D16 now distinguishes historical 4,500-token selection assumptions from current 4,700-token planning; its linear-price interpolation argument is valid.

The recomputed template hash is `c8fc4cc4…6c7d70e2a`; the control-assignment file hash is `b18714d2…b7ada41`. Both match the documents. The template’s rubric equals Part A after the specified newline trimming. Stored manifest totals remain US$56.67 expected and US$101.34 pessimistic. The supplied cross-reference check reports 781 references and no dangling references.

The remaining crossed-rule wording discrepancy is listed below.

## 4. Fingerprints

**No fingerprint input for stored runs (a)–(g) changed in the supplied complete diff.**

I checked the registered, label and safe simulation fingerprint constructors. Their hashed modules—including inference, DGP, simulation modules, frames, yoking and label sampling—are unchanged. Configuration, frame inputs and control assignment are likewise unchanged.

The changed analysis, tails simulation, inventory writer, tests and documents are outside those fingerprints. This confirms unchanged inputs relative to round 12; it is not a complete recomputation of stored fingerprints.

## 5. Verdict

**The implementation is ready for pilot registration, apart from the PI’s outstanding decisions/actions and this minor text correction. No critical or major point remains.**

**Minor — explicitly retain own-answer cells in the crossed-rule wording.**  
[docs/REGISTRATION_v2.3.md:221](E:/claude/_audit_copy/agentsControl_r24_round13_code/docs/REGISTRATION_v2.3.md:221) now excludes related judge–author cells except sibling pairs, repeating [docs/STUDY_PROTOCOL_v2.3.md:624](E:/claude/_audit_copy/agentsControl_r24_round13_code/docs/STUDY_PROTOCOL_v2.3.md:624). Read literally, this also excludes an author judging its own answer: `yoking.related()` includes self-relations. The implementation correctly constructs related pairs only between distinct models and retains own cells.

Change both sentences to: **“Exclude cells only when judge and author are distinct, related models and are not one of the three sibling pairs; retain own-answer and sibling cells.”** This makes the text implementable literally and preserves the existing fitted model. No code change or simulation rerun is needed.

**Could not check:**

- Python execution, actual mutation tests or complete fingerprint recomputation.
- Inventory regeneration against sealed records; its logic was checked against documented counts.
- Independent recalibration of effect targets, live provider behavior or the underlying exposure events. No model/API calls or file changes were made.