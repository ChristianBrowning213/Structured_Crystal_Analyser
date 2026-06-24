# Paper Target Templates

`paper_targets_v1.csv` is a paper-derived target subset template for comparing SCA
outputs against literature-style metrics. It is not a full MP-20, MPTS-52, or
other leaderboard dataset reproduction.

Reference CIF paths are intentionally blank for many rows. Fill
`reference_cif_path` and `reference_id` before using `structure_match` metrics.
Fill `hull_reference_path` or pass `--hull-reference` during the SCA benchmark
run before interpreting predicted hull/metastability metrics.

`comparator_values_v1.csv` contains contextual comparator values used by
`paper-benchmark-summary`. Comparator rows are audit aids; they should not be
reported as leaderboard claims unless the manifest explicitly uses the same
dataset scope and protocol.
