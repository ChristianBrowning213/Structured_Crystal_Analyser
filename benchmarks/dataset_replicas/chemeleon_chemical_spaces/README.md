# Chemeleon Chemical-Space Scaffold

Purpose: reproduce Chemeleon-style validity, relaxation/convergence,
chemical-space, and metastability checks.

Chemical spaces:
- Ti-O
- Zn-Ti-O
- Li-P-S-Cl

Required input files:
- `chemical_spaces.csv`
- Generated CIF manifest with formulas and optional hull reference paths.
- Local hull references registered in `benchmarks/assets/hull_reference_bundles.csv`.

Metrics computable:
Validity, minimum-distance pass rate, MLIP convergence/relaxation rate,
predicted E_hull <= 0.15 eV/atom, stable/metastable counts, uniqueness, and
new space-group counts when the needed columns are supplied.

Comparator values:
Chemeleon validity 98-99%, TiO2 MACE-MP convergence 539/549 = 98.2%,
Li-P-S-Cl stable count 17, metastable count 435, within 0.15 eV/atom ~80%.

Warning: scaffold does not include hull data and cannot produce exact Chemeleon
claims until local reference hulls and protocol-matching generated sets exist.
