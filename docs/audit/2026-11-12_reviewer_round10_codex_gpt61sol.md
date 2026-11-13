## 1. Correctness

**Two major points remain. No critical point found.** Findings below are by inspection; I did not execute Python, tests, models or API calls.

- **Judging messages:** `messages()` implements request → answer → rubric → instruction in both presentations, including retries. Model 6’s supplied system text is hash checked; other judges receive no added system message.
- **Context:** configurations specify 12,288 tokens for local judges and 4,096 for local respondents, with `truncate` and `shift` false. The runner selects canonical local overflows, changes the context to 32,768, and writes separate `_longctx` streams. Default analysis keeps those verdicts secondary. **However, marked long-context records can enter registered arrays through primary input; see M2.**
- **Costs and holds:** the revised calculations price judging without caching and retain the registered cuts. I found a stale stored hash, described below.
- **Crossed subset:** selection, reuse of existing presentations, delivered/fail-closed scoring, and omission of cells without final verdicts follow Section 8.8. The ordinary full-rank estimator agrees with the explicit dummy-variable formulation. **Its handling of collinear regressors is incorrect; see M1.** Empty fits return “not identified.”
- **Analysis:** Holm adjustment handles either test not being carried out; the interval note uses strict exclusion of zero. The hosted-completion rule now reads the registered arrays without letting missing block-5 calls suppress P1–P3. Influence and fragility calculations follow their stated definitions. One boundary-reporting sentence remains stale.
- **Labels and simulations:** prompt-bootstrap agreement, individual-labeller sensitivities and effective-number accuracy intervals follow the revised text. Runs (h) and (j) implement their specified scenarios. The reported sparse-change failure is disclosed in the protocol and left to D20.

**Conflict disclosure:** I am model 11, developed by OpenAI. The crossed-estimator finding concerns the local primary panel. Shared pilot reporting, accounting and unrestricted analysis-input paths also bear on OpenAI models 3, 9 and 11.

## 2. The tests

The supplied log reports **174 tests in eleven files, plus the passing synthetic end-to-end run**. I did not rerun them.

By inspection, reverting the message layout, system-file hash check, Holm adjustment, block-5 completion rule, prompt bootstrap, or separate long-context output path would fail corresponding assertions.

Coverage gaps remain:

- `test_sib_and_order` checks indicator values and Boolean output types, not identification under collinearity.
- Long-context tests establish default separation but never require primary input to reject `long_context=True`. The analysis test also draws replacement candidates without restricting judges to local models.
- `t_long_context_mode` captures messages but does not compare them with the original call, despite claiming that nothing else changes.
- No targeted assertion protects the new respondent-cap exemption for models 22 and 23.
- The midnight test detects the abort, but restores the actual date before retrying and never advances recorded timestamps. Its retry assertion therefore does not establish next-day recovery.

A concrete author-run reproduction of M1, requiring no model call:

```bash
python -I -B - <<'PY'
import sys
sys.path.insert(0, "analysis")
import crossed_v23 as x
r = x.fit(
    [4,6]*4, [4,4,6,6]*2,
    ["a","a","b","b","c","c","d","d"],
    [0,0,1,1,2,2,3,3], ["blind"]*8,
    [0,1,1,0,1,1,0,0], 4, [0,1,0,1])
print(r["quantities"]["delta_blind"])
PY
```

Predicted current result: an estimate of approximately `-0.5` with an available interval. Required result: `est=None`, `available=False`, reason `not identified`. Here own and sibling sum to one, so only their difference is identified.

For M2, add a negative case to `test_long_context`: pass a complete synthetic canonical table with its records marked `long_context=True` as primary `canon`. Run `python -I -B -X utf8 tests/test_sim_v23_analyze.py`. The new case must require rejection before registered results are produced; current inspection predicts acceptance.

## 3. Consistency

The principal settings and figures agree: **US$55.36 expected, US$99.43 pessimistic**, contexts 12,288/4,096/32,768, and the unchanged hosted respondent caps.

I independently checked:

- Judge-template SHA-256: `91082a8d…cde5131439b`.
- Model-6 system-file SHA-256: `521d9431…fa3c7ae6`.
- Crossed prompt-list digest: `2fbc1ff6…ad993e5a`.
- Control-assignment file SHA-256: `b18714d2…b7ada41`.

These match their recorded values.

**The holds’ manifest hash does not match.** `config/stage_holds.json:9` records `5a17fcf7…1441c37d`; the supplied manifest hashes to `ea351f0b…e6d102f7`. LF/CRLF variants did not explain the difference, and the manifest contains no substituted paths.

Two specification changes remain incomplete: the no-interval wording and delimiter-collision reporting. The manifest’s introductory caching description is also stale. Concrete repairs follow below.

The supplied cross-reference check reports 711 references and zero dangling references.

## 4. Fingerprints

**No fingerprint-input file for stored runs (a)–(g) changed in the supplied diff.** This includes `inference_v23.py`, `sim_v23_dgp.py`, `sim_v23_registered.py`, the label and safe simulation modules, and the unchanged frame, yoking, sampling and panel inputs.

The control-assignment file’s independently computed byte hash matches the unchanged protocol record. D19’s inference change already belongs to the round-9 baseline; this round changes reporting decisions around it, not that implementation.

I could not independently recompute the complete row fingerprints without executing Python.

## 5. Verdict

**The code is not ready for pilot-registration sign-off, apart from the PI’s decisions. Two major points remain.**

| Rank | Location | Required correction |
|---|---|---|
| **Major M1** | `analysis/crossed_v23.py:117` | When residual own and sibling regressors are collinear, dropping sibling and reporting the remaining coefficient as δ changes the model. Determine coefficient estimability in the full specified model; mark unidentified coefficients and dependent quantities unavailable. Add the reproduction above as a regression. |
| **Major M2** | `analysis/analyze_v23.py:205`, `:1670`, `:807` | Primary ingestion preserves `long_context` but never rejects it, and collection scores it normally. Thus an overridden `--verdicts` input or mixed file can supply long-context flags to registered arrays. Reject marked records at the primary-analysis boundary. Validate that sensitivity replacements are marked long-context records from local judges; currently the merge checks neither condition. |
| **Minor** | `analysis/analyze_v23.py:580` | `within_sentence()` treats every missing interval as “could not be estimated,” including an existing estimate with zero variance. Implement Section 2.4’s separate “has no interval” state, preserving its estimate and reason. |
| **Minor** | `scripts/pilot_report_v23.py:362` | Implement the delimiter-collision counts promised by Section 11.2. Count affected request/answer records containing the closing delimiters, report counts without text, and test both delimiters. |
| **Minor** | `config/stage_holds.json:9`; `scripts/manifest_v23.py:6` | Regenerate the manifest and then holds, verifying the recorded byte hash. Update the introduction to say no caching in either presentation. |
| **Minor** | `tests/test_judges_v23.py:805`, `:989`; `tests/test_runner_offline.py:1405` | Add explicit hosted-cap exemption assertions and original-message equality. Advance both dates and recorded timestamps across midnight, retaining the next day during recovery; require reuse of new-day evidence and replacement of old-day evidence. |

The new-layout rendering check remains an explicitly open Section 14.2 condition.

**Could not check:**

- Runtime tests, mutation tests or complete fingerprint recomputation.
- Live rendering of the revised layout across the local builds.
- Actual provider behaviour, billing or physical crash durability.