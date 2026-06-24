"""Build run manifests by mapping generated CIF files to paper target rows."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
from pymatgen.core import Composition

from sca.evaluators.cif_parse import parse_cif
from sca.io import discover_cif_files
from sca.paper_benchmarks.schema import PaperBenchmarkTarget, load_paper_manifest


RUN_MANIFEST_COLUMNS = [
    "cif_path",
    "file_name",
    "benchmark_id",
    "benchmark_group",
    "attempt_id",
    "target_formula",
    "target_reduced_formula",
    "target_structure_family",
    "target_space_group",
    "target_space_group_number",
    "target_crystal_system",
    "prompt",
    "target_cif_path",
    "reference_cif_path",
    "reference_id",
    "reference_source",
    "paper_source",
    "paper_name",
    "hull_reference_path",
    "target_energy_above_hull",
    "target_formation_energy_per_atom",
    "target_band_gap",
    "property_name",
    "property_target_value",
    "property_target_unit",
    "property_tolerance",
    "mapping_status",
    "mapping_confidence",
    "mapping_reason",
    "generated_reduced_formula",
    "generated_formula",
    "notes",
]


def build_paper_run_manifest(
    targets_csv: str | Path,
    generated_folder: str | Path,
    out_csv: str | Path,
    recursive: bool = True,
) -> pd.DataFrame:
    targets, _, warnings = load_paper_manifest(targets_csv)
    paths = discover_cif_files(generated_folder, recursive=recursive)
    rows = []
    attempt_counts: Counter[str] = Counter()
    target_index = _target_index(targets)
    for path in paths:
        generated = _generated_info(path)
        target, status, confidence, reason = _match_target(path, generated, targets, target_index)
        benchmark_id = target.benchmark_id if target else _unmapped_benchmark_id(generated, path)
        attempt_counts[benchmark_id] += 1
        rows.append(
            _manifest_row(
                path=path,
                generated=generated,
                target=target,
                benchmark_id=benchmark_id,
                attempt_id=attempt_counts[benchmark_id],
                mapping_status=status,
                mapping_confidence=confidence,
                mapping_reason=reason,
            )
        )
    frame = pd.DataFrame(rows, columns=RUN_MANIFEST_COLUMNS)
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_csv, index=False)
    if warnings:
        warning_path = out_csv.with_suffix(".warnings.txt")
        warning_path.write_text("\n".join(warnings) + "\n", encoding="utf-8")
    return frame


def _target_index(targets: list[PaperBenchmarkTarget]) -> dict[str, list[PaperBenchmarkTarget]]:
    index: dict[str, list[PaperBenchmarkTarget]] = defaultdict(list)
    for target in targets:
        for formula in (target.target_reduced_formula, target.target_formula):
            normalized = _formula_key(formula)
            if normalized:
                index[normalized].append(target)
    return index


def _match_target(
    path: Path,
    generated: dict[str, Any],
    targets: list[PaperBenchmarkTarget],
    target_index: dict[str, list[PaperBenchmarkTarget]],
) -> tuple[PaperBenchmarkTarget | None, str, float, str]:
    formula_key = _formula_key(generated.get("reduced_formula"))
    candidates = target_index.get(formula_key, []) if formula_key else []
    if candidates:
        best = _best_filename_candidate(path.name, candidates)
        return best, "matched", 1.0, "parsed reduced formula matched target"
    filename_key = _normalize_token(path.stem)
    for target in targets:
        formula_token = _normalize_token(target.target_formula)
        family_token = _normalize_token(target.target_structure_family)
        if formula_token and formula_token in filename_key:
            return target, "matched", 0.85, "filename contains target formula"
        if family_token and formula_token and formula_token in filename_key and family_token in filename_key:
            return target, "matched", 0.90, "filename contains target formula and family"
    return None, "unmapped", 0.0, "no target formula or filename match"


def _best_filename_candidate(file_name: str, candidates: list[PaperBenchmarkTarget]) -> PaperBenchmarkTarget:
    if len(candidates) == 1:
        return candidates[0]
    filename = _normalize_token(file_name)
    scored = []
    for target in candidates:
        score = 0
        family = _normalize_token(target.target_structure_family)
        space_group = _normalize_token(target.target_space_group)
        if family and family in filename:
            score += 2
        if space_group and space_group in filename:
            score += 1
        scored.append((score, target))
    scored.sort(key=lambda item: (-item[0], item[1].benchmark_id))
    return scored[0][1]


def _manifest_row(
    path: Path,
    generated: dict[str, Any],
    target: PaperBenchmarkTarget | None,
    benchmark_id: str,
    attempt_id: int,
    mapping_status: str,
    mapping_confidence: float,
    mapping_reason: str,
) -> dict[str, Any]:
    reference_path = target.reference_cif_path if target else None
    return {
        "cif_path": str(path),
        "file_name": path.name,
        "benchmark_id": benchmark_id,
        "benchmark_group": target.benchmark_group if target else "A_validity",
        "attempt_id": attempt_id,
        "target_formula": target.target_formula if target else generated.get("reduced_formula"),
        "target_reduced_formula": target.target_reduced_formula if target else generated.get("reduced_formula"),
        "target_structure_family": target.target_structure_family if target else None,
        "target_space_group": target.target_space_group if target else None,
        "target_space_group_number": target.target_space_group_number if target else None,
        "target_crystal_system": target.target_crystal_system if target else None,
        "prompt": target.prompt if target else None,
        "target_cif_path": reference_path,
        "reference_cif_path": reference_path,
        "reference_id": target.reference_id if target else None,
        "reference_source": target.reference_source if target else None,
        "paper_source": target.paper_source if target else None,
        "paper_name": target.paper_name if target else None,
        "hull_reference_path": target.hull_reference_path if target else None,
        "target_energy_above_hull": target.target_energy_above_hull if target else None,
        "target_formation_energy_per_atom": target.target_formation_energy_per_atom if target else None,
        "target_band_gap": target.target_band_gap if target else None,
        "property_name": target.property_name if target else None,
        "property_target_value": target.property_target_value if target else None,
        "property_target_unit": target.property_target_unit if target else None,
        "property_tolerance": target.property_tolerance if target else None,
        "mapping_status": mapping_status,
        "mapping_confidence": mapping_confidence,
        "mapping_reason": mapping_reason,
        "generated_reduced_formula": generated.get("reduced_formula"),
        "generated_formula": generated.get("formula"),
        "notes": target.notes if target else "Generated CIF did not map to a paper target row",
    }


def _generated_info(path: Path) -> dict[str, Any]:
    structure, parsed = parse_cif(path)
    if structure is None:
        return {"formula": None, "reduced_formula": None, "parse_error": parsed.error_message}
    composition = structure.composition
    return {
        "formula": composition.formula,
        "reduced_formula": composition.reduced_formula,
        "parse_error": None,
    }


def _formula_key(formula: str | None) -> str | None:
    if not formula:
        return None
    try:
        return _normalize_token(Composition(formula).reduced_formula)
    except Exception:
        return _normalize_token(formula)


def _normalize_token(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _unmapped_benchmark_id(generated: dict[str, Any], path: Path) -> str:
    formula = _normalize_token(generated.get("reduced_formula"))
    if formula:
        return f"unmapped_{formula}"
    return f"unmapped_{_normalize_token(path.stem)}"
