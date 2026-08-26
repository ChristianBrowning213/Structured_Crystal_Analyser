"""Run parse, geometry, severe-contact, and symmetry checks for one demo CIF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from sca.evaluators.bonds import evaluate_bonds
from sca.evaluators.geometry import evaluate_geometry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cif", type=Path, required=True)
    args = parser.parse_args()
    structure = Structure.from_file(args.cif)
    geometry = evaluate_geometry(structure)
    bonds = evaluate_bonds(structure)
    symmetry = {
        str(tolerance): SpacegroupAnalyzer(structure, symprec=tolerance, angle_tolerance=5.0).get_space_group_symbol()
        for tolerance in (0.001, 0.01, 0.1)
    }
    payload = {
        "parse_ok": True,
        "geometry": geometry.model_dump(),
        "bonds": bonds.model_dump(),
        "detected_space_groups": symmetry,
        "status": "PASS" if geometry.geometry_ok and bonds.num_bad_contacts == 0 else "FAIL",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
