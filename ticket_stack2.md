# ticket_stack2.md — Unique Verifiable CSP Benchmarks

## Purpose

This ticket stack defines the second benchmark family for SCA / LLM-CSP.

The first literature-replication benchmark stack compares our generated CIFs against existing crystal-generation papers using metrics such as validity, structure match rate, RMSE, energy-above-hull, relaxation success, and property MAE.

This second benchmark stack measures what is unique about our system:

> The system does not only output a CIF. It converts a natural-language crystal-design request into an auditable, retrieval-guided, constraint-grounded, solver-backed CSP run.

The unique benchmark family therefore evaluates:

* retrieval traceability
* evidence faithfulness
* constraint faithfulness
* solver feasibility/certification
* audit-bundle completeness
* repairability
* retrieval ablation
* end-to-end intent preservation

This benchmark should reward transparent, inspectable, reproducible text-to-crystal workflows rather than only final CIF plausibility.

---

# EPIC 1 — Traceable Run Artifact Schema

## Goal

Define a standard artifact bundle for every LLM-CSP run.

A successful run should not only output a CIF. It should output a full audit trail:

```text
prompt
structured intent
retrieval query
retrieved evidence
retrieval scores
evidence summary
derived constraints
SPP/pair statistics
solver configuration
solver status
generated CIFs
validation report
relaxation report
diagnostics report
final decision
```

## Ticket 1.1 — Add run artifact schema

Create:

```text
sca/traceability/
  __init__.py
  schema.py
  io.py
```

Define schemas for:

```text
TraceableRunBundle
StructuredIntent
RetrievalTrace
EvidenceItem
ConstraintTrace
SPPTrace
SolverTrace
GeneratedCandidateTrace
ValidationTrace
RelaxationTrace
DiagnosticsTrace
FinalDecisionTrace
```

Each schema should support:

```text
run_id
prompt_id
input_text
timestamp
file paths
checksums where useful
status
errors
notes
```

## Ticket 1.2 — Add bundle loader/validator

Add utilities to load a run directory and validate that expected files exist.

Inputs:

```text
run_dir
optional manifest row
```

Outputs:

```text
bundle_valid
missing_artifacts
parse_errors
crosslink_errors
```

## Ticket 1.3 — Add artifact bundle report

Add CLI:

```bat
python -m sca.cli inspect-run-bundle ^
  --run-dir reports\e2e_runs\example_run ^
  --out reports\run_bundle_inspection.csv ^
  --json reports\run_bundle_inspection.json ^
  --markdown reports\run_bundle_inspection.md
```

---

# EPIC 2 — Evidence Traceability Benchmark

## Goal

Measure whether the generated structure can be traced back to retrieved evidence.

This benchmark asks:

> Can the system justify where the generated structure came from?

## Ticket 2.1 — Evidence traceability evaluator

Add evaluator:

```text
evidence_traceability
```

Inputs:

```text
generated CIF
run bundle
retrieval trace
retrieved CIFs / metadata
constraint trace
SPP trace
```

Output columns:

```csv
evidence_trace_present,
num_retrieved_structures,
num_retrieved_parseable,
fraction_retrieved_parseable,
fraction_retrieved_formula_relevant,
fraction_retrieved_family_relevant,
fraction_retrieved_space_group_relevant,
evidence_to_constraint_links_present,
num_constraints_linked_to_evidence,
constraint_evidence_link_rate,
spp_pair_coverage_rate,
unsupported_constraint_count,
evidence_trace_score,
evidence_trace_error
```

## Ticket 2.2 — Retrieved evidence relevance checks

Implement relevance checks:

```text
formula relevance
chemical-system relevance
prototype/family relevance
space-group relevance
element-overlap relevance
```

These should be heuristic and transparent.

## Ticket 2.3 — Evidence-to-constraint linking

Given constraints such as:

```text
minimum Fe-O distance
target space group
prototype family
SPP pair potential Fe-O
```

check whether each can be linked to retrieved evidence.

Output:

```text
linked
unlinked
unsupported
uncertain
```

## Ticket 2.4 — Evidence traceability score

Define:

