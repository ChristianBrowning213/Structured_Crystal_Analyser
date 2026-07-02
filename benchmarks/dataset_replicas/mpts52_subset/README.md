# MPTS-52 Subset Scaffold

Purpose: subset or exact replication of Lang2Str and Uni-3DAR MPTS-52 structure
reproduction metrics for harder large-cell targets.

Required input files:
- `targets.csv` with target formulas and reference CIF paths.
- Generated CIF manifest with attempts.

Expected columns:
`benchmark_id,cif_path,attempt_id,target_formula,reference_cif_path,reference_id,method,dataset_scope,notes`

Metrics computable:
Match rate, RMSD/RMSE, N=K match rate, and best-of-K RMSD.

Comparator values:
Lang2Str MPTS-52 MR 28.36%, RMSE 0.1424; Uni-3DAR MPTS-52 MR 32.44%,
RMSE 0.0684.

Warning: scaffold rows are examples only and are not a full MPTS-52 benchmark.
