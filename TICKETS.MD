Ticket Stack — SCA Benchmark Container for Crystal Generation Validation
EPIC A — Benchmark Container Architecture
A1 — Define evaluator plugin interface

Goal: Stop hardcoding evaluator logic into one CrystaLLM-style pipeline.

Implement:

sca/evaluators/base.py
  CrystalEvaluator
  StructureEvaluator
  BatchEvaluator
  RelaxationEvaluator
  ReferenceEvaluator

Each evaluator returns a typed result object with:

evaluator_name
evaluator_version
status: ok | failed | skipped
metrics: dict
artifacts: dict
error_type
error_message
runtime_seconds

Acceptance:

Existing ALIGNN evaluator still works.
Existing crystallm-eval output is unchanged unless new flags are enabled.
New evaluators can be registered without editing the main pipeline.
A2 — Add evaluator registry

Goal: Let the CLI choose validation modules by name.

Example:

sca benchmark manifest candidates.csv \
  --evaluators validity,structure_match,novelty,alignn,chgnet,spp,robocrys_intent

Acceptance:

sca list-evaluators prints installed evaluators.
Missing optional dependencies are reported as skipped, not fatal.
Registry records package availability and import errors.
A3 — Create unified benchmark schema

Goal: Output one wide CSV plus one rich JSONL per structure.

Add:

BenchmarkRecord
EvaluatorResult
BenchmarkSummary

Acceptance:

CSV has stable top-level fields.
JSONL preserves nested evaluator payloads.
Old SCA columns are mapped into the new schema.
A4 — Add optional dependency groups

Goal: Make the repo installable as a container with selectable heavy libraries.

In pyproject.toml:

[project.optional-dependencies]
alignn = [...]
chgnet = [...]
m3gnet = [...]
mace = [...]
sevennet = [...]
robocrys = [...]
mp = [...]
all-mlip = [...]
all = [...]

Acceptance:

Base install stays lightweight.
Heavy evaluator imports are lazy.
CI can run without installing GPU/MLIP dependencies.
EPIC B — Core Pre-DFT Validity Expansion
B1 — Preserve and harden existing CrystaLLM-style evaluator

Goal: Keep current strengths as the baseline evaluator.

Current checks already include parseability, formula consistency, space-group consistency, multiplicity, bond/contact reasonableness, geometry warnings, duplicates, novelty, and optional ALIGNN.

Acceptance:

Existing tests pass.
crystallm-eval remains available.
New benchmark command can call the same checks.
B2 — Add pymatgen structure sanitisation evaluator

Goal: Detect structural weirdness before surrogate models run.

Metrics:

can_parse
can_make_primitive
can_reduce_niggli
can_standardize_spglib
site_count
species_count
has_partial_occupancy
has_disorder
has_invalid_species

Acceptance:

Bad CIFs fail gracefully.
Disordered/partial occupancy structures are labelled, not silently passed.
B3 — Add spglib symmetry robustness sweep

Goal: Make symmetry validation less brittle.

Run space-group detection at multiple tolerances:

symprec = 1e-3, 1e-2, 1e-1
angle_tolerance = 5

Output:

detected_sg_by_tolerance
stable_space_group
space_group_stability_score

Acceptance:

Structures with unstable symmetry get warning labels.
Target SG comparison can use strict or tolerant mode.
B4 — Add local environment / coordination evaluator

Goal: Validate motif-level plausibility, not just distances.

Use pymatgen local environment tools first; later optional matminer.

Metrics:

coordination_numbers_by_site
coordination_environment_summary
polyhedra_count
undercoordinated_sites
overcoordinated_sites

Acceptance:

Per-site coordination summary is included in JSONL.
Aggregate warnings appear in CSV.
EPIC C — Structure Matching, RMSE, Novelty, Rediscovery
C1 — Add StructureMatcher target-match evaluator

Goal: Match generated structures to known target structures, CrystaLLM/CrysText-style.

Inputs:

target_cif_path
reference_id
target_formula

Metrics:

structure_match
rms_dist
max_dist
anonymous_match
supercell_match
matched_reference_id

Acceptance:

