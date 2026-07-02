Yes — we should split this into a **secondary benchmark stack** with two modes:

```text
Mode 1: Direct CIF benchmark
“Here is a directory/manifest of generated CIFs. Score them against literature-style metrics.”

Mode 2: End-to-end text-to-crystal benchmark
“Here are text prompts / system inputs. Run the full workflow, generate crystals, then score the outputs.”
```

Below is the ticket stack.

---

# Secondary Benchmark Stack: Literature-Replication Benchmarks

## EPIC 1 — Benchmark protocol registry

**Goal:** encode the paper comparator table as explicit benchmark protocols, not just loose docs.

### Ticket 1.1 — Add benchmark protocol schema

Create:

```text
sca/benchmark_protocols/
  schema.py
  registry.py
  literature_values.py
```

Each protocol should define:

```text
protocol_id
paper_name
benchmark_family
metric_name
comparator_value
direction
unit
dataset_scope
attempts
required_inputs
required_evaluators
notes
```

Example protocol rows:

```text
validity_gruver_90
chemeleon_validity_98_99
crystext_mp20_n1_match_rate
crystext_mp20_n20_match_rate
lang2str_mp20_match_rate
lang2str_mp20_rmse
lang2str_relaxed_rmse
crystal_text_llm_metastable_49
chemeleon_lip_s_cl_80_percent_metastable
atomgpt_formation_energy_mae
alignn_formation_energy_mae
```

### Ticket 1.2 — Add protocol listing CLI

```bat
python -m sca.cli list-benchmark-protocols
```

Should print:

```text
protocol_id
paper
metric
value_to_beat
required inputs
whether SCA can currently compute it
```

---

# MODE 1 — Direct CIF Benchmarks

## EPIC 2 — Direct CIF benchmark runner

**Goal:** support the workflow:

> “Given this directory of good/bad/generated CIFs, tell me how good they are under all paper-comparable metrics.”

### Ticket 2.1 — Add `benchmark-cif-set` CLI

Add:

```bat
python -m sca.cli benchmark-cif-set ^
  --cif-folder path\to\cifs ^
  --manifest optional_manifest.csv ^
  --protocols all ^
  --out reports\cif_set_results.csv ^
  --summary reports\cif_set_summary.csv ^
  --markdown reports\cif_set_report.md
```

It should support:

```text
folder-only mode
manifest mode
reference CIF mode
hull-reference mode
relaxed/unrelaxed comparison mode
```

### Ticket 2.2 — CIF-set manifest schema

Manifest columns:

```csv
cif_path,
sample_id,
benchmark_id,
target_formula,
target_space_group,
target_structure_family,
reference_cif_path,
reference_id,
attempt_id,
method,
property_name,
target_property_value,
target_property_unit,
target_energy_above_hull,
target_formation_energy_per_atom,
dataset_scope,
paper_protocol,
notes
```

### Ticket 2.3 — Direct validity replication

Replicate these comparator families:

```text
Physical validity ~90%
Chemeleon validity 98–99%
Minimum distance >0.5 Å
Composition satisfaction 95%
Space-group satisfaction 74%
Composition + SG satisfaction 74%
```

Metrics:

```text
parse_validity_rate
pre_dft_validity_rate
min_distance_pass_rate
composition_match_rate
space_group_match_rate
composition_and_sg_match_rate
```

Required evaluators:

```text
pre_dft_validity
symmetry / space-group consistency
composition check
```

### Ticket 2.4 — Direct structure reproduction replication

Replicate:

```text
CrysText MP-20 N=1 match rate = 57%
CrysText MP-20 N=20 match rate = 73%
CrysText MP-20 RMSE N=20 = 0.0243
Lang2Str MP-20 MR = 63.92%
Lang2Str MP-20 RMSE = 0.076
Lang2Str relaxed RMSE = 0.055
MPTS-52 MR = 28.36%
MPTS-52 RMSE = 0.1424
```

Metrics:

