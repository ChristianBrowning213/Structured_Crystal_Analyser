# SCA — Structured Crystal Analyser

## Purpose

SCA is an internal Python toolkit for pre-DFT evaluation of generated crystal structures. It is designed for comparing text-to-crystal workflows against CrystaLLM-style generated-structure evaluation before any expensive first-principles calculations.

## Install

```bash
pip install -e .
```

For development:

```bash
pip install -r requirements-dev.txt
pytest -q
```

ALIGNN is optional. Install it only when surrogate formation-energy scoring is needed:

```bash
pip install alignn
```

## CrystaLLM-Style Pre-DFT Evaluation

The `crystallm-eval` pipeline checks:

- CIF parse/processability
- composition and target formula consistency
- declared, detected, and target space-group consistency
- atom-site multiplicity consistency when explicit CIF multiplicities exist
- bond/contact reasonableness
- volume, density, and lattice geometry warnings
- duplicate grouping with `StructureMatcher`
- novelty/rediscovery against an optional reference corpus
- optional ALIGNN formation-energy scoring

SCA does not run DFT and does not compute real energy above hull.

## CLI Usage

Single CIF:

```bash
sca crystallm-eval one examples/cifs/tiny_valid.cif \
  --target-formula NaCl \
  --target-space-group 1 \
  --out reports/one.json \
  --require-spacegroup false \
  --alignn false
```

Folder:

```bash
sca crystallm-eval folder examples/cifs \
  --target-formula NaCl \
  --out reports/pre_dft_eval.csv \
  --jsonl reports/pre_dft_eval.jsonl \
  --require-spacegroup false \
  --alignn false
```

Manifest:

```bash
sca crystallm-eval manifest manifests/generated_candidates.csv \
  --path-col cif_path \
  --formula-col target_formula \
  --spacegroup-col target_space_group \
  --method-col method \
  --query-id-col query_id \
  --alignn true \
  --out reports/pre_dft_eval.csv \
  --jsonl reports/pre_dft_eval.jsonl
```

Manifest with novelty checking against a reference CIF folder:

```bash
sca crystallm-eval manifest manifests/generated_candidates.csv \
  --path-col cif_path \
  --formula-col target_formula \
  --spacegroup-col target_space_group \
  --method-col method \
  --query-id-col query_id \
  --novelty true \
  --reference-folder data/reference_mp_subset \
  --alignn false \
  --out reports/pre_dft_eval.csv \
  --jsonl reports/pre_dft_eval.jsonl
```

Novelty can also load references from a manifest:

```bash
sca crystallm-eval folder examples/cifs \
  --novelty true \
  --reference-manifest data/reference_manifest.csv \
  --reference-path-col cif_path \
  --reference-id-col material_id \
  --out reports/pre_dft_eval.csv \
  --jsonl reports/pre_dft_eval.jsonl
```

Summarize:

```bash
sca summarize reports/pre_dft_eval.csv \
  --group-col method \
  --out reports/pre_dft_summary_by_method.csv
```

Select top-k candidates for later DFT:

```bash
sca select-top-k reports/pre_dft_eval.csv \
  --group-cols method,query_id \
  --k 5 \
  --out reports/top5_for_dft.csv
```

The original ALIGNN-only commands remain available under `sca alignn`.

## Python Library Usage

```python
from sca.pipelines.crystallm_style import evaluate_one_cif

record, structure = evaluate_one_cif(
    "examples/cifs/tiny_valid.cif",
    target_formula="NaCl",
    target_space_group="1",
    require_spacegroup=False,
    run_alignn=False,
)
print(record.model_dump())
```

Batch helpers:

```python
from sca.batch import evaluate_manifest

records = evaluate_manifest(
    "examples/cif_manifest.csv",
    path_col="cif_path",
    formula_col="target_formula",
    spacegroup_col="target_space_group",
    method_col="method",
    query_id_col="query_id",
)
```

## Manifest Format

A manifest CSV can include:

```csv
cif_path,target_formula,target_space_group,method,query_id
cifs/tiny_valid.cif,NaCl,1,crystallm,q001
```

`cif_path` is required by default. Relative paths are resolved relative to the manifest file.

## Output Columns

Reports include per-CIF fields for:

- identity: `run_id`, `method`, `query_id`, `input_path`, `file_name`
- parsing and composition: `parse_ok`, `formula`, `reduced_formula`, `target_formula`, `target_formula_match`
- symmetry: `declared_space_group`, `detected_space_group`, `target_space_group`, `space_group_consistent`
- multiplicity: `multiplicity_checked`, `multiplicity_consistent`
- bonds and geometry: `bond_reasonableness_score`, `bond_lengths_reasonable`, `min_distance`, `num_bad_contacts`, `volume`, `volume_per_atom`, `density`, `geometry_ok`
- uniqueness and novelty: `duplicate_group_id`, `is_duplicate`, `is_unique_representative`, `novelty_checked`, `nearest_reference_id`, `known_match`, `novel_by_structure_matcher`, `novelty_error`
- optional ALIGNN: `alignn_ok`, `alignn_model`, `formation_energy_per_atom`
- workflow fields: `pre_dft_valid`, `pre_dft_rank_score`, `selected_for_dft`, `error_type`, `error_message`

## ALIGNN Caveat

ALIGNN formation energy is a surrogate pre-DFT prediction. It is not DFT, not a relaxed energy, and not energy above the convex hull.

If the installed ALIGNN Python API is incompatible, configure a subprocess fallback with `SCA_ALIGNN_COMMAND`. The command may use `{input}` for a temporary POSCAR path and `{model}` for the model name.

```bash
export SCA_ALIGNN_COMMAND="python -m alignn.scripts.pretrained --model {model} --file {input}"
```

## Top-K Selection For Later DFT

`select-top-k` sorts by `pre_dft_rank_score` within each requested group and writes selected rows only, setting `selected_for_dft=true` in the output. Lower scores are better. Failed parses, formula mismatches, bad contacts, geometry failures, multiplicity inconsistencies, and duplicate non-representatives are penalized.

## Roadmap

- CHGNet and M3GNet surrogate evaluators
- richer pymatgen validity checks
- configurable novelty corpora
- optional Materials Project integration
- hull analysis after real DFT data exists
