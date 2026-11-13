## 1. Correctness

**No critical or major point remains in my inspection. Minor corrections are still needed before sign-off.** Both major fixes from round 10 are effective: collinear own/sibling coefficients become unidentified, and primary analysis rejects marked long-context verdicts.

- **D20:** The production decision applies the inclusive 30% threshold separately to P1 and P2, recomputes Holm, and leaves P3 unchanged. Empty denominators and zero variance still prevent rejection. Leave-one-out decisions use D20. **Fragility counts still use the earlier decisions**, however; see below.
- **D21:** The fixed phrase rule reads visible answer text and produces the requested descriptive counts. Its reported flag-rate denominator excludes undelivered verdicts, contrary to the registered delivered-flag scoring.
- **Missing-label bound:** I found no path by which it can pass where enumeration fails, for the registered finite inputs. The estimate range contains every assignment; the residual boxes bound the variance; the denominator minimum and degrees-of-freedom lower bound widen the interval. The residual-separation check conservatively rules out production-defined zero variance before permitting a statement. Insufficient support, a possible zero denominator, and limits touching zero prevent statements. A source with no contributing answers is handled conservatively.
- **Context fit:** Selection and message construction implement the intended measurements, but failed measurements can coexist with `fits_with_doubled_cap=True`, and `--round` does not restrict the answers selected.
- **D22:** The adapter splits before answer-status classification. Consequently the screen, judges’ messages, verdict parser, non-delivery coding and disclaimer measure receive the visible text. An opening `<think>` without a closing tag produces empty visible text, hence `truncated_empty` at the cap. Ordinary respondent and judge public logs exclude the block and retain its hash and length.
- **Reconstruction:** Judging messages use the split answer. **A split-off block can nevertheless reach a public-location file:** this sentinel-only script writes raw originals and decoded spans to `results/logs/reconstruction_v23.json`. The supplied model-17 row contains 277 reasoning characters. This is harmless sentinel material, not a route for benchmark answers, but the private-storage wording needs an explicit exception.
- **Rubric and pricing:** The two additions appear unchanged in the judge template. Repricing uses the increased rubric allowance.

**Conflict disclosure:** I am panel model 11, developed by OpenAI. The disclaimer, shared pilot-reporting and pricing findings also concern OpenAI models 3, 9 and 11. The D20 fragility, reconstruction and local-context findings concern the primary/local panel.

## 2. The tests

The supplied logs report **181 tests in eleven files, plus the passing synthetic end-to-end run**. The source contains 181 declared test functions.

The new collinearity, long-context rejection, within-sentence, delimiter, cap-exemption and midnight assertions protect their intended corrections. Reverting those corrections would break corresponding assertions. The bound tests compare forced bounds against enumeration across multiple statistics and label states, and require successful statements in strong cases.

Important gaps remain:

- `test_d20_sparse_changes` tests the one-test Holm rule by calling `holm_two` directly; it does not establish that `DN.decide` connects that rule correctly, nor test exactly 30%.
- Fragility tests still verify the earlier decision rule.
- Disclaimer tests check counts but not the rate denominator.
- D22 tests cover splitting, adapter parsing and respondent-log exclusion, but do not exercise the promised screen/message/non-delivery/judge-log chain end to end.
- Context-fit tests omit ordinary failures and mixed-round inputs.
- No offline test references the reconstruction script.

These gaps explain why the supplied passing run does not detect the findings below.

## 3. Consistency

The template matches Part A byte for byte after the specified extraction. Its SHA-256 is `8fbbd081…ecde10fa2`; the model-6 system hash and control-assignment hash also match their records. Part A has 7,661 characters.

The revised totals agree: **US$56.67 expected, US$101.34 pessimistic**, leaving US$22.66 below the freeze ceiling. Run (j)’s stored maximum D20 rejection rate is 0.02975, and its maximum without background is 0.00015, consistent with the rounded protocol figures.

The apparent manifest-hash mismatch is explained exactly by line endings: restoring CRLF without adding a final newline reproduces the holds’ recorded `2a426112…c5c56b`. I therefore do **not** count this as a repository defect.

Remaining inconsistencies include the old 3,300/4,500 prompt-token descriptions, the omitted D22 registration-condition entry, and model 6’s reconstruction claim. Both supplied model-6 rows retain `remaining_difference`; they do not establish the protocol’s “Nothing else differs” assertion.

All eleven supplied rendering records report `pass_v23=true`. The supplied cross-reference check reports 751 references and no dangling references.