Manifest can include target_cif_path.
Evaluator supports exact and anonymous matching modes.
C2 — Add reference corpus nearest-match evaluator

Goal: Generalise novelty beyond first exact match.

Use:

reference_folder
reference_manifest
reference_id_col

Metrics:

nearest_reference_id
nearest_match_type
structure_matcher_fit
rms_dist_if_fit
formula_matched_refs_count
known_match
novel_by_threshold

Acceptance:

Existing novelty loader is reused.
Large reference corpora can be cached/indexed later.
C3 — Add duplicate and uniqueness report by method/query

Goal: Compare mode collapse between generators.

Metrics:

duplicate_rate
unique_valid_count
unique_valid_rate
duplicates_per_query
largest_duplicate_group

Acceptance:

Summary can group by method, query_id, formula, or any column.
Duplicate groups are stable across reruns.
C4 — Add rediscovery vs novelty labels

Goal: Separate “valid but rediscovered” from “valid and novel”.

Labels:

invalid
valid_duplicate
valid_known_match
valid_novel
valid_unknown_reference_missing

Acceptance:

Summary reports each category.
Top-k selection can include or exclude rediscoveries.
EPIC D — Surrogate Stability / MLIP Evaluators

These are the “potentials container” tickets.

D1 — Finish robust ALIGNN adapter

Goal: ALIGNN becomes one evaluator in the registry, not a special path.

Already present as optional formation-energy scorer; README correctly states this is a surrogate pre-DFT prediction, not DFT or energy above hull.

Acceptance:

Supports Python API, subprocess fallback, and injected mock predictor.
Output includes model name/version.
Failure never kills whole benchmark.
D2 — Add CHGNet static energy evaluator

Goal: Predict unrelaxed surrogate formation/stability-like scores.

CHGNet is a pretrained machine-learning interatomic potential for crystal structures, with a public implementation and pretrained models.

Metrics:

chgnet_ok
chgnet_model
chgnet_energy_per_atom
chgnet_forces_max
chgnet_stress_norm

Acceptance:

Works on one CIF and manifest.
Skips cleanly if CHGNet unavailable.
Uses CPU by default unless device flag is set.
D3 — Add CHGNet relaxation evaluator

Goal: Cheap relaxation check before DFT.

Metrics:

chgnet_relax_ok
initial_energy_per_atom
relaxed_energy_per_atom
energy_delta
max_force_final
volume_change_pct
structure_match_initial_relaxed
relaxed_cif_path

Acceptance:

Optional because it is slower.
Writes relaxed CIFs to safe artifact directory.
Has max steps / timeout controls.
D4 — Add M3GNet / MatGL evaluator

Goal: Include second graph-potential family for cross-model agreement.

M3GNet is described as a materials graph network with 3-body interactions and a universal interatomic potential trained on Materials Project relaxations; MatGL provides implementations/pretrained models for M3GNet and related models.

Metrics:

m3gnet_ok
m3gnet_energy_per_atom
m3gnet_relax_ok
m3gnet_relaxed_energy_per_atom
m3gnet_max_force_final

Acceptance:

Static mode first.
Relaxation mode optional.
Same interface as CHGNet.
D5 — Add MACE evaluator

Goal: Add equivariant MLIP/foundation-model route.

MACE provides machine-learning interatomic potentials based on higher-order equivariant message passing, and MACE foundation models are available for materials chemistry.

Metrics:

mace_ok
mace_model
mace_energy_per_atom
mace_forces_max
mace_relax_ok

Acceptance:

ASE calculator wrapper.
Model path/config can be supplied by CLI/env.
Skips if no model file configured.
D6 — Add SevenNet evaluator

Goal: Add another ASE/LAMMPS-capable universal potential route.

SevenNet is a GNN-based interatomic-potential package with ASE calculator support and pretrained model interfaces.

Metrics:

sevennet_ok
sevennet_model
sevennet_energy_per_atom
sevennet_forces_max
sevennet_relax_ok

Acceptance:

Static ASE calculator path implemented.
Relaxation optional.
Clearly marked experimental until calibrated.
D7 — Add MLIP ensemble agreement evaluator

