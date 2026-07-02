# Paper Target Templates

`paper_targets_v1.csv` is a paper-derived target subset template for comparing SCA
outputs against literature-style metrics. It is not a full MP-20, MPTS-52, or
other leaderboard dataset reproduction.

`reference_cifs_v1.csv` and `reference_cifs/` provide auditable prototype
references for the 22 generated challenge targets. These references are not
generated CIFs and are not DFT-relaxed ground truth. Fill `hull_reference_path`
or pass `--hull-reference` during the SCA benchmark run before interpreting
predicted hull/metastability metrics.

`comparator_values_v1.csv` contains contextual comparator values used by
`paper-benchmark-summary`. Comparator rows are audit aids; they should not be
reported as leaderboard claims unless the manifest explicitly uses the same
dataset scope and protocol.

## End-to-End Run

Build a generated run manifest:

```bat
python -m sca.cli build-paper-run-manifest ^
  --targets benchmarks\paper_targets\paper_targets_v1.csv ^
  --generated-folder "C:\Users\brown\Downloads\example created cifs" ^
  --out benchmarks\paper_targets\generated_manifest.csv ^
  --unmatched-out benchmarks\paper_targets\unmatched_generated_cifs.csv
```

Run the manifest benchmark:

```bat
set SCA_CHGNET_RELAX_STEPS=50
set SCA_CHGNET_RELAX_FMAX=0.1
set SCA_CHGNET_RELAX_OUT_DIR=reports\paper_targets_chgnet_relaxed

python -m sca.cli benchmark manifest benchmarks\paper_targets\generated_manifest.csv ^
  --evaluators pre_dft_validity,structure_match,novelty,chgnet_static,chgnet_relax,m3gnet_static,mace_static,sevennet_static,mlip_ensemble ^
  --out reports\paper_targets_results.csv ^
  --jsonl reports\paper_targets_results.jsonl
```

Summarize:

```bat
python -m sca.cli paper-benchmark-summary reports\paper_targets_results.csv ^
  --manifest benchmarks\paper_targets\paper_targets_v1.csv ^
  --comparator-values benchmarks\paper_targets\comparator_values_v1.csv ^
  --include-built-in-comparators ^
  --out reports\paper_benchmark_summary.csv ^
  --json reports\paper_benchmark_summary.json ^
  --markdown reports\paper_benchmark_report.md
```

Create the per-target failure diagnostics report:

```bat
python -m sca.cli paper-target-diagnostics ^
  --results reports\paper_targets_results.csv ^
  --manifest benchmarks\paper_targets\generated_manifest.csv ^
  --references benchmarks\paper_targets\reference_cifs_v1.csv ^
  --out reports\paper_target_diagnostics.csv ^
  --json reports\paper_target_diagnostics.json ^
  --markdown reports\paper_target_diagnostics.md
```

`B_structure_reproduction` is computable when `reference_cif_path` points to
the prototype references. `D_relaxation` is computable when `chgnet_relax`
successfully writes real relaxation columns. Predicted hull metrics remain not
computable until hull reference data or `predicted_energy_above_hull` is
supplied.