```text
match_rate_n1
match_rate_nk
structure_match_rate
rms_dist
median_rms_dist
best_rms_dist
relaxed_rms_dist
rmse_improvement
```

Required inputs:

```text
reference_cif_path
attempt_id
benchmark_id
optional relaxed_cif_path
```

Required evaluator:

```text
structure_match
```

### Ticket 2.5 — Direct MLIP/metastability replication

Replicate:

```text
CDVAE metastable rate = 28%
LLaMA-2 70B metastable rate = 49%
Chemeleon metastable threshold <0.15 eV/atom
Chemeleon Li-P-S-Cl within threshold ~80%
```

Metrics:

```text
predicted_ehull_rate_0_00
predicted_ehull_rate_0_05
predicted_ehull_rate_0_10
predicted_ehull_rate_0_15
mlip_consensus_stable_rate
mlip_disagreement_rate
```

Required inputs:

```text
predicted_energy_above_hull
or local hull_reference CSV
or MLIP energy + local reference hull
```

Required evaluators:

```text
chgnet_static
m3gnet_static
mace_static
sevennet_static
mlip_ensemble
predicted_hull
```

### Ticket 2.6 — Direct relaxation replication

Replicate:

```text
Lang2Str relaxation improvement: RMSE 0.076 -> 0.055
Chemeleon TiO2 MACE-MP convergence: 539/549 = 98.2%
```

Metrics:

```text
relax_success_rate
median_energy_drop
median_max_force_before
median_max_force_after
force_threshold_success_rate_0_20
force_threshold_success_rate_0_10
rms_before
rms_after
rms_improvement_rate
collapse_rate
```

Required evaluator:

```text
chgnet_relax
```

Potential extension:

```text
mace_relax
m3gnet_relax
sevennet_relax
```

### Ticket 2.7 — Direct property MAE replication

Replicate:

```text
AtomGPT formation-energy MAE = 0.072 eV/atom
ALIGNN formation-energy MAE = 0.033 eV/atom
```

Metrics:

```text
formation_energy_mae
band_gap_mae
target_property_mae
property_hit_rate_within_tolerance
```

Required inputs:

```text
target_formation_energy_per_atom
predicted formation energy from MLIP or property predictor
```

Required evaluator:

```text
property_targets
```

---

# MODE 2 — End-to-End Text-to-Crystal Benchmarks

## EPIC 3 — E2E prompt benchmark schema

**Goal:** support the workflow:

> “Here is a text input/prompt. Run our system. Generate crystals. Analyse them using SCA. Compare to paper values.”

### Ticket 3.1 — Add E2E benchmark prompt manifest

Create:

```text
benchmarks/e2e_text_prompts/
  e2e_prompts_v1.csv
```

Columns:

```csv
prompt_id,
paper_source,
benchmark_family,
input_text,
target_formula,
target_structure_family,
target_space_group,
target_crystal_system,
reference_cif_path,
reference_id,
num_attempts,
expected_metrics,
required_tools,
notes
```

Example rows:

```text
Generate a cubic perovskite BaTiO3 structure.
Generate a spinel-like ZnFe2O4 structure.
Generate a rocksalt NiO crystal.
Generate rutile TiO2.
Generate an argyrodite-like Li6PS5Cl solid electrolyte.
Generate a pyrite-like FeS2 crystal.
Generate a fluorite-like CeO2 structure.
Generate a wurtzite ZnO structure.
Generate NdAgHg2 in space group 225.
```

### Ticket 3.2 — Add E2E runner CLI wrapper

Add:

```bat
python -m sca.cli run-e2e-text-benchmark ^
  --prompts benchmarks\e2e_text_prompts\e2e_prompts_v1.csv ^
  --system-command "python -m llm_csp.generate --prompt-file {prompt_file} --out-dir {out_dir}" ^
  --out-dir reports\e2e_runs ^
  --num-attempts 20 ^
  --benchmark-out reports\e2e_benchmark_results.csv ^
  --summary reports\e2e_benchmark_summary.csv ^
  --markdown reports\e2e_benchmark_report.md
```

