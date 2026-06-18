"""CIF parsing evaluator."""

from __future__ import annotations

from pathlib import Path

from pymatgen.core import Structure

from sca.schemas import CifParseResult


def parse_cif(path: str | Path) -> tuple[Structure | None, CifParseResult]:
    """Parse a CIF file with pymatgen and return structured metadata."""

    try:
        structure = Structure.from_file(str(path))
    except Exception as exc:
        return None, CifParseResult(
            parse_ok=False,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

    lattice = structure.lattice
    return structure, CifParseResult(
        parse_ok=True,
        formula=structure.composition.formula,
        reduced_formula=structure.composition.reduced_formula,
        n_sites=len(structure),
        volume=float(structure.volume),
        density=float(structure.density),
        lattice_a=float(lattice.a),
        lattice_b=float(lattice.b),
        lattice_c=float(lattice.c),
        lattice_alpha=float(lattice.alpha),
        lattice_beta=float(lattice.beta),
        lattice_gamma=float(lattice.gamma),
    )