## 4. Fingerprints

**No fingerprint input for stored runs (a)–(g) changed in the supplied diff.** This includes the inference, DGP, registered/label/safe simulation modules, frames, label-sampling and yoking modules, panel configuration and control assignment.

The assignment’s byte hash remains `b18714d2…b7ada41`. D20 is implemented outside the protected inference and simulation modules. I did not recompute complete row fingerprints.

## 5. Verdict

**Not quite ready for pilot-registration sign-off: the following minor corrections should land first. No critical or major correction remains.**

| Rank | Location | Concrete correction |
|---|---|---|
| **Minor** | [analysis/fragility_v23.py:44](E:/claude/_audit_copy/agentsControl_r22_round11_code/analysis/fragility_v23.py:44), `:62` | Use D20-aware decisions for production fragility counts, including hypothetical additions. Preserve an explicit earlier-rule mode for run (j)’s historical comparison. Currently a dense P2 that D20 does not reject can receive a positive fragility count. |
| **Minor** | [analysis/analyze_v23.py:868](E:/claude/_audit_copy/agentsControl_r22_round11_code/analysis/analyze_v23.py:868) | Divide registered delivered flags by attempted final verdicts, including undelivered outcomes as zero. With one harmful valid verdict and one parse error, the rate must be ½, not 1. Keep any conditional-on-delivery rate separately named. |
| **Minor** | [scripts/context_fit_v23.py:110](E:/claude/_audit_copy/agentsControl_r22_round11_code/scripts/context_fit_v23.py:110) | Require zero measurement failures before asserting fit; missing token counts should also count as failed measurements. Test one timeout alongside successful fitting calls and require no affirmative fit result. |
| **Minor** | [scripts/context_fit_v23.py:140](E:/claude/_audit_copy/agentsControl_r22_round11_code/scripts/context_fit_v23.py:140); [scripts/pilot_report_v23.py:405](E:/claude/_audit_copy/agentsControl_r22_round11_code/scripts/pilot_report_v23.py:405) | Filter tables to the selected round’s prompt IDs before context selection and delimiter counting. Currently combined round-1/round-2 runs contaminate these round-specific reports. |
| **Minor** | [scripts/check_reconstruction_v23.py:148](E:/claude/_audit_copy/agentsControl_r22_round11_code/scripts/check_reconstruction_v23.py:148); `docs/STUDY_PROTOCOL_v2.3.md:75` | Complete the whitespace comparison for model 6, including whitespace joined with other text in a token, and test it offline; meanwhile report the remaining difference as unverified. Document the sentinel-only exception to private reasoning storage. |
| **Minor** | [scripts/manifest_v23.py:6](E:/claude/_audit_copy/agentsControl_r22_round11_code/scripts/manifest_v23.py:6); `docs/STUDY_PROTOCOL_v2.3.md:1036`, `:1194`, `:916` | Update prompt assumptions to **3,450/4,700**, include D22 in registration conditions, and replace the obsolete rubric paraphrase about ignoring disclaimers. |
| **Minor** | [tests/test_judges_v23.py:1117](E:/claude/_audit_copy/agentsControl_r22_round11_code/tests/test_judges_v23.py:1117); `tests/test_sim_v23_analyze.py:1419` | Add the end-to-end D22 assertions and D20 boundary/connection cases described above. Run both test files offline after correction. |

A concrete author-run reproduction of the fragility mismatch, requiring no model call:

```bash
python -I -B - <<'PY'
import sys, numpy as np
sys.path.insert(0, "analysis")
import inference_v23 as I, density_v23 as D, fragility_v23 as F
N = np.full(300, 6.)
h = np.repeat([0, 1], 150)
a = np.zeros(300)
a[[3, 40, 77, 160, 201, 260]] = 6
b = np.tile(np.r_[np.ones(84), -np.ones(66)], 2)
b[234] = 1
x = {"th": a, "io": b, "be": b*0}
r = {k: I.cluster_ratio(v, N, h) for k, v in x.items()}
t = D.decide(r["th"], r["io"], r["be"], a, b, N)
print(bool(t["p2"]), int(F.counts(x, N, h)["p2"]))
PY
```

Predicted current output: `False 1`. Required production result after correction: `False 0`.

**Could not check:**

- Python execution, mutation tests or complete fingerprint recomputation.
- Live provider behaviour, rendering or reconstruction.
- Provenance of the updated D20 simulation run: its JSON is supplied, but its newly cited D20 execution log is absent.