```text
evidence_trace_score =
  0.25 * retrieval_trace_present
+ 0.20 * fraction_retrieved_parseable
+ 0.20 * fraction_retrieved_family_relevant
+ 0.20 * constraint_evidence_link_rate
+ 0.15 * spp_pair_coverage_rate
```

Document this as a workflow-audit score, not a physical-validity score.

---

# EPIC 3 — Constraint Faithfulness Benchmark

## Goal

Measure whether the output obeys the constraints that were explicitly parsed from the natural-language prompt.

This benchmark asks:

> Did the system preserve the scientific intent of the prompt?

## Ticket 3.1 — Constraint faithfulness evaluator

Add evaluator:

```text
constraint_faithfulness
```

Inputs:

```text
generated CIF
structured intent
constraint trace
optional reference CIF
optional prototype family
```

Output columns:

```csv
constraint_trace_present,
num_prompt_constraints,
num_solver_constraints,
num_posthoc_checked_constraints,
formula_constraint_satisfied,
space_group_constraint_satisfied,
crystal_system_constraint_satisfied,
prototype_constraint_satisfied,
site_role_constraint_satisfied,
coordination_constraint_satisfied,
minimum_distance_constraint_satisfied,
forbidden_contact_violation_count,
constraint_satisfaction_rate,
constraint_violation_count,
constraint_violation_summary,
constraint_faithfulness_score,
constraint_faithfulness_error
```

## Ticket 3.2 — Natural-language constraint categories

Support these constraint types:

```text
formula
chemical system
space group
crystal system
prototype family
site role
coordination motif
minimum distance
forbidden contact
target property
```

## Ticket 3.3 — Constraint violation report

For each failed constraint, report:

```text
constraint_id
constraint_type
expected_value
observed_value
severity
source_text
solver_enforced
posthoc_checked
failure_reason
```

## Ticket 3.4 — Prompt constraint satisfaction metric

Compute:

```text
constraint_satisfaction_rate =
  satisfied_constraints / checked_constraints
```

Also compute a weighted score where hard constraints count more than soft preferences.

---

# EPIC 4 — Solver Certificate / Feasibility Benchmark

## Goal

Measure whether the system provides a solver-backed certificate for the generated candidate or for an infeasible request.

This benchmark asks:

> Did the system actually solve a constrained CSP problem, and can it report the status?

## Ticket 4.1 — Solver certificate evaluator

Add evaluator:

```text
solver_certificate
```

Inputs:

```text
solver trace
solver logs
generated CIF
constraint trace
```

Output columns:

```csv
solver_trace_present,
solver_backend,
solver_status,
solver_status_valid,
solver_optimal,
solver_feasible,
solver_infeasible,
objective_value_present,
objective_value,
variable_count_present,
constraint_count_present,
num_variables,
num_constraints,
solve_time_seconds,
infeasible_case_detected,
infeasibility_explanation_present,
solver_certificate_score,
solver_certificate_error
```

## Ticket 4.2 — Infeasible prompt test set

Create:

```text
benchmarks/unique_verifiable_csp/infeasible_prompts.csv
```

Example prompts:

```csv
prompt_id,input_text,expected_status,expected_failure_type
impossible_rocksalt_ab3,Generate a rocksalt AB3 crystal in a two-site primitive rocksalt cell.,infeasible,composition_site_mismatch
too_short_batio3,Generate cubic BaTiO3 but force all Ba-O distances below 1.0 Å.,infeasible,distance_constraint_conflict
bad_charge_balance,Generate a charge-balanced NaCl2 rocksalt structure.,infeasible_or_invalid,charge_or_composition_conflict
```

## Ticket 4.3 — Infeasibility detection metrics

Compute:

```text
infeasible_case_detection_rate
invalid_prompt_refusal_rate
repair_suggestion_rate
false_feasible_rate
```

---

# EPIC 5 — Retrieval Ablation Benchmark

## Goal

Measure whether retrieval actually improves generation.

This benchmark asks:

> Does retrieved structural evidence improve validity, prototype match, stability, and relaxation robustness?

## Ticket 5.1 — Retrieval ablation manifest

Create:

```text
benchmarks/unique_verifiable_csp/retrieval_ablation_prompts.csv
```

Columns:

