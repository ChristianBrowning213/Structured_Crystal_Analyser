SCA Advanced Energetic + DFT Validation Ticket Stack
Goal

Extend SCA from:

crystallographic validity
+
MLIP pre-DFT screening

to:

generated CIF
    ↓
crystallographic intent validation
    ↓
multi-MLIP static screening
    ↓
MLIP relaxation
    ↓
post-relaxation crystallographic validation
    ↓
DFT preparation / execution / collection
    ↓
post-DFT crystallographic validation
    ↓
DFT formation energy / convex hull
    ↓
one complete scientific validation report

The important rule throughout:

SCA is the analysis/orchestration layer. The DFT package remains the actual electronic-structure engine.

EPIC 0 — Freeze the current paper validation set
T0.1 — Create the advanced-analysis paper manifest

Create:

benchmarks/paper_advanced_validation/
    PAPER_16_MANIFEST.csv

Include the current 16:

MgO
TiN
ZrO2
BaTiO3
CaTiO3
SrTiO3
CsPbBr3
CsPbCl3
CsSnI3
ZnFe2O4
MgAl2O4
CoFe2O4
Li6PS5Cl
LiCoO2
LiFePO4
Li2FeO3

Fields:

candidate_id
formula
family
cif_path
cif_sha256
target_formula
target_space_group
target_family
intent_source
Acceptance
16/16 CIFs exist.
SHA256 recorded.
NASICON/NZP absent.
Manifest contains original intent links.
T0.2 — Freeze the starting structures

Before any relaxation:

artifacts/paper_advanced_validation/raw/

Record:

sha256
formula
space group
volume
site count
SCA intent result
minimum distance
bad contacts
Acceptance

This becomes the immutable pre-relaxation baseline.

EPIC 1 — Existing MLIP stack: run it properly

This is mostly execution and reporting, not new model implementation.

The existing benchmark pattern already invokes chgnet_static, chgnet_relax, m3gnet_static, mace_static, sevennet_static and mlip_ensemble.

T1.1 — Backend readiness audit

Run:

python -m sca.cli verify-backends

Produce:

MLIP_BACKEND_READINESS.csv
MLIP_BACKEND_READINESS.md

For:

CHGNet
M3GNet / MatGL
MACE
SevenNet
ALIGNN if retained
Acceptance

Each backend is:

READY
SKIPPED_DEPENDENCY
SKIPPED_MODEL
FAILED

Never silently absent.

T1.2 — Static MLIP campaign

Run all available static models over all 16 raw CIFs.

Record per model:

energy_per_atom
max_force
mean_force
stress_norm
runtime
model name
model version
device
success/failure

Outputs:

MLIP_STATIC_RESULTS.csv
MLIP_STATIC_RESULTS.jsonl
MODEL_SUPPORT_MATRIX.csv
Important

Do not directly average raw energies from unrelated MLIP models.

Use model-by-model values and within-model rankings for ensemble comparison, which SCA already appears designed to do.

T1.3 — Ensemble disagreement analysis

For each candidate calculate:

models_available
energy_rank_consensus
force_rank_consensus
rank_variance
disagreement_flag

Outputs:

MLIP_ENSEMBLE_RESULTS.csv
MLIP_DISAGREEMENT_CASES.csv
Acceptance

A candidate is never called “stable” simply because one model returns a low value.

EPIC 2 — MLIP relaxation campaign
T2.1 — Run CHGNet relaxation on all 16

Use a frozen configuration, for example:

max_steps
fmax
cell_filter
device
model version

Do not pick values silently; persist them.

Output per candidate:

initial_energy_per_atom
relaxed_energy_per_atom
delta_energy_per_atom
initial_max_force
final_max_force
relax_steps
converged
initial_volume
relaxed_volume
volume_change_pct
relaxed_cif_path

The current SCA code already has a structured chgnet_relax route and tests its failure handling.

T2.2 — Preserve both raw and relaxed structures

