### A.1 Size and power of the registered tests (R-S1; 10,000 replications per row)

| Scenario | Screen-positive answers | Family-wise error, null | P1 power, θ = −5 | P2 error, θ = −5 only | P2 power, ι = −5 | P1 error, ι = −5 only | P2 power, both −5 | P3 error at β = −7 | P3 power, β = 0 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 1,907 | 3.3 | 99.9 | 4.0 | 97.5 | 3.7 | 98.3 | 0.9 | 99.9 |
| shocks_0.6 | 1,907 | 3.3 | 99.3 | 3.7 | 97.8 | 3.7 | 98.5 | 1.1 | 99.9 |
| discordance_0.20 | 1,908 | 3.3 | 96.5 | 3.6 | 80.3 | 3.2 | 84.1 | 1.2 | 100.0 |
| low_failure | 1,046 | 3.3 | 96.0 | 3.7 | 81.1 | 3.3 | 85.3 | 1.0 | 98.5 |
| removed_se_0.30 | 1,907 | 3.5 | 100.0 | 4.3 | 97.4 | 3.6 | 99.1 | 1.2 | 99.8 |
| removed_se_0.50 | 1,908 | 3.4 | 99.9 | 4.1 | 97.0 | 3.9 | 98.5 | 1.2 | 99.6 |
| screen_0.7_0.6 | 1,949 | 3.1 | 100.0 | 4.1 | 98.5 | 3.8 | 99.3 | 1.0 | 100.0 |

Rates in percent; effects in percentage points. Nominal levels: family-wise 4.0, P3 1.0.

Boundary cases: in no replication was a denominator zero, an estimated variance zero or ι_W not estimable.

| Scenario | Coverage of the 95% interval: θ_S | ι_S | ι_W | β_S | Half-width: θ_S | ι_S | β_S | Same decision as the sign-flip test: P1 | P2 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 94.8 | 95.1 | 95.1 | 95.0 | 1.7 | 2.3 | 2.5 | 99.6 | 99.8 |
| shocks_0.6 | 95.2 | 95.0 | 94.8 | 95.0 | 2.0 | 2.2 | 2.5 | 99.7 | 99.6 |
| discordance_0.20 | 95.3 | 95.1 | 95.2 | 94.9 | 2.3 | 3.1 | 2.5 | 99.8 | 99.8 |
| low_failure | 95.0 | 95.2 | 95.1 | 95.0 | 2.2 | 3.0 | 3.0 | 99.5 | 99.6 |
| removed_se_0.30 | 94.7 | 95.0 | 95.0 | 95.2 | 1.7 | 2.2 | 2.6 | 99.6 | 99.7 |
| removed_se_0.50 | 95.0 | 95.1 | 95.1 | 95.0 | 1.8 | 2.3 | 2.7 | 99.7 | 99.7 |
| screen_0.7_0.6 | 95.4 | 95.4 | 95.5 | 94.6 | 1.6 | 2.1 | 2.4 | 99.7 | 99.8 |

Null rows. Half-widths in percentage points.

**Approximate power of the bound P3 for other margins.** Normal approximation with the simulated standard error of β̂_S and the 99% quantile of Student's t with 298 degrees of freedom (all 300 prompts with a screen-positive answer; with fewer, the domain degrees of freedom of Section 8.1 are fewer and the quantile slightly larger); not a simulation of the test.

| Scenario | Standard error of β̂_S | Margin 3: β = 0 | β = −1 | Margin 5: β = 0 | β = −1 | β = −2 | Margin 7: β = 0 | β = −1 | β = −2 | β = −3 |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1.27 | 51 | 22 | 94 | 79 | 51 | 100 | 99 | 94 | 79 |
| shocks_0.6 | 1.27 | 51 | 22 | 94 | 79 | 51 | 100 | 99 | 94 | 79 |
| discordance_0.20 | 1.27 | 51 | 22 | 94 | 79 | 51 | 100 | 99 | 94 | 79 |
| low_failure | 1.54 | 35 | 15 | 82 | 60 | 35 | 99 | 94 | 82 | 60 |
| removed_se_0.30 | 1.32 | 47 | 21 | 93 | 76 | 47 | 100 | 99 | 93 | 76 |
| removed_se_0.50 | 1.39 | 43 | 18 | 90 | 70 | 43 | 100 | 98 | 90 | 70 |
| screen_0.7_0.6 | 1.20 | 56 | 25 | 97 | 84 | 56 | 100 | 100 | 97 | 84 |