Goal: Do not trust one surrogate blindly.

Input columns from:

ALIGNN
CHGNet
M3GNet
MACE
SevenNet

Metrics:

mlip_energy_mean
mlip_energy_std
mlip_rank_mean
mlip_rank_variance
mlip_disagreement_flag
mlip_consensus_stable_flag

Acceptance:

Works even when only two models are available.
Flags high disagreement.
Used by top-k selection.
EPIC E — SPP Plausibility Evaluator
E1 — Define SPP artifact format for validation

Goal: SCA can score generated CIFs against SPPs, not just QLIP can use SPPs.

Your docs define SPPs as distance-statistics-based plausibility potentials where common species-pair distances receive low penalties and rare/unusual distances receive higher penalties; in the workflow, retrieved neighbours define the query-conditioned SPP prior.

Artifact:

spp.v1.json
  species_pairs
  bin_edges
  penalties
  smoothing
  corpus_hash
  cutoff_policy
  weighting_policy

Acceptance:

Artifact validates against JSON schema.
Includes provenance and corpus summary.
E2 — Add SPP scorer evaluator

Goal: Score any generated CIF against one or more SPPs.

Metrics:

spp_ok
spp_total_score
spp_score_per_atom
spp_score_per_pair
spp_tail_violation_count
spp_missing_pair_count
worst_species_pair

Acceptance:

CLI accepts --spp-artifact.
Missing species-pair tables are reported, not ignored.
Produces per-pair breakdown in JSONL.
E3 — Add SPP calibration evaluator

Goal: Calibrate generated structures against known/reference structures.

Metrics:

spp_percentile_vs_reference
spp_zscore_vs_reference
spp_pass_threshold
spp_calibration_set_size

Acceptance:

Input reference scores from CSV or recomputed reference folder.
Can label generated CIF as typical / borderline / weird.
Saves calibration report.
E4 — Add Anti-SPP / wackiness failure analysis

Goal: Catch structures that exploit SPP scoring.

Checks:

too_short_distance_reward
long_range_padding
missing_pair_artifact
collapsed_cell_warning

Acceptance:

SPP score is not accepted if geometry checks fail.
Report explains when SPP score is invalid or misleading.
EPIC F — Energy Above Hull / Materials Project Reference Integration
F1 — Add Materials Project reference manifest support

Goal: Ground benchmark sets against MP metadata without making MP mandatory.

The design docs already treat MP as the safe default source to track provenance while ICSD needs legal caution.

Manifest fields:

material_id
formula
formation_energy_per_atom
energy_above_hull
band_gap
space_group
cif_path
source
license_notes

Acceptance:

SCA can load MP reference metadata from local CSV/JSON.
No network call required during normal tests.
Provenance fields are preserved.
F2 — Add predicted hull-distance evaluator

Goal: Approximate stability against a local reference hull.

Inputs:

generated formation energy proxy
reference phase diagram entries
chemical system

Metrics:

predicted_energy_above_hull
hull_reference_count
hull_ok
decomposition_products

Acceptance:

Clearly labelled as predicted/surrogate hull, not DFT hull.
Fails gracefully when reference entries are insufficient.
F3 — Add real DFT result ingestion

Goal: Later CASTEP/VASP results can be folded back into SCA.

Input manifest:

cif_path
relaxed_cif_path
dft_energy
dft_energy_per_atom
calculation_status
calculator
functional
cutoff
kpoints

Metrics:

dft_relax_ok
dft_energy_per_atom
dft_volume_change_pct
dft_structure_match_initial_relaxed

Acceptance:

No DFT is run by SCA.
SCA only ingests and reports DFT outputs.
EPIC G — Intent Alignment / RoboCrystallographer Validation
G1 — Add RoboCrystallographer description evaluator

Goal: Convert final CIF into a structure description.

Your validation plan explicitly says to run RoboCrystallographer or similar on the generated final crystal, then compare that description against the original prompt for motifs like perovskite-like oxide, cuboctahedral environments, or structure family.

Metrics/artifacts:

robocrys_ok
robocrys_description
robocrys_key_features
robocrys_error

