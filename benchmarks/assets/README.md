# Benchmark Asset Registries

These registries describe optional local assets used by literature-replication
benchmarks. They do not download large datasets and do not imply that an exact
paper protocol is available.

Files:
- `reference_cif_bundles.csv`: reference CIF bundles for structure matching.
- `hull_reference_bundles.csv`: local phase-entry bundles for predicted hulls.
- `property_target_bundles.csv`: property target bundles for MAE/hit-rate metrics.

The `available` column states whether the asset is present in this repository.
Missing assets should produce not-computable benchmark rows, not crashes.