This should be system-agnostic. It does **not** need to know your generator internals; it should call a configurable command.

The runner should:

```text
1. read prompt manifest
2. call generator for each prompt
3. collect generated CIFs
4. build SCA manifest
5. run SCA evaluators
6. run paper-benchmark-summary
7. write per-prompt report
```

### Ticket 3.3 — Add attempt handling for N=1 / N=20

For CrysText/CrystaLLM-style replication, we need:

```text
N=1 match rate
N=20 match rate
best-of-20 RMSD
best-of-20 MLIP score
best-of-20 relaxed RMSD
```

Implement:

```text
attempt_id
attempt_rank
prompt_id
benchmark_id
```

Selection policies:

```text
first_attempt
best_structure_match
best_mlip_consensus
best_relaxed_score
best_paper_rank_score
```

### Ticket 3.4 — E2E text intent satisfaction

This is where our system can show uniqueness later.

Metrics:

```text
composition_satisfaction
space_group_satisfaction
prototype_satisfaction
text_intent_alignment
retrieval_trace_present
solver_trace_present
verification_trace_present
```

For now:

```text
composition_satisfaction = formula match
space_group_satisfaction = detected or declared SG match
prototype_satisfaction = prototype_match
```

Later:

```text
RoboCrystallographer description alignment
LLM judge over prompt vs generated structure description
retrieval evidence alignment
```

### Ticket 3.5 — E2E report

Markdown sections:

```text
# E2E Text-to-Crystal Benchmark Report

## Prompt set
## Generation success
## Validity
## Composition / SG satisfaction
## Structure reproduction
## MLIP stability
## Relaxation
## Novelty / uniqueness
## Comparator pass/fail
## Per-prompt failures
## Traceability audit
```

---

# EPIC 4 — Dataset-specific replicas

## Ticket 4.1 — MP-20-style direct benchmark

Purpose:

```text
Replicate CrysText / Lang2Str structure match style.
```

Inputs needed:

```text
MP-20 target CIF subset
generated CIFs for each MP-20 composition
reference_cif_path per target
attempt_id up to 20
```

Outputs:

```text
N=1 match rate
N=20 match rate
RMSE / RMSD
composition satisfaction
space-group satisfaction if prompts include SG
```

Comparator values:

```text
CrysText N=1 MR 57%
CrysText N=20 MR 73%
CrysText RMSE N=20 0.0243
Lang2Str MP-20 MR 63.92%
Lang2Str MP-20 RMSE 0.076
Lang2Str relaxed RMSE 0.055
```

## Ticket 4.2 — MPTS-52-style direct benchmark

Purpose:

```text
Harder large-cell reproduction benchmark.
```

Comparator values:

```text
Lang2Str MPTS-52 MR 28.36%
Lang2Str MPTS-52 RMSE 0.1424
Uni-3DAR MPTS-52 MR 32.44%
Uni-3DAR MPTS-52 RMSE 0.0684
```

Inputs:

```text
MPTS-52 subset
generated CIFs
reference CIFs
attempts
```

## Ticket 4.3 — Chemeleon chemical-space benchmark

Purpose:

```text
Replicate text-guided chemical-space/stability style.
```

Subsets:

```text
Ti-O
Zn-Ti-O
Li-P-S-Cl
```

Metrics:

```text
validity rate
composition allowed by SMACT-like filter
MLIP relaxation/convergence rate
predicted E_hull <= 0.15 eV/atom
stable count
metastable count
unique structure count
new space-group count
```

Comparator values:

```text
validity 98–99%
TiO2 MACE-MP convergence 539/549 = 98.2%
TiO2 DFT-metastable structures 122
Li-P-S-Cl stable count 17
Li-P-S-Cl metastable count 435
Li-P-S-Cl within 0.15 eV/atom ~80%
```

Needed additions:

```text
chemical-system manifest builder
SMACT-like composition filter
local hull builder/importer
stable/metastable counter
```

