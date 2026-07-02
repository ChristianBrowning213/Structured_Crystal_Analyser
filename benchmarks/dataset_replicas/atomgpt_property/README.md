# AtomGPT Property Scaffold

Purpose: reproduce property-target and formation-energy MAE style benchmarks.

Required input files:
- `property_targets.csv`
- Generated or predicted property CSV with target IDs.

Expected columns:
`benchmark_id,cif_path,target_formula,target_formation_energy_per_atom,target_band_gap,property_name,target_property_value,target_property_unit,property_tolerance,notes`

Metrics computable:
formation_energy_mae, band_gap_mae, target_property_mae, and hit rate within
tolerance when predictions are supplied.

Comparator values:
AtomGPT formation-energy MAE 0.072 eV/atom; ALIGNN baseline 0.033 eV/atom;
CGCNN 0.063 eV/atom; CFID 0.142 eV/atom.

Warning: this scaffold contains schemas and examples only, not benchmark claims.