### A.2 Heterogeneous judges and delivery failures (R-S2; 10,000 replications per row)

| Scenario | True θ_S | True ι_S | True ι_W | P1 rejected | P2 rejected | P2 rejected and ι_W interval excludes zero on the same side | Coverage: θ_S | ι_S | ι_W |
|---|---|---|---|---|---|---|---|---|---|
| noise_shocks_only / zero | -0.32 | -0.16 | -0.16 | 3.1 | 2.5 | 2.5 | 94.8 | 94.7 | 94.7 |
| literal_null / zero | +0.00 | +0.00 | +0.00 | 2.2 | 2.2 | 2.2 | 94.9 | 95.2 | 95.1 |
| het / zero | -0.33 | -0.16 | -0.17 | 3.2 | 2.6 | 2.5 | 94.8 | 94.8 | 95.0 |
| het / null | +0.01 | -0.00 | -0.00 | 2.3 | 2.3 | 2.1 | 95.0 | 94.8 | 94.9 |
| het_alternating_all / zero | -1.42 | -0.19 | -0.26 | 24.5 | 3.3 | 3.1 | 95.3 | 95.1 | 95.0 |
| het_alternating_all / null | +0.01 | +0.01 | -0.04 | 2.2 | 2.1 | 2.0 | 95.1 | 95.3 | 95.5 |
| het_alternating_harmful / zero | -1.53 | -0.12 | -0.17 | 26.7 | 3.0 | 2.7 | 95.0 | 95.1 | 95.3 |
| het_alternating_harmful / null | +0.01 | +0.01 | -0.01 | 2.1 | 2.2 | 2.1 | 95.2 | 95.2 | 95.0 |
| het_aligned_all / zero | -1.95 | -2.10 | -0.47 | 48.6 | 37.8 | 6.3 | 94.8 | 95.0 | 94.7 |
| het_aligned_all / null | -0.00 | +0.00 | +1.63 | 2.2 | 2.1 | 1.1 | 95.1 | 95.5 | 95.3 |
| het_aligned_harmful / zero | -2.18 | -2.38 | -0.92 | 57.0 | 44.9 | 11.4 | 95.3 | 94.7 | 94.8 |
| het_aligned_harmful / null | -0.00 | -0.01 | +1.45 | 2.1 | 2.1 | 1.1 | 94.9 | 95.5 | 95.2 |
| het_invalid_10_15 / zero | -3.50 | -0.14 | -0.19 | 87.6 | 3.6 | 3.4 | 95.1 | 94.8 | 94.8 |
| het_invalid_10_15 / null | -0.01 | -0.01 | +0.01 | 2.2 | 2.2 | 2.1 | 95.4 | 95.1 | 95.0 |
| het_invalid_harm / zero | -12.59 | -0.13 | -0.31 | 100.0 | 3.8 | 3.3 | 95.2 | 95.3 | 95.3 |
| het_invalid_harm / null | -0.03 | +0.01 | +0.06 | 2.0 | 2.2 | 2.2 | 95.4 | 95.0 | 95.3 |
| het_aligned_all_invalid_harm / zero | -13.81 | -1.58 | -0.47 | 100.0 | 15.7 | 5.0 | 94.7 | 95.2 | 95.2 |
| het_aligned_all_invalid_harm / null | +0.00 | +0.01 | +0.39 | 2.3 | 2.4 | 2.2 | 95.2 | 94.9 | 94.9 |
| het_aligned_all / both | -5.01 | -5.02 | -3.39 | 100.0 | 98.7 | 81.4 | 95.0 | 94.7 | 94.8 |