```csv
prompt_id,
input_text,
target_formula,
target_structure_family,
target_space_group,
reference_cif_path,
num_attempts,
notes
```

## Ticket 5.2 — Ablation runner

Add CLI:

```bat
python -m sca.cli run-retrieval-ablation-benchmark ^
  --prompts benchmarks\unique_verifiable_csp\retrieval_ablation_prompts.csv ^
  --generator-command "python -m llm_csp.generate --prompt {prompt} --out-dir {out_dir} --retrieval-mode {retrieval_mode} --attempts {num_attempts}" ^
  --retrieval-modes none,metadata,evidence_spp ^
  --out-dir reports\retrieval_ablation ^
  --summary reports\retrieval_ablation_summary.csv ^
  --json reports\retrieval_ablation_summary.json ^
  --markdown reports\retrieval_ablation_report.md
```

## Ticket 5.3 — Ablation metrics

For each retrieval mode, compute:

```text
parse_validity_rate
pre_dft_validity_rate
composition_match_rate
space_group_match_rate
prototype_match_rate
structure_match_rate
median_rms_dist
mlip_consensus_stable_rate
bad_contact_rate
relax_success_rate
collapse_rate
constraint_satisfaction_rate
evidence_trace_score
```

## Ticket 5.4 — Retrieval uplift score

Compute deltas:

```text
metadata_vs_none_delta
evidence_spp_vs_none_delta
evidence_spp_vs_metadata_delta
```

For:

```text
validity
prototype match
structure match
MLIP stability
relaxation success
constraint satisfaction
```

---

# EPIC 6 — Repairability / Failure Recovery Benchmark

## Goal

Measure whether the system can diagnose and repair failed generated structures.

This benchmark asks:

> When generation fails, can the system detect the failure, classify it, modify constraints, rerun, and improve the candidate?

## Ticket 6.1 — Repair benchmark manifest

Create:

```text
benchmarks/unique_verifiable_csp/repair_cases.csv
```

Columns:

```csv
case_id,
input_cif_path,
input_prompt,
target_formula,
target_structure_family,
reference_cif_path,
known_failure_type,
expected_repair_action,
notes
```

Example failure cases:

```text
ZnFe2O4 spinel with bad Zn-Fe contact
CeO2 fluorite with Ce-O at 1.15 Å
LiMn2O4 spinel with Li-O collision
wrong-space-group BaTiO3
composition-correct but prototype-wrong NiS2
```

## Ticket 6.2 — Repair benchmark runner

Add CLI:

```bat
python -m sca.cli run-repairability-benchmark ^
  --cases benchmarks\unique_verifiable_csp\repair_cases.csv ^
  --repair-command "python -m llm_csp.repair --input-cif {input_cif} --prompt {prompt} --out-dir {out_dir}" ^
  --out-dir reports\repairability ^
  --summary reports\repairability_summary.csv ^
  --json reports\repairability_summary.json ^
  --markdown reports\repairability_report.md
```

## Ticket 6.3 — Repairability metrics

Compute:

```text
failure_detected_rate
failure_classification_accuracy
repair_attempt_success_rate
validity_improvement_rate
structure_match_improvement_rate
rms_improvement_rate
bad_contact_reduction_rate
relaxation_success_improvement_rate
constraint_satisfaction_improvement_rate
audit_log_complete_rate
```

## Ticket 6.4 — Before/after repair report

For each case, output:

```csv
case_id,
known_failure_type,
detected_failure_type,
failure_detected,
classification_correct,
before_pre_dft_valid,
after_pre_dft_valid,
before_structure_match,
after_structure_match,
before_rms_dist,
after_rms_dist,
before_bad_contact_count,
after_bad_contact_count,
repair_success,
repair_notes
```

---

# EPIC 7 — Evidence Faithfulness / Anti-Hallucination Benchmark

## Goal

Measure whether the system’s claims are supported by retrieved evidence.

This benchmark asks:

> Does the system only claim evidence it actually retrieved and used?

## Ticket 7.1 — Evidence faithfulness evaluator

Add evaluator:

```text
evidence_faithfulness
```

Inputs:

```text
run bundle
retrieval trace
final explanation
constraint trace
```