## Ticket 4.4 — Crystal-text LLM metastability benchmark

Purpose:

```text
Replicate stable/metastable text-generation claim.
```

Metrics:

```text
physical validity rate
predicted_metastable_rate
DFT/MLIP metastable rate
```

Comparator values:

```text
physical validity ~90%
CDVAE metastable 28%
LLaMA-2 70B metastable 49%
```

## Ticket 4.5 — AtomGPT property MAE benchmark

Purpose:

```text
Replicate property prediction / inverse-design property targeting.
```

Metrics:

```text
formation_energy_mae
band_gap_mae
target_property_mae
property_hit_rate
```

Comparator values:

```text
AtomGPT formation-energy MAE 0.072 eV/atom
ALIGNN baseline 0.033 eV/atom
CGCNN 0.063 eV/atom
CFID 0.142 eV/atom
```

---

# EPIC 5 — Report generator for “values to beat”

## Ticket 5.1 — Comparator pass/fail matrix

Create one output table:

```csv
benchmark_family,
metric,
our_value,
paper_value,
paper_name,
beats_paper,
delta,
dataset_scope,
protocol_match_level,
notes
```

Where `protocol_match_level` is:

```text
exact_protocol
subset_protocol
approximate_protocol
contextual_only
not_comparable
```

This is crucial. We do not want to accidentally claim:

```text
we beat MP-20
```

when we only ran:

```text
22 paper-derived prototype targets
```

## Ticket 5.2 — Paper-style leaderboard report

Generate:

```text
reports/literature_replication_report.md
```

Sections:

```text
## Exact protocol replications
## Subset replications
## Contextual comparator checks
## Metrics not yet computable
## Direct CIF benchmark results
## E2E text-to-crystal benchmark results
## What we beat
## What we do not beat yet
## Caveats
```

---

# EPIC 6 — Required data assets

## Ticket 6.1 — Reference CIF bundles

Needed for:

```text
Structure reproduction
RMSE/RMSD
N=1/N=20 match rate
```

Bundles:

```text
paper_targets_22_reference_cifs
mp20_subset_reference_cifs
mpts52_subset_reference_cifs
chemeleon_chemical_space_reference_cifs
```

## Ticket 6.2 — Local hull reference bundles

Needed for:

```text
predicted_energy_above_hull
stable/metastable count
```

Bundles:

```text
Ti-O hull
Zn-Ti-O hull
Li-P-S-Cl hull
prototype_22 hulls
MP-20 subset hulls
```

## Ticket 6.3 — Property target bundles

Needed for AtomGPT-style metrics:

```text
formation_energy_per_atom target
band_gap target
Tc target if superconductivity benchmark is used
```

---

# Recommended build order

Do it in this order.

## Phase 1 — Direct CIF replication

This is easiest because SCA already exists.

```text
1. protocol registry
2. benchmark-cif-set CLI
3. comparator pass/fail matrix
4. direct validity / match / MLIP / relaxation / property summaries
```

Deliverable:

```text
Given any CIF folder, produce a literature-comparator report.
```

## Phase 2 — E2E prompt replication

```text
1. e2e prompt manifest
2. generator command wrapper
3. attempt handling N=1/N=20
4. full SCA analysis
5. prompt-level report
```

Deliverable:

```text
Given text prompts, run our full workflow and score generated crystals.
```

## Phase 3 — Dataset-specific replicas

```text
1. MP-20 subset
2. MPTS-52 subset
3. Chemeleon chemical spaces
4. AtomGPT property targets
```

Deliverable:

```text
Subset or exact replicas of paper protocols.
```

---

# One mega Codex goal for Phase 1

Use this first:

```text
/goal Build Phase 1 of literature-replication benchmarks: direct CIF comparator reports.

Context:
SCA already supports paper-target A-E metrics and has a 22-target paper challenge smoke benchmark.
Now we need a secondary benchmark stack that replicates literature comparator metrics for arbitrary direct CIF inputs.

Main objective:
Given a folder or manifest of CIFs, produce a literature-comparator report against known paper values:
- validity ~90%, 98–99%
- min distance >0.5 Å
- composition satisfaction 95%
- space-group satisfaction 74%
- MP-20/CrysText/Lang2Str match-rate and RMSE values where references exist
- metastable-rate values 28%, 49%, ~80% where hull values exist
- relaxation metrics vs Lang2Str and Chemeleon
- formation-energy MAE vs AtomGPT / ALIGNN where property targets exist

Tasks:
1. Add benchmark protocol registry.
2. Add `list-benchmark-protocols`.
3. Add `benchmark-cif-set`.
4. Add direct CIF manifest schema.
5. Add comparator pass/fail matrix.
6. Add direct CIF Markdown report.
7. Mark each comparator as exact_protocol, subset_protocol, approximate_protocol, contextual_only, or not_comparable.
8. Ensure missing references/hulls/properties produce not-computable rows, not crashes.
9. Add tests with synthetic CSVs.
10. Update docs with Windows commands.

Required CLI:

python -m sca.cli benchmark-cif-set ^
  --cif-folder "C:\Users\brown\Downloads\example created cifs" ^
  --protocols all ^
  --out reports\direct_cif_results.csv ^
  --summary reports\direct_cif_summary.csv ^
  --json reports\direct_cif_summary.json ^
  --markdown reports\direct_cif_report.md

Also support manifest mode:

python -m sca.cli benchmark-cif-set ^
  --manifest benchmarks\paper_targets\generated_manifest.csv ^
  --protocols all ^
  --out reports\direct_cif_results.csv ^
  --summary reports\direct_cif_summary.csv ^
  --json reports\direct_cif_summary.json ^
  --markdown reports\direct_cif_report.md

Definition of done:
- direct CIF benchmark works on folder and manifest inputs
- comparator matrix is generated
- unsupported metrics are marked not-computable
- tests pass
- ruff passes
```

---

# One mega Codex goal for Phase 2

Then use this:

```text
/goal Build Phase 2 of literature-replication benchmarks: end-to-end text-to-crystal prompt runner.

Context:
Phase 1 scores existing CIF folders/manifests.
Now we need an E2E benchmark runner that starts from text prompts, invokes the actual LLM-CSP generation system, collects CIFs, and runs SCA analysis.

Main objective:
Given a prompt manifest, run the system end-to-end:
text prompt -> generation command -> generated CIFs -> SCA manifest -> benchmark-cif-set -> report.

Tasks:
1. Add E2E prompt manifest schema.
2. Add `run-e2e-text-benchmark` CLI.
3. Support configurable generator command template.
4. Support N attempts per prompt: N=1, N=20.
5. Track attempt_id and prompt_id.
6. Build generated CIF manifest automatically.
7. Run direct CIF comparator benchmark automatically.
8. Report composition satisfaction, SG satisfaction, prototype satisfaction, match rate, RMSE, MLIP stability, relaxation, novelty.
9. Include traceability fields:
   - prompt
   - generation config
   - retrieved evidence path if provided
   - solver config path if provided
   - generated CIF path
10. Add docs and tests with a fake generator command.

Required CLI:

python -m sca.cli run-e2e-text-benchmark ^
  --prompts benchmarks\e2e_text_prompts\e2e_prompts_v1.csv ^
  --generator-command "python -m llm_csp.generate --prompt {prompt} --out-dir {out_dir} --attempts {num_attempts}" ^
  --out-dir reports\e2e_runs ^
  --num-attempts 20 ^
  --protocols all ^
  --summary reports\e2e_benchmark_summary.csv ^
  --markdown reports\e2e_benchmark_report.md

Definition of done:
- fake generator test passes
- prompt manifest is created
- generated CIFs are collected
- N=1/N=20 metrics are supported
- comparator report is generated
- failures are structured and auditable
```

This gives us the clean split:

```text
Direct CIF benchmark = compare outputs.
E2E text benchmark = compare the full system.
```