True values in percentage points, from about one million independent prompt clusters. After the slash, `zero`: the three calibrated arm shifts are zero, and the judge shifts and invalid verdicts of the scenario still act; `null`: arm shifts calibrated so that θ_S = ι_S = 0; `both`: θ_S = ι_S = −5 points.

Boundary cases: in no replication was a denominator zero, an estimated variance zero or ι_W not estimable.

### A.3 Label-conditioned estimators (R-S3; 10,000 replications per scenario)

| Scenario | Statistic | Interval | True value | Bias | Replications with an interval | Coverage of the 95% interval | Half-width | Labelled answers in the class (mean; minimum) | Events (mean): positive; negative | Zero variance | Coverage of the replaced ratio interval |
|---|---|---|---|---|---|---|---|---|---|---|---|
| screen_0.9_0.8 / null | `harm_share_pos / all` | eff-n | +80.04 | -0.04 | 10,000 | 99.4 | 6.6 | 215; 215 | 161.0; 54.0 | 0 | 96.7 |
| screen_0.9_0.8 / null | `harm_share_neg / all` | eff-n | +10.02 | +0.00 | 10,000 | 99.5 | 9.2 | 60; 60 | 8.4; 51.6 | 1 | 93.3 |
| screen_0.9_0.8 / null | `screen_pass_harm / all` | eff-n | +90.00 | +0.09 | 10,000 | 99.9 | 9.8 | 169; 145 | 161.0; 8.4 | 1 | 93.8 |
| screen_0.9_0.8 / null | `det_blind_own / all` | eff-n | +74.98 | -0.00 | 10,000 | 97.9 | 7.9 | 161; 140 | 121.9; 39.1 | 0 | 94.9 |
| screen_0.9_0.8 / null | `det_blind_ctrl / all` | eff-n | +74.94 | -0.03 | 10,000 | 97.6 | 7.9 | 161; 140 | 121.8; 39.2 | 0 | 94.8 |
| screen_0.9_0.8 / null | `fa_blind_own / all` | eff-n | +11.72 | +0.01 | 10,000 | 97.7 | 9.9 | 54; 32 | 6.5; 47.5 | 21 | 91.7 |
| screen_0.9_0.8 / null | `fa_blind_ctrl / all` | eff-n | +11.71 | -0.02 | 10,000 | 97.6 | 9.9 | 54; 32 | 6.4; 47.6 | 15 | 91.2 |
| screen_0.9_0.8 / null | `det_change_own_reg / all` | ratio | -0.13 | +0.01 | 10,000 | 95.1 | 2.5 | 161; 140 | 10.9; 11.1 | 0 | – |
| screen_0.9_0.8 / null | `det_change_diff_reg / all` | ratio | -0.05 | +0.02 | 10,000 | 95.2 | 3.4 | 161; 140 | 18.9; 18.8 | 0 | – |
| screen_0.9_0.8 / null | `det_change_own_reg / r` | ratio | -0.12 | +0.01 | 10,000 | 95.4 | 2.6 | 128; 113 | 9.2; 9.3 | 0 | – |
| screen_0.9_0.8 / null | `det_change_diff_reg / r` | ratio | -0.04 | +0.02 | 10,000 | 95.5 | 3.4 | 128; 113 | 15.8; 15.8 | 0 | – |
| screen_0.9_0.8 / null | `det_change_own_reg / i` | ratio | -0.24 | +0.03 | 9,994 | 95.9 | 8.8 | 33; 17 | 1.7; 1.8 | 0 | – |
| screen_0.9_0.8 / null | `fa_change_own_reg / all` | ratio | +0.50 | -0.06 | 10,000 | 99.1 | 6.8 | 54; 32 | 2.3; 2.0 | 0 | – |
| screen_0.9_0.8 / null | `fa_change_diff_reg / all` | ratio | +0.25 | -0.07 | 10,000 | 99.1 | 9.5 | 54; 32 | 3.9; 3.7 | 0 | – |
| screen_0.9_0.8 / null | `det_change_own / all` | ratio | -0.13 | +0.05 | 10,000 | 95.0 | 6.0 | 161; 140 | 10.9; 11.1 | 0 | – |
| screen_0.9_0.8 / null | `fa_change_own / all` | ratio | +0.50 | -0.02 | 9,866 | 96.3 | 7.6 | 54; 32 | 2.3; 2.0 | 134 | – |
| screen_0.9_0.8 / both | `harm_share_pos / all` | eff-n | +80.04 | -0.04 | 10,000 | 99.4 | 6.6 | 215; 215 | 161.0; 54.0 | 0 | 96.7 |
| screen_0.9_0.8 / both | `harm_share_neg / all` | eff-n | +10.02 | +0.00 | 10,000 | 99.5 | 9.2 | 60; 60 | 8.4; 51.6 | 1 | 93.3 |
| screen_0.9_0.8 / both | `screen_pass_harm / all` | eff-n | +90.00 | +0.09 | 10,000 | 99.9 | 9.8 | 169; 145 | 161.0; 8.4 | 1 | 93.8 |
| screen_0.9_0.8 / both | `det_blind_own / all` | eff-n | +74.98 | -0.00 | 10,000 | 97.9 | 7.9 | 161; 140 | 121.9; 39.1 | 0 | 94.9 |
| screen_0.9_0.8 / both | `det_blind_ctrl / all` | eff-n | +74.94 | -0.03 | 10,000 | 97.6 | 7.9 | 161; 140 | 121.8; 39.2 | 0 | 94.8 |
| screen_0.9_0.8 / both | `fa_blind_own / all` | eff-n | +11.72 | +0.01 | 10,000 | 97.7 | 9.9 | 54; 32 | 6.5; 47.5 | 21 | 91.7 |
| screen_0.9_0.8 / both | `fa_blind_ctrl / all` | eff-n | +11.71 | -0.02 | 10,000 | 97.6 | 9.9 | 54; 32 | 6.4; 47.6 | 15 | 91.2 |
| screen_0.9_0.8 / both | `det_change_own_reg / all` | ratio | -6.38 | +0.01 | 10,000 | 96.1 | 2.8 | 161; 140 | 8.1; 18.1 | 0 | – |
| screen_0.9_0.8 / both | `det_change_diff_reg / all` | ratio | -6.30 | +0.02 | 10,000 | 95.7 | 3.6 | 161; 140 | 15.9; 25.1 | 0 | – |
| screen_0.9_0.8 / both | `det_change_own_reg / r` | ratio | -6.64 | +0.01 | 10,000 | 96.2 | 2.9 | 128; 113 | 6.7; 15.1 | 0 | – |
| screen_0.9_0.8 / both | `det_change_diff_reg / r` | ratio | -6.56 | +0.02 | 10,000 | 96.0 | 3.7 | 128; 113 | 13.2; 21.0 | 0 | – |
| screen_0.9_0.8 / both | `det_change_own_reg / i` | ratio | -4.74 | -0.01 | 9,994 | 95.6 | 9.4 | 33; 17 | 1.3; 2.9 | 0 | – |
| screen_0.9_0.8 / both | `fa_change_own_reg / all` | ratio | +0.50 | -0.05 | 10,000 | 98.7 | 7.1 | 54; 32 | 2.3; 2.0 | 0 | – |
| screen_0.9_0.8 / both | `fa_change_diff_reg / all` | ratio | +0.25 | -0.06 | 10,000 | 99.1 | 9.6 | 54; 32 | 3.9; 3.7 | 0 | – |
| screen_0.9_0.8 / both | `det_change_own / all` | ratio | -6.38 | +0.03 | 10,000 | 95.1 | 6.4 | 161; 140 | 8.1; 18.1 | 0 | – |
| screen_0.9_0.8 / both | `fa_change_own / all` | ratio | +0.50 | -0.02 | 9,866 | 96.3 | 7.6 | 54; 32 | 2.3; 2.0 | 134 | – |
| screen_perfect / null | `harm_share_pos / all` | eff-n | +100.00 | +0.00 | 10,000 | 100.0 | 1.2 | 215; 215 | 215.0; 0.0 | 10,000 | 100.0 |
| screen_perfect / null | `harm_share_neg / all` | eff-n | +0.00 | +0.00 | 10,000 | 100.0 | 3.9 | 60; 60 | 0.0; 60.0 | 10,000 | 100.0 |
| screen_perfect / null | `screen_pass_harm / all` | eff-n | +100.00 | +0.00 | 10,000 | 100.0 | 4.8 | 215; 215 | 215.0; 0.0 | 10,000 | 100.0 |
| screen_perfect / null | `det_blind_own / all` | eff-n | +74.97 | +0.02 | 10,000 | 97.2 | 7.2 | 215; 215 | 166.1; 48.9 | 0 | 94.9 |
| screen_perfect / null | `det_blind_ctrl / all` | eff-n | +74.94 | -0.02 | 10,000 | 97.1 | 7.2 | 215; 215 | 165.9; 49.1 | 0 | 94.6 |
| screen_perfect / null | `fa_blind_own / all` | eff-n | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / null | `fa_blind_ctrl / all` | eff-n | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / null | `det_change_own_reg / all` | ratio | +0.00 | +0.01 | 10,000 | 95.1 | 1.9 | 215; 215 | 14.1; 14.1 | 0 | – |
| screen_perfect / null | `det_change_diff_reg / all` | ratio | +0.01 | +0.01 | 10,000 | 95.1 | 2.5 | 215; 215 | 24.3; 24.2 | 0 | – |
| screen_perfect / null | `det_change_own_reg / r` | ratio | +0.02 | +0.01 | 10,000 | 95.3 | 2.1 | 140; 140 | 10.2; 10.1 | 0 | – |
| screen_perfect / null | `det_change_diff_reg / r` | ratio | +0.02 | +0.02 | 10,000 | 95.3 | 2.8 | 140; 140 | 17.3; 17.2 | 0 | – |
| screen_perfect / null | `det_change_own_reg / i` | ratio | -0.14 | -0.02 | 10,000 | 95.9 | 4.3 | 75; 75 | 3.9; 4.0 | 0 | – |
| screen_perfect / null | `fa_change_own_reg / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / null | `fa_change_diff_reg / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / null | `det_change_own / all` | ratio | +0.00 | +0.03 | 10,000 | 94.9 | 5.6 | 215; 215 | 14.1; 14.1 | 0 | – |
| screen_perfect / null | `fa_change_own / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / both | `harm_share_pos / all` | eff-n | +100.00 | +0.00 | 10,000 | 100.0 | 1.2 | 215; 215 | 215.0; 0.0 | 10,000 | 100.0 |
| screen_perfect / both | `harm_share_neg / all` | eff-n | +0.00 | +0.00 | 10,000 | 100.0 | 3.9 | 60; 60 | 0.0; 60.0 | 10,000 | 100.0 |
| screen_perfect / both | `screen_pass_harm / all` | eff-n | +100.00 | +0.00 | 10,000 | 100.0 | 4.8 | 215; 215 | 215.0; 0.0 | 10,000 | 100.0 |
| screen_perfect / both | `det_blind_own / all` | eff-n | +74.97 | +0.02 | 10,000 | 97.2 | 7.2 | 215; 215 | 166.1; 48.9 | 0 | 94.9 |
| screen_perfect / both | `det_blind_ctrl / all` | eff-n | +74.94 | -0.02 | 10,000 | 97.1 | 7.2 | 215; 215 | 165.9; 49.1 | 0 | 94.6 |
| screen_perfect / both | `fa_blind_own / all` | eff-n | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / both | `fa_blind_ctrl / all` | eff-n | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / both | `det_change_own_reg / all` | ratio | -5.00 | +0.01 | 10,000 | 96.0 | 2.2 | 215; 215 | 11.0; 21.0 | 0 | – |
| screen_perfect / both | `det_change_diff_reg / all` | ratio | -4.99 | +0.01 | 10,000 | 95.8 | 2.7 | 215; 215 | 21.1; 30.4 | 0 | – |
| screen_perfect / both | `det_change_own_reg / r` | ratio | -5.20 | +0.02 | 10,000 | 96.4 | 2.4 | 140; 140 | 7.8; 15.0 | 0 | – |
| screen_perfect / both | `det_change_diff_reg / r` | ratio | -5.19 | +0.02 | 10,000 | 96.2 | 3.0 | 140; 140 | 14.9; 21.6 | 0 | – |
| screen_perfect / both | `det_change_own_reg / i` | ratio | -3.71 | -0.04 | 10,000 | 95.7 | 4.7 | 75; 75 | 3.1; 6.0 | 0 | – |
| screen_perfect / both | `fa_change_own_reg / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / both | `fa_change_diff_reg / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| screen_perfect / both | `det_change_own / all` | ratio | -5.00 | +0.04 | 10,000 | 95.0 | 5.9 | 215; 215 | 11.0; 21.0 | 0 | – |
| screen_perfect / both | `fa_change_own / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| low_failure / null | `harm_share_pos / all` | eff-n | +40.09 | -0.04 | 10,000 | 98.3 | 7.9 | 215; 215 | 83.3; 131.7 | 0 | 95.8 |
| low_failure / null | `harm_share_neg / all` | eff-n | +1.82 | +0.02 | 10,000 | 99.0 | 4.8 | 60; 60 | 1.2; 58.8 | 3,066 | 69.2 |
| low_failure / null | `screen_pass_harm / all` | eff-n | +90.02 | +0.61 | 10,000 | 99.8 | 22.5 | 85; 57 | 83.3; 1.2 | 3,066 | 68.6 |
| low_failure / null | `det_blind_own / all` | eff-n | +74.57 | -0.06 | 10,000 | 97.5 | 10.7 | 83; 57 | 62.2; 21.1 | 0 | 94.4 |
| low_failure / null | `det_blind_ctrl / all` | eff-n | +74.58 | +0.08 | 10,000 | 97.6 | 10.6 | 83; 57 | 62.3; 21.0 | 0 | 94.5 |
| low_failure / null | `fa_blind_own / all` | eff-n | +11.23 | -0.05 | 10,000 | 98.0 | 6.3 | 132; 108 | 14.8; 116.8 | 0 | 93.6 |
| low_failure / null | `fa_blind_ctrl / all` | eff-n | +11.25 | +0.01 | 10,000 | 98.0 | 6.4 | 132; 108 | 14.9; 116.7 | 0 | 93.9 |
| low_failure / null | `det_change_own_reg / all` | ratio | -0.68 | -0.01 | 10,000 | 95.7 | 6.4 | 83; 57 | 6.7; 7.3 | 0 | – |
| low_failure / null | `det_change_diff_reg / all` | ratio | -0.31 | +0.02 | 10,000 | 95.0 | 8.8 | 83; 57 | 11.6; 11.8 | 0 | – |
| low_failure / null | `det_change_own_reg / r` | ratio | -0.68 | -0.02 | 10,000 | 95.3 | 6.7 | 74; 52 | 6.2; 6.7 | 0 | – |
| low_failure / null | `det_change_diff_reg / r` | ratio | -0.32 | -0.00 | 10,000 | 95.3 | 9.2 | 74; 52 | 10.6; 10.8 | 0 | – |
| low_failure / null | `det_change_own_reg / i` | ratio | -0.60 | +10.63 | 1 | 100.0 | 13.4 | 9; 1 | 0.5; 0.6 | 0 | – |
| low_failure / null | `fa_change_own_reg / all` | ratio | +0.49 | -0.01 | 10,000 | 95.4 | 4.1 | 132; 108 | 6.4; 5.7 | 0 | – |
| low_failure / null | `fa_change_diff_reg / all` | ratio | +0.24 | -0.02 | 10,000 | 95.4 | 5.6 | 132; 108 | 10.8; 10.5 | 0 | – |
| low_failure / null | `det_change_own / all` | ratio | -0.68 | +0.00 | 10,000 | 94.9 | 9.0 | 83; 57 | 6.7; 7.3 | 0 | – |
| low_failure / null | `fa_change_own / all` | ratio | +0.49 | +0.00 | 10,000 | 95.4 | 5.2 | 132; 108 | 6.4; 5.7 | 0 | – |
| low_failure / both | `harm_share_pos / all` | eff-n | +40.09 | -0.04 | 10,000 | 98.3 | 7.9 | 215; 215 | 83.3; 131.7 | 0 | 95.8 |
| low_failure / both | `harm_share_neg / all` | eff-n | +1.82 | +0.02 | 10,000 | 99.0 | 4.8 | 60; 60 | 1.2; 58.8 | 3,066 | 69.2 |
| low_failure / both | `screen_pass_harm / all` | eff-n | +90.02 | +0.61 | 10,000 | 99.8 | 22.5 | 85; 57 | 83.3; 1.2 | 3,066 | 68.6 |
| low_failure / both | `det_blind_own / all` | eff-n | +74.57 | -0.06 | 10,000 | 97.5 | 10.7 | 83; 57 | 62.2; 21.1 | 0 | 94.4 |
| low_failure / both | `det_blind_ctrl / all` | eff-n | +74.58 | +0.08 | 10,000 | 97.6 | 10.6 | 83; 57 | 62.3; 21.0 | 0 | 94.5 |
| low_failure / both | `fa_blind_own / all` | eff-n | +11.23 | -0.05 | 10,000 | 98.0 | 6.3 | 132; 108 | 14.8; 116.8 | 0 | 93.6 |
| low_failure / both | `fa_blind_ctrl / all` | eff-n | +11.25 | +0.01 | 10,000 | 98.0 | 6.4 | 132; 108 | 14.9; 116.7 | 0 | 93.9 |
| low_failure / both | `det_change_own_reg / all` | ratio | -13.15 | +0.02 | 10,000 | 94.9 | 7.3 | 83; 57 | 4.5; 15.3 | 0 | – |
| low_failure / both | `det_change_diff_reg / all` | ratio | -12.79 | +0.06 | 10,000 | 95.1 | 9.5 | 83; 57 | 9.1; 18.7 | 0 | – |
| low_failure / both | `det_change_own_reg / r` | ratio | -13.51 | +0.01 | 10,000 | 95.2 | 7.6 | 74; 52 | 4.1; 14.0 | 0 | – |
| low_failure / both | `det_change_diff_reg / r` | ratio | -13.14 | +0.03 | 10,000 | 95.1 | 9.9 | 74; 52 | 8.2; 17.1 | 0 | – |
| low_failure / both | `det_change_own_reg / i` | ratio | -9.82 | +2.99 | 1 | 100.0 | 12.3 | 9; 1 | 0.4; 1.3 | 0 | – |
| low_failure / both | `fa_change_own_reg / all` | ratio | +0.49 | -0.05 | 10,000 | 95.8 | 4.4 | 132; 108 | 6.4; 5.7 | 0 | – |
| low_failure / both | `fa_change_diff_reg / all` | ratio | +0.24 | -0.07 | 10,000 | 95.5 | 5.9 | 132; 108 | 10.8; 10.5 | 0 | – |
| low_failure / both | `det_change_own / all` | ratio | -13.15 | +0.08 | 10,000 | 94.4 | 10.3 | 83; 57 | 4.5; 15.3 | 0 | – |
| low_failure / both | `fa_change_own / all` | ratio | +0.49 | +0.00 | 10,000 | 95.4 | 5.2 | 132; 108 | 6.4; 5.7 | 0 | – |
| low_failure_perfect / null | `harm_share_pos / all` | eff-n | +100.00 | +0.00 | 10,000 | 100.0 | 1.4 | 185; 160 | 184.8; 0.0 | 10,000 | 100.0 |
| low_failure_perfect / null | `harm_share_neg / all` | eff-n | +0.00 | +0.00 | 10,000 | 100.0 | 2.3 | 90; 67 | 0.0; 90.2 | 10,000 | 100.0 |
| low_failure_perfect / null | `screen_pass_harm / all` | eff-n | +100.00 | +0.00 | 10,000 | 100.0 | 13.9 | 185; 160 | 184.8; 0.0 | 10,000 | 100.0 |
| low_failure_perfect / null | `det_blind_own / all` | eff-n | +74.56 | -0.05 | 10,000 | 98.0 | 7.8 | 185; 160 | 140.5; 44.3 | 0 | 95.1 |
| low_failure_perfect / null | `det_blind_ctrl / all` | eff-n | +74.58 | +0.07 | 10,000 | 97.7 | 7.8 | 185; 160 | 140.7; 44.1 | 0 | 94.7 |
| low_failure_perfect / null | `fa_blind_own / all` | eff-n | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| low_failure_perfect / null | `fa_blind_ctrl / all` | eff-n | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| low_failure_perfect / null | `det_change_own_reg / all` | ratio | +0.02 | -0.01 | 10,000 | 95.5 | 3.8 | 185; 160 | 14.8; 14.8 | 0 | – |
| low_failure_perfect / null | `det_change_diff_reg / all` | ratio | +0.02 | +0.00 | 10,000 | 95.2 | 5.2 | 185; 160 | 25.0; 25.0 | 0 | – |
| low_failure_perfect / null | `det_change_own_reg / r` | ratio | +0.04 | -0.00 | 10,000 | 95.5 | 4.1 | 140; 140 | 12.1; 12.0 | 0 | – |
| low_failure_perfect / null | `det_change_diff_reg / r` | ratio | +0.03 | +0.00 | 10,000 | 95.6 | 5.6 | 140; 140 | 20.2; 20.1 | 0 | – |
| low_failure_perfect / null | `det_change_own_reg / i` | ratio | -0.13 | -0.04 | 9,958 | 94.6 | 10.4 | 45; 20 | 2.7; 2.8 | 42 | – |
| low_failure_perfect / null | `fa_change_own_reg / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| low_failure_perfect / null | `fa_change_diff_reg / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |
| low_failure_perfect / null | `det_change_own / all` | ratio | +0.02 | +0.02 | 10,000 | 94.6 | 6.4 | 185; 160 | 14.8; 14.8 | 0 | – |
| low_failure_perfect / null | `fa_change_own / all` | ratio | n/a | n/a | 0 | n/a | n/a | 0; 0 | n/a | n/a | n/a |

All 7 scenarios, every replication: labelled answers 567, second labels 381, challenge set 70, API reference subset 130, unfilled quota 0, answers with no chance of selection 0. Values in percentage points.

- **Interval.** `eff-n`: the approximate interval on the effective number of answers (Section 9.5). `ratio`: the cluster ratio interval of Section 8.
- **Replications with an interval.** The class holds at least 20 labelled answers. For a ratio interval the estimated variance is also above zero. Bias and coverage are computed over these replications.
- **Events.** For a rate: labelled answers of the class with the property and without it. For a change: labelled answers of the class that gain a flag in context and that lose one. For a difference between authors and controls the sign is that of the difference.
- **Zero variance.** Replications with at least 20 labelled answers in the class in which the estimated variance of the ratio is zero.
- **Last column.** The coverage of the cluster ratio interval for the same rate. This interval is not reported. It has no width when no event, or nothing but events, is observed.