Output columns:

```csv
final_explanation_present,
num_evidence_claims,
num_supported_evidence_claims,
num_unsupported_evidence_claims,
unsupported_evidence_claim_rate,
wrong_family_evidence_rate,
retrieval_citation_completeness,
evidence_constraint_consistency,
evidence_faithfulness_score,
evidence_faithfulness_error
```

## Ticket 7.2 — Trap prompt set

Create:

```text
benchmarks/unique_verifiable_csp/evidence_trap_prompts.csv
```

Example prompts:

```text
Generate a spinel oxide using retrieved spinel evidence only.
Generate BaTiO3 and cite which known structures informed the constraints.
Generate a Li-P-S-Cl conductor, but do not use oxide examples.
Generate an unknown XyZ3 perovskite and do not invent supporting evidence.
```

## Ticket 7.3 — Claim extraction

Implement lightweight claim extraction from final run explanations.

Claims can initially be extracted using simple rules:

```text
"used"
"based on"
"retrieved"
"similar to"
"evidence from"
"constraint derived from"
```

Do not require an LLM judge for tests.

---

# EPIC 8 — Intent-to-Artifact Completeness Benchmark

## Goal

Measure whether the system produces a complete, reproducible research artifact.

This benchmark asks:

> Does the run produce every artifact needed for scientific inspection and reproduction?

## Ticket 8.1 — Audit bundle completeness evaluator

Add evaluator:

```text
audit_bundle_completeness
```

Output columns:

```csv
prompt_present,
structured_intent_present,
retrieval_trace_present,
retrieved_evidence_present,
constraint_trace_present,
spp_trace_present,
solver_trace_present,
generated_cif_present,
validation_report_present,
relaxation_report_present,
diagnostics_report_present,
final_decision_present,
artifact_bundle_complete,
artifact_bundle_complete_rate,
artifact_crosslink_validity_rate,
missing_artifact_count,
missing_artifacts,
audit_bundle_score,
audit_bundle_error
```

## Ticket 8.2 — Reproducibility check

Check whether the bundle contains enough information to rerun:

```text
environment info
generator config
retrieval config
solver config
random seed
input prompt
output paths
```

Output:

```text
reproducibility_metadata_present
missing_reproducibility_fields
```

---

# EPIC 9 — Unique Composite Benchmark Score

## Goal

Create one score that summarizes the unique verifiable-CSP capability.

This benchmark should not replace physical metrics. It should sit beside them.

## Ticket 9.1 — Composite score

Add metric:

```text
traceable_constraint_grounded_csp_score
```

Formula:

```text
score =
  0.20 * output_validity
+ 0.20 * constraint_faithfulness_score
+ 0.15 * structure_or_prototype_match_score
+ 0.15 * mlip_or_relaxation_robustness_score
+ 0.15 * evidence_trace_score
+ 0.10 * audit_bundle_score
+ 0.05 * solver_certificate_score
```

Each component should be reported separately.

## Ticket 9.2 — Composite benchmark report

Add CLI:

```bat
python -m sca.cli unique-csp-benchmark-summary ^
  --results reports\e2e_benchmark_results.csv ^
  --bundles reports\e2e_runs ^
  --out reports\unique_csp_benchmark_summary.csv ^
  --json reports\unique_csp_benchmark_summary.json ^
  --markdown reports\unique_csp_benchmark_report.md
```

Markdown sections:

```text
# Unique Verifiable CSP Benchmark Report

## Summary
## Output validity
## Constraint faithfulness
## Structure/prototype match
## MLIP/relaxation robustness
## Evidence traceability
## Solver certificate
## Audit bundle completeness
## Retrieval ablation
## Repairability
## Failure cases
## Why this benchmark is different
```

---

# EPIC 10 — Unique Benchmark Prompt Suites

## Goal

Create prompt suites specifically designed to test traceability, constraints, solver feasibility, retrieval, and repairability.

## Ticket 10.1 — Core unique prompt set

Create:

```text
benchmarks/unique_verifiable_csp/traceable_csp_prompts_v1.csv
```

Columns:

