# SCA Evaluators

SCA evaluators are pre-DFT screening tools. They help rank and triage generated
CIFs, but they do not prove thermodynamic stability or replace DFT relaxation,
energy-above-hull analysis, or experimental validation.

## Core Evaluators

- `pre_dft_validity`: parsing, composition, symmetry, multiplicity, bond/contact,
  geometry, duplicate, novelty, and optional ALIGNN-in-pipeline checks.
- `structure_match`: StructureMatcher target-CIF comparison, including exact and
  anonymous matching modes.
- `spp`: Statistical Pair Potential plausibility scoring from a versioned
  `spp.v1.json` artifact.

## Optional Surrogate/MLIP Evaluators

- `alignn`: optional ALIGNN formation-energy prediction.
- `chgnet_static`: optional CHGNet static surrogate energy and force magnitude.
- `m3gnet_static`: optional MatGL/M3GNet static surrogate energy.
- `mace_static`: optional MACE ASE calculator route. Requires `SCA_MACE_MODEL`.
- `sevennet_static`: optional SevenNet ASE calculator route. Requires
  `SCA_SEVENNET_MODEL`.
- `mlip_ensemble`: computes agreement metrics from available surrogate/MLIP
  energy columns.
- `property_targets`: compares predicted/surrogate property values against
  manifest targets.
- `predicted_hull`: computes predicted/surrogate energy above a local reference
  phase diagram. It does not call Materials Project or DFT.

Missing optional dependencies or missing model configuration are returned as
structured benchmark results. They should not crash a benchmark run.

## SPP Fields

The `spp` evaluator outputs:

- `spp_ok`
- `spp_total_score`
- `spp_score_per_atom`
- `spp_score_per_pair`
- `spp_tail_violation_count`
- `spp_missing_pair_count`
- `worst_species_pair`

Per-pair details are included under `evaluator_spp_details` in JSONL output.
Missing species-pair tables are counted in `spp_missing_pair_count`.

Example:

```bash
python -m sca.cli benchmark one examples/cifs/tiny_valid.cif \
  --evaluators pre_dft_validity,spp \
  --spp-artifact examples/spp.v1.json \
  --out reports/spp.csv \
  --jsonl reports/spp.jsonl
```

## MLIP Agreement Fields

The `mlip_ensemble` evaluator reads available energy columns from ALIGNN, CHGNet,
M3GNet, MACE, and SevenNet outputs. It emits:

- `mlip_energy_mean`
- `mlip_energy_std`
- `mlip_rank_mean`
- `mlip_rank_variance`
- `mlip_disagreement_flag`
- `mlip_consensus_stable_flag`

These values are model-dependent proxy metrics. Treat disagreement as a prompt to
inspect or relax candidates more carefully, not as a final stability decision.

## Benchmark Ranking

Benchmark rows include `benchmark_rank_score`, a deterministic pre-DFT triage
score. Lower is better. It combines validity gates, target-match penalties,
rediscovery/duplicate penalties, SPP score, available surrogate/MLIP energy, and
MLIP disagreement. It is intended for screening and queueing candidates, not for
claiming final physical stability.

## Property Targets And Predicted Hull

Benchmark manifests may include:

- `target_formation_energy_per_atom`
- `target_energy_above_hull`
- `target_band_gap`
- `target_property_name`
- `target_property_value`

Use `property_targets` to compare these targets against available predicted
columns. The evaluator reports deltas such as `formation_energy_error`,
`energy_above_hull_error`, `band_gap_error`, and `property_error`.

Use `predicted_hull` with a local CSV or JSON phase-entry file:

```bash
python -m sca.cli benchmark manifest examples/cif_manifest.csv \
  --evaluators chgnet_static,predicted_hull,property_targets \
  --hull-reference references/local_phase_entries.csv \
  --out reports/property_hull.csv \
  --jsonl reports/property_hull.jsonl
```

The local reference file should include `formula` and
`formation_energy_per_atom`; optional provenance fields such as `material_id`,
`source`, and `license_notes` may be retained for traceability. Output fields
include `predicted_energy_above_hull`, `hull_reference_count`, `hull_ok`, and
`decomposition_products`. These values are predicted/surrogate hull metrics
unless the supplied energies are real DFT energies.