Acceptance:

Optional dependency.
Text output saved to artifact path.
JSONL stores compact feature summary.
G2 — Add prompt/intention manifest fields

Goal: Benchmark text-to-crystal intent alignment, not just CIF quality.

Manifest columns:

prompt
target_family
target_motif
target_coordination
target_dimensionality
target_space_group
target_formula

Acceptance:

Old manifests still work.
Missing prompt fields skip intent checks cleanly.
G3 — Add rule-based intent matcher

Goal: First-pass deterministic matching before LLM judge.

Checks:

formula mentioned and matched
space group mentioned and matched
family keyword found in description
coordination keyword found
motif keyword found

Metrics:

intent_alignment_score_rule
intent_alignment_failures

Acceptance:

No LLM required.
Transparent failure reasons.
G4 — Add optional LLM-assisted intent judge

Goal: Later compare original prompt vs RoboCrys description more flexibly.

Output:

intent_alignment_score_llm
intent_alignment_label
intent_alignment_rationale

Acceptance:

Disabled by default.
Requires explicit --llm-intent true.
Prompt and response are logged for audit.
EPIC H — Comparator Benchmark Harness
H1 — Define standard generated-candidate manifest

Goal: One format for CrystaLLM, AtomGPT, CrysText, Lang2Str, and LLM-CSP outputs.

Columns:

candidate_id
method
model
query_id
prompt
target_formula
target_space_group
target_cif_path
cif_path
generation_status
raw_output_path

Acceptance:

Existing examples migrate to this format.
Works for folder-only outputs and method-labelled CSVs.
H2 — Add benchmark run config

Goal: Reproducible benchmark presets.

Example:

benchmark_name: text_to_crystal_pre_dft_v1
evaluators:
  - validity
  - composition
  - symmetry
  - structure_match
  - novelty
  - uniqueness
  - alignn
  - chgnet_static
  - spp
  - robocrys_intent
top_k:
  group_by: [method, query_id]
  k: 5

Acceptance:

sca benchmark run config.yaml works.
Config is copied into output folder.
H3 — Add method-comparison summary

Goal: Produce paper-ready aggregate tables.

Metrics by method:

num_generated
parse_valid_rate
composition_match_rate
space_group_match_rate
structure_match_rate
mean_rms_dist
novel_rate
duplicate_rate
mlip_consensus_rate
mean_predicted_energy
mean_spp_score
intent_alignment_rate
top_k_selected_count

Acceptance:

One CSV summary per group.
One Markdown summary for quick inspection.
H4 — Add top-k selection with multi-objective ranking

Goal: Select candidates for DFT/relaxation from many systems.

Ranking terms:

validity gate
formula gate
bad-contact penalty
duplicate penalty
known-match penalty optional
MLIP energy rank
SPP plausibility rank
intent alignment rank
MLIP disagreement penalty

Acceptance:

Ranking config is explicit.
Output explains why each candidate was selected.
EPIC I — Containerisation and Tool Service
I1 — Add Dockerfile for base SCA

Goal: Portable validation container.

Base image includes:

pymatgen
spglib
pandas
typer
rich
pytest

Acceptance:

docker build succeeds.
docker run sca pytest -q succeeds.
Example CIF benchmark runs inside container.
I2 — Add Dockerfile variants for MLIP-heavy installs

Goal: Avoid one impossible monster image.

Images:

sca-base
sca-alignn
sca-chgnet
sca-matgl
sca-mlip-all

Acceptance:

Heavy images are optional.
Each image prints installed evaluator availability.
I3 — Add REST or CLI service mode

Goal: Other crystal-generation systems can call SCA as a validation service.

Endpoints or command wrappers:

POST /evaluate-one
POST /evaluate-manifest
GET /evaluators
GET /health

Acceptance:

Service accepts mounted CIF paths or uploaded CIF text.
Returns BenchmarkRecord JSON.
No arbitrary host path access.
I4 — Add MCP-compatible tool wrapper later

Goal: Let LLM-CSP call SCA as a tool.

Tools:

