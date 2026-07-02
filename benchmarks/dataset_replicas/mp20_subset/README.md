# MP-20 Subset Scaffold

Purpose: subset or exact replication of CrysText and Lang2Str MP-20 structure
reproduction metrics.

Required input files:
- `targets.csv`: MP-20 target metadata and reference CIF paths.
- Generated CIF manifest with `benchmark_id`, `attempt_id`, and `cif_path`.
- Reference CIF bundle registered in `benchmarks/assets/reference_cif_bundles.csv`.

Expected columns:
`benchmark_id,cif_path,attempt_id,target_formula,target_space_group,reference_cif_path,reference_id,method,dataset_scope,notes`

Metrics computable:
N=1 match rate, N=K match rate, RMSD/RMSE, best-of-K RMSD, composition
satisfaction, and optional relaxed RMSD.

Comparator values:
CrysText MP-20 N=1 MR 57%, N=20 MR 73%, RMSE N=20 0.0243; Lang2Str
MP-20 MR 63.92%, RMSE 0.076, relaxed RMSE 0.055.

Warning: results are only `exact_protocol` when the full MP-20 protocol, target
set, attempts, and matching settings are used.