```csv
prompt_id,
benchmark_type,
input_text,
target_formula,
target_structure_family,
target_space_group,
reference_cif_path,
expected_constraints,
expected_evidence_family,
expected_solver_status,
num_attempts,
notes
```

Seed prompts:

```text
Generate a cubic perovskite BaTiO3 structure using retrieved perovskite evidence.
Generate a spinel-like ZnFe2O4 structure using evidence from known spinel oxides.
Generate a fluorite CeO2 structure with no Ce-Ce contact below 3 Å.
Generate a rutile TiO2-like structure with Ti octahedrally coordinated by oxygen.
Generate a pyrite-like FeS2 structure and preserve the S-S dumbbell motif.
Generate a rocksalt NiO crystal with Ni and O occupying alternating FCC sublattices.
Generate Li6PS5Cl using sulfide solid-electrolyte evidence, not oxide examples.
Generate an intentionally infeasible rocksalt AB3 structure in a two-site primitive cell.
```

## Ticket 10.2 — Prompt suite documentation

Add:

```text
benchmarks/unique_verifiable_csp/README.md
```

Explain each prompt type:

```text
traceability
constraint faithfulness
solver infeasibility
retrieval ablation
repairability
evidence faithfulness
audit completeness
```

---

# EPIC 11 — CLI Integration

## Goal

Expose the unique benchmark stack through SCA CLI.

Required commands:

```bat
python -m sca.cli inspect-run-bundle --help

python -m sca.cli run-retrieval-ablation-benchmark --help

python -m sca.cli run-repairability-benchmark --help

python -m sca.cli unique-csp-benchmark-summary --help
```

Optional if evaluator wiring supports them:

```bat
python -m sca.cli benchmark manifest ... --evaluators evidence_traceability,constraint_faithfulness,solver_certificate,evidence_faithfulness,audit_bundle_completeness
```

---

# EPIC 12 — Tests

## Goal

Add tests without requiring the real generator, QLIP, CHGNet, MACE, SevenNet, or internet.

Test using synthetic fixtures and fake run bundles.

Required tests:

```text
traceable run schema validates
run bundle loader handles missing artifacts
inspect-run-bundle CLI writes CSV/JSON/Markdown
evidence_traceability evaluator scores complete vs incomplete evidence
constraint_faithfulness evaluator handles formula/SG/prototype constraints
solver_certificate evaluator handles optimal/infeasible/missing logs
retrieval ablation runner works with fake generator
repairability runner works with fake repair command
evidence_faithfulness detects unsupported claims
audit_bundle_completeness scores complete/incomplete bundles
unique composite score computes expected value
unique-csp-benchmark-summary writes Markdown sections
prompt suite CSVs parse
all new CLIs show help
```

---

# EPIC 13 — Documentation

Add:

```text
docs/UNIQUE_VERIFIABLE_CSP_BENCHMARKS.md
```

Update:

```text
README.md
docs/BENCHMARKING.md
docs/EVALUATORS.md
docs/PAPER_BENCHMARKS.md
```

Documentation must explain:

```text
existing crystal-generation benchmarks ask: did you generate a plausible CIF?
our unique benchmark asks: did you generate a traceable, constraint-grounded, solver-backed CSP run?
```

Include Windows commands for:

```bat
python -m sca.cli inspect-run-bundle ^
  --run-dir reports\e2e_runs\example_run ^
  --out reports\run_bundle_inspection.csv ^
  --json reports\run_bundle_inspection.json ^
  --markdown reports\run_bundle_inspection.md

python -m sca.cli run-retrieval-ablation-benchmark ^
  --prompts benchmarks\unique_verifiable_csp\retrieval_ablation_prompts.csv ^
  --generator-command "python tests\fixtures\fake_generator.py --prompt {prompt} --out-dir {out_dir} --attempts {num_attempts}" ^
  --retrieval-modes none,metadata,evidence_spp ^
  --out-dir reports\retrieval_ablation ^
  --summary reports\retrieval_ablation_summary.csv ^
  --json reports\retrieval_ablation_summary.json ^
  --markdown reports\retrieval_ablation_report.md

python -m sca.cli run-repairability-benchmark ^
  --cases benchmarks\unique_verifiable_csp\repair_cases.csv ^
  --repair-command "python tests\fixtures\fake_repair.py --input-cif {input_cif} --prompt {prompt} --out-dir {out_dir}" ^
  --out-dir reports\repairability ^
  --summary reports\repairability_summary.csv ^
  --json reports\repairability_summary.json ^
  --markdown reports\repairability_report.md

python -m sca.cli unique-csp-benchmark-summary ^
  --results reports\e2e_benchmark_results.csv ^
  --bundles reports\e2e_runs ^
  --out reports\unique_csp_benchmark_summary.csv ^
  --json reports\unique_csp_benchmark_summary.json ^
  --markdown reports\unique_csp_benchmark_report.md
```

