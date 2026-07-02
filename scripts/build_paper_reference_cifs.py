"""Build prototype reference CIFs for paper-target challenge rows.

The generated CIFs are never used as references.  These are simple,
auditable crystallographic prototypes aligned to the target family and
composition where the family is unambiguous.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from pymatgen.core import Lattice, Structure
from pymatgen.io.cif import CifWriter


ROOT = Path(__file__).resolve().parents[1]
TARGETS = ROOT / "benchmarks" / "paper_targets" / "paper_targets_v1.csv"
REFERENCE_DIR = ROOT / "benchmarks" / "paper_targets" / "reference_cifs"
REGISTRY = ROOT / "benchmarks" / "paper_targets" / "reference_cifs_v1.csv"


@dataclass(frozen=True)
class ReferenceSpec:
    benchmark_id: str
    formula: str
    family: str
    prototype: str
    space_group: str
    lattice_a: float
    source: str
    notes: str

    @property
    def reference_id(self) -> str:
        return f"prototype_{self.benchmark_id}"

    @property
    def file_name(self) -> str:
        return f"{self.benchmark_id}.cif"


SPECS = [
    ReferenceSpec("sanity_batio3_perovskite", "BaTiO3", "perovskite", "cubic ABO3 perovskite", "Pm-3m", 4.01, "prototype", "Ideal cubic perovskite prototype."),
    ReferenceSpec("sanity_catio3_perovskite", "CaTiO3", "perovskite", "cubic ABO3 perovskite", "Pm-3m", 3.85, "prototype", "Ideal cubic perovskite prototype; real CaTiO3 may be distorted."),
    ReferenceSpec("generated_challenge_cspbbr3_perovskite", "CsPbBr3", "perovskite", "cubic ABX3 perovskite", "Pm-3m", 5.87, "prototype", "Ideal cubic halide perovskite prototype."),
    ReferenceSpec("generated_challenge_cssni3_mapbi3_proxy", "CsSnI3", "proxy/perovskite", "cubic ABX3 perovskite", "Pm-3m", 6.20, "prototype", "Reference follows parsed CsSnI3 proxy composition, not MAPbI3."),
    ReferenceSpec("generated_challenge_basno3_perovskite", "BaSnO3", "perovskite", "cubic ABO3 perovskite", "Pm-3m", 4.12, "prototype", "Ideal cubic perovskite prototype."),
    ReferenceSpec("generated_challenge_baceo3_perovskite", "BaCeO3", "perovskite", "cubic ABO3 perovskite", "Pm-3m", 4.40, "prototype", "Ideal cubic perovskite prototype; real BaCeO3 may be distorted."),
    ReferenceSpec("sanity_nacl_rocksalt", "NaCl", "rocksalt", "B1 rocksalt", "Fm-3m", 5.64, "prototype", "Canonical rocksalt prototype."),
    ReferenceSpec("sanity_lif_rocksalt", "LiF", "rocksalt", "B1 rocksalt", "Fm-3m", 4.02, "prototype", "Canonical rocksalt prototype."),
    ReferenceSpec("sanity_nio_rocksalt", "NiO", "rocksalt", "B1 rocksalt", "Fm-3m", 4.17, "prototype", "Canonical rocksalt prototype."),
    ReferenceSpec("sanity_coo_rocksalt", "CoO", "rocksalt", "B1 rocksalt", "Fm-3m", 4.26, "prototype", "Canonical rocksalt prototype."),
    ReferenceSpec("generated_challenge_feo_wustite", "FeO", "wustite/rocksalt", "B1 rocksalt", "Fm-3m", 4.33, "prototype", "Wustite-like rocksalt prototype."),
    ReferenceSpec("generated_challenge_mno_rocksalt", "MnO", "rocksalt", "B1 rocksalt", "Fm-3m", 4.44, "prototype", "Canonical rocksalt prototype."),
    ReferenceSpec("generated_challenge_pbs_rocksalt", "PbS", "rocksalt", "B1 rocksalt", "Fm-3m", 5.94, "prototype", "Canonical rocksalt galena prototype."),
    ReferenceSpec("sanity_zns_sphalerite", "ZnS", "sphalerite", "zinc blende", "F-43m", 5.41, "prototype", "Canonical sphalerite/zinc-blende prototype."),
    ReferenceSpec("sanity_zro2_fluorite", "ZrO2", "fluorite", "fluorite", "Fm-3m", 5.09, "prototype", "Fluorite prototype; not the monoclinic ground-state polymorph."),
    ReferenceSpec("sanity_ceo2_fluorite", "CeO2", "fluorite", "fluorite", "Fm-3m", 5.41, "prototype", "Canonical fluorite prototype."),
    ReferenceSpec("generated_challenge_mgal2o4_spinel", "MgAl2O4", "spinel", "normal spinel", "Fd-3m", 8.08, "prototype", "Normal spinel prototype."),
    ReferenceSpec("generated_challenge_znfe2o4_spinel", "ZnFe2O4", "spinel", "normal spinel", "Fd-3m", 8.44, "prototype", "Normal spinel prototype."),
    ReferenceSpec("generated_challenge_limn2o4_spinel", "LiMn2O4", "spinel", "normal spinel", "Fd-3m", 8.24, "prototype", "Spinel prototype."),
    ReferenceSpec("generated_challenge_fes2_pyrite", "FeS2", "pyrite", "pyrite", "Pa-3", 5.42, "prototype", "Pyrite prototype."),
    ReferenceSpec("generated_challenge_cos2_pyrite", "CoS2", "pyrite", "pyrite", "Pa-3", 5.54, "prototype", "Pyrite prototype."),
    ReferenceSpec("generated_challenge_nis2_pyrite", "NiS2", "pyrite", "pyrite", "Pa-3", 5.69, "prototype", "Pyrite prototype."),
]


def main() -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    registry_rows = []
    specs_by_id = {spec.benchmark_id: spec for spec in SPECS}

    for spec in SPECS:
        structure = build_structure(spec)
        reference_path = REFERENCE_DIR / spec.file_name
        CifWriter(structure, symprec=0.1).write_file(reference_path)
        registry_rows.append(
            {
                "benchmark_id": spec.benchmark_id,
                "reference_id": spec.reference_id,
                "reference_cif_path": str(Path("reference_cifs") / spec.file_name),
                "reference_source": spec.source,
                "reference_formula": spec.formula,
                "reference_family": spec.family,
                "reference_prototype": spec.prototype,
                "reference_space_group": spec.space_group,
                "notes": spec.notes,
            }
        )

    with REGISTRY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(registry_rows[0]))
        writer.writeheader()
        writer.writerows(registry_rows)

    update_targets(specs_by_id)
    print(f"Wrote {len(SPECS)} reference CIFs to {REFERENCE_DIR}")
    print(f"Wrote registry to {REGISTRY}")
    print(f"Updated references in {TARGETS}")


def build_structure(spec: ReferenceSpec) -> Structure:
    formula = parse_formula(spec.formula)
    family = spec.family.lower()
    lattice = Lattice.cubic(spec.lattice_a)

    if "perovskite" in family:
        a, b, x = formula_elements(spec.formula)
        return Structure.from_spacegroup(
            spec.space_group,
            lattice,
            [a, b, x],
            [[0, 0, 0], [0.5, 0.5, 0.5], [0.5, 0.5, 0]],
        )
    if "rocksalt" in family or "wustite" in family:
        cation, anion = formula_elements(spec.formula)
        return Structure.from_spacegroup(
            spec.space_group,
            lattice,
            [cation, anion],
            [[0, 0, 0], [0.5, 0.5, 0.5]],
        )
    if "sphalerite" in family:
        cation, anion = formula_elements(spec.formula)
        return Structure.from_spacegroup(
            spec.space_group,
            lattice,
            [cation, anion],
            [[0, 0, 0], [0.25, 0.25, 0.25]],
        )
    if "fluorite" in family:
        cation = next(iter(formula))
        anion = [el for el in formula if el != cation][0]
        return Structure.from_spacegroup(
            spec.space_group,
            lattice,
            [cation, anion],
            [[0, 0, 0], [0.25, 0.25, 0.25]],
        )
    if "spinel" in family:
        a, b, oxygen = formula_elements(spec.formula)
        return Structure.from_spacegroup(
            spec.space_group,
            lattice,
            [a, b, oxygen],
            [[0.5, 0.5, 0.5], [0.125, 0.125, 0.125], [0.261, 0.261, 0.261]],
        )
    if "pyrite" in family:
        metal, sulfur = formula_elements(spec.formula)
        return Structure.from_spacegroup(
            spec.space_group,
            lattice,
            [metal, sulfur],
            [[0, 0, 0], [0.385, 0.385, 0.385]],
        )
    raise ValueError(f"No prototype builder for {spec.benchmark_id}: {spec.family}")


def update_targets(specs_by_id: dict[str, ReferenceSpec]) -> None:
    with TARGETS.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.readline()
    if not rows:
        return
    fieldnames = list(rows[0])
    for row in rows:
        spec = specs_by_id.get(row["benchmark_id"])
        if not spec:
            continue
        row["reference_cif_path"] = str(Path("reference_cifs") / spec.file_name)
        row["reference_id"] = spec.reference_id
        row["reference_source"] = spec.source
    with TARGETS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_formula(formula: str) -> dict[str, int]:
    from pymatgen.core import Composition

    return {str(el): int(amount) for el, amount in Composition(formula).as_dict().items()}


def formula_elements(formula: str) -> list[str]:
    return list(parse_formula(formula))


if __name__ == "__main__":
    main()