Never overwrite:

generated.cif

Write:

relaxed/chgnet/<candidate_id>.cif

Record both hashes.

Acceptance

Raw candidate hash remains unchanged.

T2.3 — Structural displacement analysis

Add an initial → relaxed evaluator.

Metrics:

atomic_rms_displacement_A
atomic_max_displacement_A
lattice_a_change_pct
lattice_b_change_pct
lattice_c_change_pct
angle_change_max_deg
volume_change_pct

Do not require reference-crystal matching.

This comparison is:

generated structure
vs
its own relaxed structure
EPIC 3 — Post-MLIP crystallographic revalidation
T3.1 — Run SCA again on every relaxed CIF

Check:

composition
site count
space group
crystal system
family/topology
geometry
bad contacts
minimum distance
T3.2 — Intent-retention evaluator

Create:

relaxation_intent_retention

Metrics:

composition_retained
site_count_retained

requested_sg_initial
requested_sg_relaxed
space_group_retained

target_family
family_initial_status
family_relaxed_status
family_retained

geometry_valid_after
bad_contacts_after

overall_relaxation_status

Status:

ROBUST
MODIFIED_BUT_VALID
COLLAPSED
FAILED_RELAXATION
Suggested meanings

ROBUST

relaxation converged;
composition retained;
geometry valid;
requested family/topology retained;
no severe contacts.

MODIFIED_BUT_VALID

structure changed/symmetry lowered;
still crystallographically valid and retains core intended family.

COLLAPSED

topology lost, severe contacts introduced, pathological volume change, etc.
EPIC 4 — Advanced relaxation report
T4.1 — Build one MLIP validation summary

Create:

PAPER_16_MLIP_RELAXATION_SUMMARY.csv
PAPER_16_MLIP_RELAXATION_SUMMARY.md

Headline metrics:

static evaluable X/16
relaxation converged X/16
composition retained X/16
family retained X/16
geometry valid after relaxation X/16
zero bad contacts after relaxation X/16

median delta_E/atom
median volume change
median RMS displacement
T4.2 — Make publication figure

A simple figure, not another giant table.

Potential panels:

A | Energy decrease after relaxation
B | Volume change %
C | RMS atomic displacement
D | Intent retained after relaxation

Or one horizontal compact figure.

Title:

Generated structures remain crystallographically coherent under MLIP relaxation

Do not call it thermodynamic stability.

EPIC 5 — DFT data contract

This is where genuinely new infrastructure begins.

The current roadmap only specifies ingesting external DFT results and explicitly says SCA itself does not yet run DFT.

T5.1 — Define DFTCalculationSpec

Create:

sca/dft/schema.py

Fields:

calculation_id
candidate_id
input_cif_path
input_cif_sha256

engine
calculation_type

xc_functional
dispersion
pseudopotential_family
cutoff_energy

kpoint_scheme
kpoint_spacing

spin_polarized
initial_magnetic_moments

hubbard_u

energy_tolerance
force_tolerance
stress_tolerance
max_steps

charge
smearing
metadata
T5.2 — Define calculation types

Support explicitly:

RELAX
STATIC

Later:

PHONON
ELASTIC
BAND_STRUCTURE
DOS

but keep those out of v1.

T5.3 — Define DFTResult

Fields:

status
converged

initial_cif
relaxed_cif

total_energy_eV
energy_per_atom_eV

max_force_eV_A
stress

num_ionic_steps
num_scf_iterations

final_volume
runtime_seconds

stdout_path
stderr_path

engine_version
EPIC 6 — DFT backend abstraction
T6.1 — Add generic backend interface

Create:

sca/dft/backends/base.py

Interface:

prepare(...)
parse(...)
validate(...)

Do not place engine-specific logic in CLI code.

T6.2 — Implement first real DFT backend

Choose the package actually available/licensed on Barkla.

For example:

CASTEP
or
VASP

Do one first.