---

# EPIC 14 — Smoke Runs

Run fake/synthetic smoke tests only.

Commands:

```bat
python -m sca.cli inspect-run-bundle ^
  --run-dir tests\fixtures\traceable_run_bundle ^
  --out reports\run_bundle_inspection.csv ^
  --json reports\run_bundle_inspection.json ^
  --markdown reports\run_bundle_inspection.md
```

```bat
python -m sca.cli run-retrieval-ablation-benchmark ^
  --prompts benchmarks\unique_verifiable_csp\retrieval_ablation_prompts.csv ^
  --generator-command "python tests\fixtures\fake_generator.py --prompt {prompt} --out-dir {out_dir} --attempts {num_attempts}" ^
  --retrieval-modes none,metadata,evidence_spp ^
  --out-dir reports\retrieval_ablation ^
  --summary reports\retrieval_ablation_summary.csv ^
  --json reports\retrieval_ablation_summary.json ^
  --markdown reports\retrieval_ablation_report.md
```

```bat
python -m sca.cli run-repairability-benchmark ^
  --cases benchmarks\unique_verifiable_csp\repair_cases.csv ^
  --repair-command "python tests\fixtures\fake_repair.py --input-cif {input_cif} --prompt {prompt} --out-dir {out_dir}" ^
  --out-dir reports\repairability ^
  --summary reports\repairability_summary.csv ^
  --json reports\repairability_summary.json ^
  --markdown reports\repairability_report.md
```

```bat
python -m sca.cli unique-csp-benchmark-summary ^
  --results reports\e2e_fake_runs\e2e_benchmark_results.csv ^
  --bundles reports\e2e_fake_runs ^
  --out reports\unique_csp_benchmark_summary.csv ^
  --json reports\unique_csp_benchmark_summary.json ^
  --markdown reports\unique_csp_benchmark_report.md
```

---

# EPIC 15 — Verification

Run:

```bat
pytest -q --basetemp .pytest_tmp
ruff check sca tests scripts
python -m sca.cli inspect-run-bundle --help
python -m sca.cli run-retrieval-ablation-benchmark --help
python -m sca.cli run-repairability-benchmark --help
python -m sca.cli unique-csp-benchmark-summary --help
```

---

# Definition of Done

This ticket stack is complete when:

```text
Traceable run artifact schema exists.
Run bundle inspection CLI exists.
Evidence traceability evaluator exists.
Constraint faithfulness evaluator exists.
Solver certificate evaluator exists.
Evidence faithfulness evaluator exists.
Audit bundle completeness evaluator exists.
Retrieval ablation runner exists.
Repairability benchmark runner exists.
Unique composite benchmark summary exists.
Unique benchmark prompt suites exist.
Docs explain why this benchmark is unique.
Fake/synthetic smoke runs work.
Tests pass.
Ruff passes.
```

Final implementation report must include:

```text
files added/changed
CLIs added
evaluators added
prompt/benchmark assets added
smoke outputs generated
test results
known limitations
which metrics require real LLM-CSP/QLIP integration
which metrics work with synthetic bundles
```

---

# Scientific Claim Enabled

When this stack is implemented, the paper can claim:

> Existing crystal-generation benchmarks primarily evaluate whether a model can emit plausible CIFs. We introduce a complementary benchmark for traceable, constraint-grounded text-to-CSP workflows. It evaluates whether a system can convert a natural-language materials request into a reproducible CSP run with retrieved evidence, derived constraints, solver status, generated candidates, validation diagnostics, and auditable failure explanations.
