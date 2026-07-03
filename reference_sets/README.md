# Evaluation-Only Reference Sets

Reference sets in this directory are for evaluation only unless a workflow
explicitly opts into using them for generation.

Expected layout:

```text
reference_sets/
  mp20/
  materials_project_snapshot/
  crystal_db_snapshot/
```

These folders can hold CIFs, manifests, or metadata snapshots used by SCA for:

- novelty checks
- nearest-neighbour/reference matching
- optional reference-set diagnostics
- evaluation-only S.U.N. benchmarking

They are not added to the generation Crystal-DB by default. In particular,
`reference_sets/mp20/` is not treated as a training benchmark or an MP-20
leaderboard split unless the calling command explicitly supplies exact MP-20
split metadata and reference CIF paths.

Large CIF collections and raw reference-set data are intentionally gitignored.
Keep only small documentation or manifest templates in git. Put downloaded or
exported reference snapshots under the relevant subdirectory locally.

Example evaluation-only command:

```bat
python -m sca.cli build-reference-manifest ^
  --cif-dir reference_sets/materials_project_snapshot/cifs ^
  --out reference_sets/materials_project_snapshot/metadata.csv ^
  --reference-set-name materials_project_snapshot

python -m sca.cli run-sun-benchmark ^
  --manifest local_runs/full_100_intent_benchmark_seeded_20260626_guided_spp_jsonschema_fixed/manifests/generated_cifs_manifest_for_sca.csv ^
  --reference-manifest reference_sets/materials_project_snapshot/metadata.csv ^
  --reference-id-col reference_id ^
  --out-dir local_runs/full_100_intent_benchmark_seeded_20260626_guided_spp_jsonschema_fixed/sun_benchmark
```

If no reference set is supplied, SCA still computes generated-set uniqueness and
marks novelty as not computable.

## Novelty Runs

Reference sets are evaluation-only. Do not commit reference CIF snapshots to git,
and do not add MP-20 or Materials Project snapshots to the generation Crystal-DB
unless a separate generation workflow explicitly opts into doing so.

Use exact-species matching by default. Add `--anonymous` only when you want
composition-agnostic prototype novelty checks.

## Stability Proxy Inputs

S.U.N. can compute hull-threshold rates only from real
`predicted_energy_above_hull`, `energy_above_hull`, or `e_above_hull` columns.
It does not fake hull stability from static model energies.

If CHGNet is installed, SCA can produce a real static surrogate-energy column:

```bat
python -m sca.cli benchmark manifest ^
  local_runs/full_100_intent_benchmark_seeded_20260626_guided_spp_jsonschema_fixed/manifests/generated_cifs_manifest_for_sca.csv ^
  --evaluators chgnet_static ^
  --out local_runs/full_100_intent_benchmark_seeded_20260626_guided_spp_jsonschema_fixed/sun_benchmark/chgnet_static_results.csv ^
  --jsonl local_runs/full_100_intent_benchmark_seeded_20260626_guided_spp_jsonschema_fixed/sun_benchmark/chgnet_static_results.jsonl
```

The resulting `chgnet_energy_per_atom` column can be passed to S.U.N. as a
static-energy proxy for energy summarization. It is not an energy-above-hull
column, so the 0.00/0.05/0.10/0.15 eV/atom hull rates remain not computable
unless an actual hull column is supplied.