Then add the second adapter later.

Required behavior:

CIF
→
DFT input files

No job is run yet.

T6.3 — Input reproducibility manifest

Each prepared calculation directory contains:

calculation.json
input.cif
input.sha256
engine input files
environment.json
Acceptance

The calculation can be reconstructed without guessing settings.

EPIC 7 — Slurm / Barkla execution
T7.1 — Slurm job builder

Generate:

submit.slurm

from a versioned template.

Configuration:

partition
time
nodes
tasks
memory
account
modules
executable

Do not hardcode user-specific paths inside scientific records.

T7.2 — sca dft prepare

Example:

sca dft prepare ^
  --manifest PAPER_16_MANIFEST.csv ^
  --backend castep ^
  --config configs\dft_pbe_relax.yaml ^
  --out-dir reports\dft\prepared
T7.3 — sca dft submit
sca dft submit ^
  --calculations reports\dft\prepared

Record:

Slurm job ID
submit time
calculation ID
T7.4 — sca dft status

Output:

PREPARED
QUEUED
RUNNING
COMPLETED
FAILED
TIMEOUT
NOT_CONVERGED
T7.5 — sca dft collect

Parse completed calculations and produce:

DFT_RESULTS.csv
DFT_RESULTS.jsonl
EPIC 8 — Failure handling
T8.1 — Structured DFT failure taxonomy

Examples:

SCF_NOT_CONVERGED
IONIC_NOT_CONVERGED
WALLTIME
ENGINE_CRASH
MISSING_OUTPUT
BAD_PSEUDOPOTENTIAL
MEMORY
STRUCTURE_COLLAPSE
UNKNOWN
T8.2 — No silent repair

SCA may recommend:

increase SCF iterations
increase walltime
change mixing
retry ionic relaxation

but must never silently change scientific settings.

Every rerun gets:

calculation_id_v2
parent_calculation_id
changed_parameters
reason
EPIC 9 — Post-DFT structural validation
T9.1 — Re-run full SCA on DFT-relaxed CIF

Compare:

generated
→
MLIP relaxed
→
DFT relaxed

Record:

composition retained
site count retained
space group
crystal system
family topology
minimum distance
bad contacts
volume change
atomic RMS displacement
T9.2 — DFT relaxation status

Define:

DFT_ROBUST
DFT_VALID_SYMMETRY_LOWERED
DFT_TOPOLOGY_CHANGED
DFT_COLLAPSED
DFT_NOT_CONVERGED

Again:

DFT relaxation success ≠ thermodynamic stability.

EPIC 10 — Formation energies
T10.1 — Elemental chemical-potential contract

For real formation energy:

ΔE
f
	​

=E
compound
	​

−
i
∑
	​

n
i
	​

μ
i
	​


Store explicitly:

reference element
reference phase
reference energy
DFT functional
pseudopotential family
calculation settings
T10.2 — Compatible-energy guard

SCA must reject formation-energy/hull calculations if candidate and references are not compatible in:

XC functional
pseudopotential family
energy corrections
+U convention

Do not mix random Materials Project values with locally calculated incompatible energies.

EPIC 11 — Real DFT energy above hull

The existing SCA roadmap already distinguishes surrogate predicted-hull analysis from real DFT results.

T11.1 — DFT hull reference bundle schema

Create local bundles:

chemical_system
material_id
formula
DFT total energy
DFT energy/atom
formation energy
settings fingerprint
source
T11.2 — Phase diagram builder

Using pymatgen:

candidate DFT entry
+
compatible competing-phase entries
→
PhaseDiagram

Calculate:

energy_above_hull_eV_atom
is_on_hull
decomposition_products
decomposition_energy
hull_reference_count
T11.3 — Stability labels

Do not make arbitrary hard scientific claims.

Report raw E
hull
	​

, plus configurable descriptive bands such as:

ON_HULL
NEAR_HULL
ABOVE_HULL

