# Paper-Comparable Benchmarks

SCA paper benchmark summaries consume ordinary `sca benchmark` CSV outputs and
compute scalar A-E metrics for paper-style comparison. This is a framework for
paper-derived target subsets and comparable protocol checks. It is not a full
MP-20, MPTS-52, or other leaderboard reproduction unless the manifest explicitly
uses that full dataset and protocol.

## Benchmark Groups

- `A_validity`: parse, composition, pre-DFT validity, geometry, contacts.
- `B_structure_reproduction`: StructureMatcher match rates and RMS distances.
- `C_mlip_stability`: optional MLIP success, disagreement, and predicted hull
  threshold rates.
- `D_relaxation`: relaxation success, force, energy-drop, and RMSE deltas from
  real relaxation columns.
- `E_novelty_sun`: local uniqueness, local novelty, and SUN using predicted hull
  or MLIP consensus as the stability proxy.

Missing inputs produce not-computable rows instead of crashes.

## Templates

- `benchmarks/paper_targets/paper_targets_v1.csv`
- `benchmarks/paper_targets/comparator_values_v1.csv`

Fill `reference_cif_path` before interpreting `B_structure_reproduction`
StructureMatcher metrics. Fill or pass a hull reference before interpreting
predicted hull metrics.

## Example 1: Generated Folder

Build a run manifest that maps generated CIFs to paper target rows:

```bat
python -m sca.cli build-paper-run-manifest ^
  --targets benchmarks\paper_targets\paper_targets_v1.csv ^
  --generated-folder "C:\Users\brown\Downloads\example created cifs" ^
  --out benchmarks\paper_targets\generated_manifest.csv
```

Then benchmark that manifest so paper metadata such as `benchmark_id`,
`attempt_id`, and `target_formula` are preserved in the result CSV:

```bat
python -m sca.cli benchmark manifest benchmarks\paper_targets\generated_manifest.csv ^
  --evaluators pre_dft_validity,structure_match,chgnet_static,m3gnet_static,mace_static,sevennet_static,mlip_ensemble ^
  --path-col cif_path ^
  --formula-col target_formula ^
  --spacegroup-col target_space_group ^
  --target-cif-col target_cif_path ^
  --target-reference-id-col reference_id ^
  --method-col paper_source ^
  --query-id-col benchmark_id ^
  --out reports\paper_targets_manifest_results.csv ^
  --jsonl reports\paper_targets_manifest_results.jsonl
```

## Example 2: Summarize Against Manifest

```bat
python -m sca.cli paper-benchmark-summary reports\paper_targets_manifest_results.csv ^
  --manifest benchmarks\paper_targets\generated_manifest.csv ^
  --comparator-values benchmarks\paper_targets\comparator_values_v1.csv ^
  --include-built-in-comparators ^
  --out reports\paper_targets_manifest_summary.csv ^
  --json reports\paper_targets_manifest_summary.json ^
  --markdown reports\paper_targets_manifest_report.md
```

## Example 3: With Hull Reference

```bat
python -m sca.cli benchmark manifest benchmarks\paper_targets\generated_manifest.csv ^
  --evaluators pre_dft_validity,structure_match,predicted_hull,chgnet_static,m3gnet_static,mace_static,sevennet_static,mlip_ensemble ^
  --hull-reference data\reference_hulls\paper_targets_hull.csv ^
  --out reports\paper_targets_hull_results.csv ^
  --jsonl reports\paper_targets_hull_results.jsonl
```

## Output Columns

`paper-benchmark-summary` writes rows with:

- `summary_scope`
- `benchmark_group`
- `metric_name`
- `our_value`
- `n_total`
- `n_computable`
- `n_not_computable`
- `comparator_name`
- `comparator_value`
- `comparator_direction`
- `beats_comparator`
- `delta`
- `unit`
- `notes`

Comparator rows include metric name, comparator name, comparator value, direction,
our value, pass/fail, delta, units, and notes.

## Caveats

- Surrogate MLIP scores are not DFT.
- Local novelty is not global novelty.
- Paper-derived target subsets are not full MP-20/MPTS-52 leaderboard results
  unless explicitly scoped that way.
- Predicted hull metrics require local reference hull entries.
- Relaxation metrics require actual relaxed structures; SCA does not fake them
  from static energy outputs.
