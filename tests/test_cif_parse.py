from pathlib import Path

from sca.evaluators.cif_parse import parse_cif


FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_cif_parse_result() -> None:
    structure, result = parse_cif(FIXTURES / "tiny_valid.cif")

    assert structure is not None
    assert result.parse_ok is True
    assert result.reduced_formula == "NaCl"
    assert result.lattice_a is not None


def test_malformed_cif_parse_result() -> None:
    structure, result = parse_cif(FIXTURES / "malformed.cif")

    assert structure is None
    assert result.parse_ok is False
    assert result.error_type is not None