with threshold stored in the run config.

EPIC 12 — Paper-first DFT campaign

Do not immediately run everything.

T12.1 — Six representative structures first

Suggested:

MgO
BaTiO3
ZnFe2O4
LiCoO2
LiFePO4
Li2FeO3

This covers most major families.

Goal

Check that the DFT pipeline itself is correct before spending time on 16.

T12.2 — DFT relaxation smoke

For each:

prepare
submit
collect
convergence
post-DFT SCA
Acceptance

At least one full calculation traverses:

CIF
→ DFT
→ relaxed CIF
→ SCA
→ final report

without manual data editing.

T12.3 — Expand to all 16

Only after the six-case pipeline is green.

EPIC 13 — Unified “advanced crystal analysis” report

This is the thing that makes SCA feel properly powerful.

T13.1 — sca analyse-crystal

Conceptually:

sca analyse-crystal candidate.cif ^
  --intent intent.json ^
  --level advanced

Outputs:

1. Crystallography
2. Intent satisfaction
3. Pair geometry
4. Topology
5. MLIP static predictions
6. MLIP agreement
7. MLIP relaxation
8. Relaxed intent retention
9. DFT status/results
10. DFT relaxation retention
11. Formation energy
12. Energy above hull
13. Decomposition products
14. Provenance
T13.2 — Scientific quality labels

Never collapse everything into one meaningless green tick.

Use separate dimensions:

Crystallographically valid
Intent compliant
MLIP relaxation robust
DFT relaxation robust
Thermodynamic hull position

This distinction is important.

EPIC 14 — Paper result figure

Once DFT exists, the paper can have a compact final validation figure:

Requested intent
      ↓
Generated CIF
      ↓
SCA PASS
      ↓
MLIP relaxation
      ↓
DFT relaxation
      ↓
E_hull

Possible headline values:

16/16 intent-valid
X/16 MLIP-relaxation robust
Y/6 DFT-relaxation robust
median DFT displacement
median volume change
Z/6 within chosen hull threshold

Only populate what we actually calculate.

EPIC 15 — Tests

Must include:

test_dft_schema_roundtrip
test_dft_prepare_does_not_modify_input_cif
test_backend_missing_executable_structured_failure
test_slurm_script_generation
test_dft_result_parser_success
test_dft_result_parser_not_converged
test_dft_result_parser_timeout
test_post_dft_intent_retention
test_incompatible_energy_settings_rejected
test_formation_energy_known_fixture
test_phase_diagram_known_fixture
test_ehull_known_fixture
test_missing_hull_entries_not_computable

No real DFT required in CI.

Use frozen synthetic output fixtures.

EPIC 16 — Documentation

Add:

docs/ADVANCED_CRYSTAL_ANALYSIS.md
docs/MLIP_RELAXATION_VALIDATION.md
docs/DFT_WORKFLOW.md
docs/DFT_ENERGY_CONTRACT.md
docs/HULL_ANALYSIS.md

Every document must distinguish:

SPP score
MLIP energy
MLIP relaxation
DFT energy
DFT relaxation
formation energy
energy above hull
experimental stability
Recommended implementation order

Do it in this exact sequence:

1. T0       freeze the 16 structures
2. T1       run existing static MLIP stack
3. T2       run CHGNet relaxation
4. T3       post-relax SCA intent validation
5. T4       make paper MLIP summary/figure

STOP HERE AND INSPECT RESULTS.

6. T5       DFT schemas
7. T6       first backend adapter
8. T7       Barkla/Slurm execution
9. T8       structured failure handling
10. T9      post-DFT SCA
11. T10     formation-energy contract
12. T11     real hull calculation
13. T12     six-crystal DFT campaign
14. T13     unified advanced SCA report
15. T14     paper figure
16. T15/16  tests + docs

The important thing is that tickets 1–4 should be very quick, because they mostly use capabilities you already have. The true new project begins at the DFT contract/orchestration layer.