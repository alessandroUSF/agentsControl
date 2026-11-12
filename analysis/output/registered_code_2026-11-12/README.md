# Appendix A with the registered code (12 November 2026)

Results of the simulations of Appendix A run with the inference as registered (Section 8.1: Σ_h (n_h − 1) = 298 degrees of freedom), before amendment D19. They are published because Appendix A.4 publishes every first and second result, passed or failed, and because they are the reason for amendment D19.

- `sim_v23_rs1.json`, `sim_v23_rs2.json`: R-S1 and R-S2 of 11 November 2026 (twelve-model panel); every check passes.
- `sim_v23_rs3.json`, `sim_v23_rs3_rerun.json`: R-S3 with ten commercial models (decision D17) and the second run of the one check that failed (`det_change_own_reg|i` in `low_failure_perfect|null`).
- `sim_v23_safe.json`, `sim_v23_safe_rerun.json`: run (d), safe-side intervals, both runs.
- `sim_v23_rare.json`, `sim_v23_rare_rerun.json`: run (e), rare flags; `rare_10|bound` fails checks 1 and 3 in both runs.
- `sim_v23_informative_unfinished.json`: run (b), stopped unfinished when run (e) showed that the inference had to be revised.
- `tables_v23.md`: the tables of A.1 to A.3 from these files.
- `logs/`: the console output of the runs of 12 November 2026.

The files carry the fingerprints of the registered code; the scripts do not reuse them with the code under amendment D19.