sca.list_evaluators
sca.evaluate_cif
sca.evaluate_manifest
sca.summarize
sca.select_top_k

Acceptance:

JSON-only inputs/outputs.
Strict schemas.
Safe artifact directory.
EPIC J — Testing and Golden Benchmark Fixtures
J1 — Expand synthetic CIF fixtures

Goal: Test every validation failure mode.

Fixtures:

valid_nacl.cif
bad_parse.cif
wrong_formula.cif
short_contact.cif
huge_volume.cif
duplicate_pair_a.cif
duplicate_pair_b.cif
target_match.cif
target_mismatch.cif
partial_occupancy.cif

Acceptance:

Each evaluator has at least one positive and negative test.
J2 — Add mocked optional evaluator tests

Goal: CI does not need CHGNet/MACE/etc.

Pattern:

mock predictor returns fixed energy
mock predictor raises RuntimeError

Acceptance:

Optional dependency absence is tested.
Failure payloads are stable.
J3 — Add golden benchmark run

Goal: Freeze expected output schema and summary behaviour.

Command:

sca benchmark run tests/fixtures/benchmark_config.yaml

Acceptance:

Produces CSV, JSONL, summary CSV, summary MD.
Tests assert key metrics and columns.
J4 — Add performance smoke tests

Goal: Prevent accidental O(N²) catastrophe for modest batches.

Acceptance:

100 CIF fixture/reference benchmark completes within a configured timeout.
Reference matching cache is used where possible.
EPIC K — Documentation
K1 — Write docs/EVALUATORS.md

Each evaluator documents:

what it measures
what it does not measure
required dependency
CLI flags
output fields
failure modes

Acceptance:

ALIGNN caveat repeated: surrogate, not DFT.
MLIP caveat repeated: model-dependent proxy.
K2 — Write docs/BENCHMARK_PROTOCOL_TEXT_TO_CRYSTAL.md

Goal: Make the validation protocol explicit.

Sections:

1. Input manifest format
2. Required targets
3. Validity metrics
4. Structure match metrics
5. Novelty/uniqueness metrics
6. Surrogate stability metrics
7. SPP plausibility metrics
8. Intent alignment metrics
9. Top-k DFT selection
10. Reporting

Acceptance:

Directly maps to CrystaLLM/AtomGPT/CrysText/Lang2Str comparison plan.
Explains what is pre-DFT vs post-DFT.
K3 — Write docs/CONTAINER_USAGE.md

Goal: Make it easy to call from other repos.

Examples:

docker run -v ./cifs:/data/cifs sca-base \
  sca benchmark folder /data/cifs --out /data/reports

Acceptance:

Includes folder, manifest, one-CIF, and service mode examples.
Implementation Order

Do it in this order:

1. EPIC A — evaluator registry/schema
2. EPIC B — harden existing validity pipeline
3. EPIC C — target matching + novelty/rediscovery
4. EPIC H — benchmark manifest + summaries
5. EPIC D1-D4 — ALIGNN, CHGNet, M3GNet first
6. EPIC E — SPP scorer/calibration
7. EPIC G — RoboCrys intent alignment
8. EPIC F — MP/hull/DFT ingestion
9. EPIC I — Docker/service/MCP wrapper
10. EPIC J/K — full fixture/docs hardening throughout
Minimum “good enough” v1

For the first serious benchmark against other generators, I would define v1 as:

validity
composition match
space-group consistency
StructureMatcher target match + RMSE
uniqueness / duplicate grouping
novelty against reference corpus
ALIGNN energy
CHGNet static energy
M3GNet static energy
SPP score against query-conditioned SPP
top-k selector
method comparison summary
Docker base container

Then v1.5 adds:

CHGNet/M3GNet relaxation
RoboCrystallographer intent alignment
predicted hull distance
MACE / SevenNet adapters
REST/MCP service mode

This keeps the repo scientifically honest: SCA v1 is pre-DFT benchmarking and triage, not a claim of final physical validation. That matches your current framing: the generated structures still need later relaxation/DFT/experimental validation, while SCA tells you which candidates are valid, plausible, non-duplicate, non-obvious rediscoveries, and worth sending forward.