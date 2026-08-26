"""Package paper CIFs and run CHGNet static/relaxation screens."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import math
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import torch
from chgnet.model.dynamics import StructOptimizer
from chgnet.model.model import CHGNet
from pymatgen.io.cif import CifWriter
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from sca.evaluators.bonds import evaluate_bonds
from sca.evaluators.cif_parse import parse_cif
from sca.evaluators.composition import evaluate_composition
from sca.evaluators.geometry import evaluate_geometry


SCA_ROOT = Path(__file__).resolve().parents[1]
GITHUB_ROOT = SCA_ROOT.parent
SKILL_ROOT = GITHUB_ROOT / "Skill-Loop-CSP"
SCA_FULL_ROOT = SCA_ROOT / "local_runs" / "paper_experiments_full_sca"
OUT_ROOT = SCA_ROOT / "local_runs" / "paper_experiments_chgnet_relax"
PACKAGE_ROOT = SKILL_ROOT / "artifacts" / "paper_final_cifs"
PRE_DIR = PACKAGE_ROOT / "pre_relax"
RELAX_DIR = PACKAGE_ROOT / "chgnet_relaxed"
MANIFEST_DIR = PACKAGE_ROOT / "manifests"
REPORT_DIR = PACKAGE_ROOT / "reports"
SCA_RELAX_DIR = OUT_ROOT / "relaxed_cifs"
SKILL_ARTIFACTS = SKILL_ROOT / "artifacts"

RELAXATION_PARAMETERS = {"fmax": 0.1, "steps": 80, "relax_cell": True}

PRE_MANIFEST_COLUMNS = [
    "experiment_id",
    "row_id",
    "formula",
    "target_family",
    "source_db_path",
    "source_db_scope",
    "generation_evidence_mode",
    "used_live_crystaldb_retrieval",
    "used_direct_mp_generation_lookup",
    "original_generated_cif_path",
    "packaged_pre_relax_cif_path",
    "sha256",
    "parse_ok",
    "formula_match",
    "symmetry_match",
    "geometry_contact_pass",
    "artifact_manifest_path",
    "workflow_trace_path",
]

STATIC_COLUMNS = [
    "experiment_id",
    "row_id",
    "formula",
    "pre_relax_cif_path",
    "chgnet_static_status",
    "energy_per_atom",
    "total_energy",
    "max_force",
    "mean_force",
    "stress_summary",
    "model_version",
    "error_text",
]

RELAX_COLUMNS = [
    "experiment_id",
    "row_id",
    "formula",
    "pre_relax_cif_path",
    "relaxed_cif_path",
    "relax_status",
    "converged",
    "steps",
    "initial_energy_per_atom",
    "final_energy_per_atom",
    "energy_drop_per_atom",
    "initial_max_force",
    "final_max_force",
    "initial_mean_force",
    "final_mean_force",
    "volume_initial",
    "volume_final",
    "volume_change_percent",
    "formula_preserved",
    "parse_ok_after_relax",
    "error_text",
    "model_version",
    "relaxation_parameters",
]

RELAXED_SCA_COLUMNS = [
    "experiment_id",
    "row_id",
    "formula",
    "pre_relax_cif_path",
    "relaxed_cif_path",
    "parse_ok_after_relax",
    "formula_preserved_after_relax",
    "pre_relax_space_group_number",
    "post_relax_space_group_number",
    "pre_relax_crystal_system",
    "post_relax_crystal_system",
    "pre_relax_symmetry_match",
    "post_relax_symmetry_match",
    "prototype_preserved_after_relax",
    "crystal_system_preserved_after_relax",
    "geometry_contact_pass_after_relax",
    "density_after_relax",
    "volume_after_relax",
    "volume_per_atom_after_relax",
    "min_distance_after_relax",
    "bad_contact_count_after_relax",
]

COMPARISON_COLUMNS = [
    "experiment_id",
    "row_id",
    "formula",
    "pre_relax_cif_path",
    "relaxed_cif_path",
    "chgnet_static_status",
    "relax_status",
    "converged",
    "initial_energy_per_atom",
    "final_energy_per_atom",
    "energy_drop_per_atom",
    "initial_max_force",
    "final_max_force",
    "force_reduction",
    "volume_change_percent",
    "formula_preserved_after_relax",
    "parse_ok_after_relax",
    "prototype_preserved_after_relax",
    "geometry_contact_pass_after_relax",
    "paper_use_recommendation",
]


def main() -> int:
    prepare_dirs()
    manifest_rows = read_csv(SCA_FULL_ROOT / "paper_experiments_generated_manifest.csv")
    full_sca_rows = {row["row_id"]: row for row in read_csv(SCA_FULL_ROOT / "full_sca_results.csv")}

    pre_manifest = package_pre_relax_cifs(manifest_rows, full_sca_rows)
    write_csv(MANIFEST_DIR / "PRE_RELAX_CIF_MANIFEST.csv", pre_manifest, PRE_MANIFEST_COLUMNS)
    write_json(MANIFEST_DIR / "PRE_RELAX_CIF_MANIFEST.json", {"rows": pre_manifest})
    (REPORT_DIR / "PRE_RELAX_CIF_PACKAGE_REPORT.md").write_text(render_pre_report(pre_manifest), encoding="utf-8")

    env_report = inspect_environment(pre_manifest[0]["packaged_pre_relax_cif_path"])
    write_json(OUT_ROOT / "CHGNET_ENVIRONMENT_REPORT.json", env_report)
    env_md = render_env_report(env_report)
    (OUT_ROOT / "CHGNET_ENVIRONMENT_REPORT.md").write_text(env_md, encoding="utf-8")
    (REPORT_DIR / "CHGNET_ENVIRONMENT_REPORT.md").write_text(env_md, encoding="utf-8")

    model = CHGNet.load()
    model_version = f"chgnet-{env_report['chgnet_version']}:{getattr(model, '__class__', type(model)).__name__}"
    static_rows = run_static(pre_manifest, model=model, model_version=model_version)
    write_csv(OUT_ROOT / "chgnet_static_results.csv", static_rows, STATIC_COLUMNS)
    write_json(OUT_ROOT / "chgnet_static_results.json", {"rows": static_rows})

    relax_rows = run_relax(pre_manifest, model=model, model_version=model_version)
    write_csv(OUT_ROOT / "chgnet_relax_results.csv", relax_rows, RELAX_COLUMNS)
    write_json(OUT_ROOT / "chgnet_relax_results.json", {"rows": relax_rows})

    relaxed_manifest = build_relaxed_manifest(pre_manifest, relax_rows)
    write_csv(OUT_ROOT / "relaxed_cif_manifest.csv", relaxed_manifest, ["experiment_id", "row_id", "formula", "pre_relax_cif_path", "relaxed_cif_path", "target_space_group_number", "target_crystal_system"])

    relaxed_sca_rows = validate_relaxed(pre_manifest, relax_rows, full_sca_rows)
    write_csv(OUT_ROOT / "relaxed_sca_results.csv", relaxed_sca_rows, RELAXED_SCA_COLUMNS)
    write_json(OUT_ROOT / "relaxed_sca_results.json", {"rows": relaxed_sca_rows})
    relaxed_summary = summarize_relaxed(relaxed_sca_rows, relax_rows)
    write_json(OUT_ROOT / "relaxed_sca_summary.json", relaxed_summary)
    relaxed_report = render_relaxed_report(relaxed_summary)
    (OUT_ROOT / "relaxed_sca_report.md").write_text(relaxed_report, encoding="utf-8")
    write_json(OUT_ROOT / "relaxed_sca_report.json", {"summary": relaxed_summary, "rows": relaxed_sca_rows})

    comparison = build_comparison(pre_manifest, static_rows, relax_rows, relaxed_sca_rows)
    write_csv(MANIFEST_DIR / "PRE_POST_RELAX_COMPARISON.csv", comparison, COMPARISON_COLUMNS)
    write_json(MANIFEST_DIR / "PRE_POST_RELAX_COMPARISON.json", {"rows": comparison})

    package_report = render_final_package_report(pre_manifest, relax_rows)
    relaxation_report = render_chgnet_report(env_report, static_rows, relax_rows, relaxed_summary)
    pre_post_summary = render_pre_post_summary(static_rows, relax_rows, relaxed_summary)
    (REPORT_DIR / "PAPER_FINAL_CIF_PACKAGE_REPORT.md").write_text(package_report, encoding="utf-8")
    (REPORT_DIR / "PAPER_CHGNET_RELAXATION_REPORT.md").write_text(relaxation_report, encoding="utf-8")
    (REPORT_DIR / "PAPER_PRE_POST_RELAX_SUMMARY.md").write_text(pre_post_summary, encoding="utf-8")
    copy_top_level_artifacts(package_report, relaxation_report, pre_post_summary)
    append_final_summary(static_rows, relax_rows, relaxed_summary)

    print(
        json.dumps(
            {
                "pre_relax_packaged": len(pre_manifest),
                "static_success": sum(row["chgnet_static_status"] == "ok" for row in static_rows),
                "relax_success": sum(row["relax_status"] == "ok" for row in relax_rows),
                "relaxed_cifs": sum(bool(row["relaxed_cif_path"]) for row in relax_rows),
                "out_root": str(OUT_ROOT),
                "package_root": str(PACKAGE_ROOT),
            },
            indent=2,
        )
    )
    return 0


def prepare_dirs() -> None:
    for path in [OUT_ROOT, PRE_DIR, RELAX_DIR, MANIFEST_DIR, REPORT_DIR, SCA_RELAX_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def package_pre_relax_cifs(manifest_rows: list[dict[str, str]], full_sca_rows: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen = set()
    for row in manifest_rows:
        filename = f"{safe_name(row['experiment_id'])}__{safe_name(row['row_id'])}__{safe_name(row['target_formula'])}__pre_relax.cif"
        source = Path(row["generated_cif_path"])
        target = PRE_DIR / filename
        if not source.exists():
            raise FileNotFoundError(source)
        shutil.copyfile(source, target)
        key = str(target).lower()
        if key in seen:
            raise RuntimeError(f"duplicate packaged CIF path: {target}")
        seen.add(key)
        sca = full_sca_rows.get(row["row_id"], {})
        row_dir = source.parent
        rows.append(
            {
                "experiment_id": row["experiment_id"],
                "row_id": row["row_id"],
                "formula": row["target_formula"],
                "target_family": row["target_family"],
                "source_db_path": row["source_db_path"],
                "source_db_scope": row["source_db_scope"],
                "generation_evidence_mode": row["generation_evidence_mode"],
                "used_live_crystaldb_retrieval": row["used_live_crystaldb_retrieval"],
                "used_direct_mp_generation_lookup": row["used_direct_mp_generation_lookup"],
                "original_generated_cif_path": str(source),
                "packaged_pre_relax_cif_path": str(target),
                "sha256": sha256(target),
                "parse_ok": sca.get("parse_ok", ""),
                "formula_match": sca.get("formula_match", ""),
                "symmetry_match": sca.get("prototype_symmetry_match", ""),
                "geometry_contact_pass": str(as_bool(sca.get("geometry_ok")) and as_bool(sca.get("contact_screen_pass"))),
                "artifact_manifest_path": str(row_dir / "artifact_manifest.json"),
                "workflow_trace_path": str(row_dir / "workflow_trace.json"),
            }
        )
    if len(rows) != 30:
        raise RuntimeError(f"expected 30 pre-relax CIFs, found {len(rows)}")
    return rows


def inspect_environment(smoke_cif_path: str) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python_executable": sys.executable,
        "install_command_used": "python -m pip install chgnet",
    }
    try:
        import chgnet

        report["chgnet_available"] = True
        report["chgnet_version"] = getattr(chgnet, "__version__", importlib.metadata.version("chgnet"))
        report["torch_version"] = torch.__version__
        report["cuda_available"] = torch.cuda.is_available()
        model = CHGNet.load()
        structure, _ = parse_cif(smoke_cif_path)
        if structure is None:
            raise RuntimeError("smoke CIF did not parse")
        static = model.predict_structure(structure)
        static_status = "ok" if "e" in static and "f" in static else "missing_prediction_fields"
        relaxed = StructOptimizer(model=model).relax(structure, fmax=0.2, steps=2, relax_cell=True, verbose=False)
        relax_status = "ok" if relaxed.get("final_structure") is not None else "missing_final_structure"
        report["smoke_status"] = {"static": static_status, "relax": relax_status}
        report["error_text"] = ""
    except Exception as exc:  # noqa: BLE001
        report["chgnet_available"] = False
        report["chgnet_version"] = ""
        report["torch_version"] = getattr(torch, "__version__", "")
        report["cuda_available"] = torch.cuda.is_available()
        report["smoke_status"] = {"static": "failed", "relax": "failed"}
        report["error_text"] = f"{type(exc).__name__}: {exc}"
    return report


def run_static(pre_manifest: list[dict[str, Any]], *, model: Any, model_version: str) -> list[dict[str, Any]]:
    rows = []
    for row in pre_manifest:
        try:
            structure, parsed = parse_cif(row["packaged_pre_relax_cif_path"])
            if structure is None:
                raise RuntimeError(parsed.error_message or "parse failed")
            prediction = model.predict_structure(structure)
            energy_per_atom = as_float(prediction.get("e"))
            forces = force_stats(prediction.get("f"))
            rows.append(
                {
                    "experiment_id": row["experiment_id"],
                    "row_id": row["row_id"],
                    "formula": row["formula"],
                    "pre_relax_cif_path": row["packaged_pre_relax_cif_path"],
                    "chgnet_static_status": "ok",
                    "energy_per_atom": energy_per_atom,
                    "total_energy": energy_per_atom * len(structure) if energy_per_atom is not None else "",
                    "max_force": forces["max"],
                    "mean_force": forces["mean"],
                    "stress_summary": stress_summary(prediction.get("s")),
                    "model_version": model_version,
                    "error_text": "",
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(static_error_row(row, model_version, f"{type(exc).__name__}: {exc}"))
    return rows


def run_relax(pre_manifest: list[dict[str, Any]], *, model: Any, model_version: str) -> list[dict[str, Any]]:
    rows = []
    relaxer = StructOptimizer(model=model)
    for row in pre_manifest:
        pre_path = Path(row["packaged_pre_relax_cif_path"])
        try:
            structure, parsed = parse_cif(pre_path)
            if structure is None:
                raise RuntimeError(parsed.error_message or "parse failed")
            result = relaxer.relax(structure, verbose=False, **RELAXATION_PARAMETERS)
            relaxed = result.get("final_structure") or result.get("structure")
            if relaxed is None:
                raise RuntimeError("CHGNet relaxation did not return a final structure")
            traj = result.get("trajectory")
            energies = [float(item) for item in getattr(traj, "energies", [])]
            forces = [force_stats(item) for item in getattr(traj, "forces", [])]
            initial_e = per_atom(energies[0], len(structure)) if energies else None
            final_e = per_atom(energies[-1], len(relaxed)) if energies else None
            initial_force = forces[0] if forces else {"max": "", "mean": ""}
            final_force = forces[-1] if forces else {"max": "", "mean": ""}
            filename = f"{safe_name(row['experiment_id'])}__{safe_name(row['row_id'])}__{safe_name(row['formula'])}__chgnet_relaxed.cif"
            skill_relaxed = RELAX_DIR / filename
            sca_relaxed = SCA_RELAX_DIR / filename
            CifWriter(relaxed).write_file(skill_relaxed)
            shutil.copyfile(skill_relaxed, sca_relaxed)
            formula_preserved = same_formula(structure.composition.reduced_formula, relaxed.composition.reduced_formula)
            parse_after, parsed_after = parse_cif(skill_relaxed)
            final_max_force = as_float(final_force["max"])
            rows.append(
                {
                    "experiment_id": row["experiment_id"],
                    "row_id": row["row_id"],
                    "formula": row["formula"],
                    "pre_relax_cif_path": str(pre_path),
                    "relaxed_cif_path": str(skill_relaxed),
                    "relax_status": "ok",
                    "converged": bool(final_max_force is not None and final_max_force <= RELAXATION_PARAMETERS["fmax"]),
                    "steps": max(len(energies) - 1, 0),
                    "initial_energy_per_atom": initial_e,
                    "final_energy_per_atom": final_e,
                    "energy_drop_per_atom": initial_e - final_e if initial_e is not None and final_e is not None else "",
                    "initial_max_force": initial_force["max"],
                    "final_max_force": final_force["max"],
                    "initial_mean_force": initial_force["mean"],
                    "final_mean_force": final_force["mean"],
                    "volume_initial": structure.volume,
                    "volume_final": relaxed.volume,
                    "volume_change_percent": percent_change(relaxed.volume, structure.volume),
                    "formula_preserved": formula_preserved,
                    "parse_ok_after_relax": parse_after is not None and parsed_after.parse_ok,
                    "error_text": "",
                    "model_version": model_version,
                    "relaxation_parameters": json.dumps(RELAXATION_PARAMETERS, sort_keys=True),
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append(relax_error_row(row, model_version, f"{type(exc).__name__}: {exc}"))
    return rows


def validate_relaxed(pre_manifest: list[dict[str, Any]], relax_rows: list[dict[str, Any]], full_sca_rows: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    pre_by_id = {row["row_id"]: row for row in pre_manifest}
    rows = []
    for relax in relax_rows:
        pre = pre_by_id[relax["row_id"]]
        full = full_sca_rows[relax["row_id"]]
        base = {
            "experiment_id": relax["experiment_id"],
            "row_id": relax["row_id"],
            "formula": relax["formula"],
            "pre_relax_cif_path": relax["pre_relax_cif_path"],
            "relaxed_cif_path": relax["relaxed_cif_path"],
            "parse_ok_after_relax": False,
            "formula_preserved_after_relax": False,
            "pre_relax_space_group_number": full.get("detected_space_group_number", ""),
            "post_relax_space_group_number": "",
            "pre_relax_crystal_system": full.get("detected_crystal_system", ""),
            "post_relax_crystal_system": "",
            "pre_relax_symmetry_match": full.get("prototype_symmetry_match", ""),
            "post_relax_symmetry_match": False,
            "prototype_preserved_after_relax": False,
            "crystal_system_preserved_after_relax": False,
            "geometry_contact_pass_after_relax": False,
            "density_after_relax": "",
            "volume_after_relax": "",
            "volume_per_atom_after_relax": "",
            "min_distance_after_relax": "",
            "bad_contact_count_after_relax": "",
        }
        if relax["relax_status"] != "ok" or not relax["relaxed_cif_path"]:
            rows.append(base)
            continue
        structure, parsed = parse_cif(relax["relaxed_cif_path"])
        if structure is None:
            rows.append(base)
            continue
        sg_symbol, sg_number, crystal_system = analyze_symmetry(structure)
        geometry = evaluate_geometry(structure)
        bonds = evaluate_bonds(structure)
        composition = evaluate_composition(structure, pre["formula"])
        target_sg = as_int(full.get("target_space_group_number"))
        post_match = bool(target_sg is not None and sg_number == target_sg)
        crystal_system_preserved = str(crystal_system).lower() == str(full.get("detected_crystal_system", "")).lower()
        base.update(
            {
                "parse_ok_after_relax": bool(parsed.parse_ok),
                "formula_preserved_after_relax": bool(composition.target_formula_match),
                "post_relax_space_group_number": sg_number,
                "post_relax_crystal_system": crystal_system,
                "post_relax_symmetry_match": post_match,
                "prototype_preserved_after_relax": post_match,
                "crystal_system_preserved_after_relax": crystal_system_preserved,
                "geometry_contact_pass_after_relax": bool(geometry.geometry_ok and (bonds.num_bad_contacts or 0) == 0),
                "density_after_relax": geometry.density,
                "volume_after_relax": geometry.volume,
                "volume_per_atom_after_relax": geometry.volume_per_atom,
                "min_distance_after_relax": bonds.min_distance,
                "bad_contact_count_after_relax": bonds.num_bad_contacts,
            }
        )
        rows.append(base)
    return rows


def build_relaxed_manifest(pre_manifest: list[dict[str, Any]], relax_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pre_by_id = {row["row_id"]: row for row in pre_manifest}
    full_sca = {row["row_id"]: row for row in read_csv(SCA_FULL_ROOT / "full_sca_results.csv")}
    rows = []
    for relax in relax_rows:
        if relax["relax_status"] != "ok" or not relax["relaxed_cif_path"]:
            continue
        full = full_sca[relax["row_id"]]
        rows.append(
            {
                "experiment_id": relax["experiment_id"],
                "row_id": relax["row_id"],
                "formula": relax["formula"],
                "pre_relax_cif_path": pre_by_id[relax["row_id"]]["packaged_pre_relax_cif_path"],
                "relaxed_cif_path": relax["relaxed_cif_path"],
                "target_space_group_number": full.get("target_space_group_number", ""),
                "target_crystal_system": full.get("target_crystal_system", ""),
            }
        )
    return rows


def build_comparison(pre_manifest: list[dict[str, Any]], static_rows: list[dict[str, Any]], relax_rows: list[dict[str, Any]], relaxed_sca_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    static_by_id = {row["row_id"]: row for row in static_rows}
    relax_by_id = {row["row_id"]: row for row in relax_rows}
    sca_by_id = {row["row_id"]: row for row in relaxed_sca_rows}
    comparison = []
    for pre in pre_manifest:
        row_id = pre["row_id"]
        static = static_by_id[row_id]
        relax = relax_by_id[row_id]
        sca = sca_by_id[row_id]
        force_reduction = numeric_diff(relax.get("initial_max_force"), relax.get("final_max_force"))
        recommendation = recommendation_for(relax, sca)
        comparison.append(
            {
                "experiment_id": pre["experiment_id"],
                "row_id": row_id,
                "formula": pre["formula"],
                "pre_relax_cif_path": pre["packaged_pre_relax_cif_path"],
                "relaxed_cif_path": relax.get("relaxed_cif_path", ""),
                "chgnet_static_status": static["chgnet_static_status"],
                "relax_status": relax["relax_status"],
                "converged": relax["converged"],
                "initial_energy_per_atom": relax["initial_energy_per_atom"],
                "final_energy_per_atom": relax["final_energy_per_atom"],
                "energy_drop_per_atom": relax["energy_drop_per_atom"],
                "initial_max_force": relax["initial_max_force"],
                "final_max_force": relax["final_max_force"],
                "force_reduction": force_reduction,
                "volume_change_percent": relax["volume_change_percent"],
                "formula_preserved_after_relax": sca["formula_preserved_after_relax"],
                "parse_ok_after_relax": sca["parse_ok_after_relax"],
                "prototype_preserved_after_relax": sca["prototype_preserved_after_relax"],
                "geometry_contact_pass_after_relax": sca["geometry_contact_pass_after_relax"],
                "paper_use_recommendation": recommendation,
            }
        )
    return comparison


def recommendation_for(relax: dict[str, Any], sca: dict[str, Any]) -> str:
    if relax["relax_status"] != "ok":
        return "include_pre_only_relax_failed"
    if not as_bool(sca["parse_ok_after_relax"]) or not as_bool(sca["formula_preserved_after_relax"]):
        return "exclude_from_relaxed_set"
    if not as_bool(sca["prototype_preserved_after_relax"]):
        return "include_pre_only_symmetry_not_preserved"
    if not as_bool(sca["geometry_contact_pass_after_relax"]):
        return "review_needed"
    return "include_pre_and_relaxed"


def summarize_relaxed(relaxed_sca_rows: list[dict[str, Any]], relax_rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(relaxed_sca_rows)
    successful = [row for row in relax_rows if row["relax_status"] == "ok"]
    return {
        "rows": total,
        "relaxation_success_count": len(successful),
        "relaxed_cif_count": sum(bool(row.get("relaxed_cif_path")) for row in relax_rows),
        "formula_preservation_count": sum(as_bool(row["formula_preserved_after_relax"]) for row in relaxed_sca_rows),
        "parse_ok_after_relax_count": sum(as_bool(row["parse_ok_after_relax"]) for row in relaxed_sca_rows),
        "geometry_contact_pass_after_relax_count": sum(as_bool(row["geometry_contact_pass_after_relax"]) for row in relaxed_sca_rows),
        "prototype_preserved_after_relax_count": sum(as_bool(row["prototype_preserved_after_relax"]) for row in relaxed_sca_rows),
        "prototype_not_preserved_rows": [
            row["row_id"] for row in relaxed_sca_rows if not as_bool(row["prototype_preserved_after_relax"])
        ],
        "crystal_system_preserved_after_relax_count": sum(as_bool(row["crystal_system_preserved_after_relax"]) for row in relaxed_sca_rows),
        "relax_status_counts": dict(Counter(row["relax_status"] for row in relax_rows)),
        "median_energy_drop_per_atom": median([as_float(row["energy_drop_per_atom"]) for row in relax_rows]),
        "mean_energy_drop_per_atom": mean([as_float(row["energy_drop_per_atom"]) for row in relax_rows]),
        "median_initial_max_force": median([as_float(row["initial_max_force"]) for row in relax_rows]),
        "median_final_max_force": median([as_float(row["final_max_force"]) for row in relax_rows]),
        "mean_force_reduction": mean([numeric_diff(row.get("initial_max_force"), row.get("final_max_force")) for row in relax_rows]),
    }


def render_pre_report(rows: list[dict[str, Any]]) -> str:
    return (
        "# Pre-Relax CIF Package Report\n\n"
        f"- Packaged pre-relax CIFs: {len(rows)}\n"
        f"- Destination: `{PRE_DIR}`\n"
        f"- Manifest CSV: `{MANIFEST_DIR / 'PRE_RELAX_CIF_MANIFEST.csv'}`\n"
        f"- Direct MP generation lookup count: {sum(as_bool(row['used_direct_mp_generation_lookup']) for row in rows)}\n"
    )


def render_env_report(report: dict[str, Any]) -> str:
    return (
        "# CHGNet Environment Report\n\n"
        f"- Python executable: `{report['python_executable']}`\n"
        f"- Install command used: `{report['install_command_used']}`\n"
        f"- CHGNet available: {report['chgnet_available']}\n"
        f"- CHGNet version: `{report['chgnet_version']}`\n"
        f"- Torch version: `{report['torch_version']}`\n"
        f"- CUDA available: {report['cuda_available']}\n"
        f"- Smoke status: `{report['smoke_status']}`\n"
        f"- Error: `{report['error_text']}`\n"
    )


def render_relaxed_report(summary: dict[str, Any]) -> str:
    return (
        "# Relaxed SCA Report\n\n"
        f"- Rows: {summary['rows']}\n"
        f"- Relaxation success count: {summary['relaxation_success_count']}\n"
        f"- Relaxed CIF count: {summary['relaxed_cif_count']}\n"
        f"- Formula preservation: {summary['formula_preservation_count']}/{summary['rows']}\n"
        f"- Post-relax geometry/contact pass: {summary['geometry_contact_pass_after_relax_count']}/{summary['rows']}\n"
        f"- Post-relax prototype preservation: {summary['prototype_preserved_after_relax_count']}/{summary['rows']}\n"
        f"- Post-relax crystal-system preservation: {summary['crystal_system_preserved_after_relax_count']}/{summary['rows']}\n"
        "\nCHGNet is used here as an MLIP screen; this report does not make a DFT validation claim.\n"
    )


def render_final_package_report(pre_rows: list[dict[str, Any]], relax_rows: list[dict[str, Any]]) -> str:
    return (
        "# Paper Final CIF Package Report\n\n"
        f"- Pre-relax CIF directory: `{PRE_DIR}`\n"
        f"- CHGNet-relaxed CIF directory: `{RELAX_DIR}`\n"
        f"- Pre-relax CIFs packaged: {len(pre_rows)}\n"
        f"- Relaxed CIFs written: {sum(bool(row['relaxed_cif_path']) for row in relax_rows)}\n"
        f"- Manifest directory: `{MANIFEST_DIR}`\n"
        f"- Report directory: `{REPORT_DIR}`\n"
    )


def render_chgnet_report(env_report: dict[str, Any], static_rows: list[dict[str, Any]], relax_rows: list[dict[str, Any]], relaxed_summary: dict[str, Any]) -> str:
    return (
        "# Paper CHGNet Relaxation Report\n\n"
        f"- CHGNet version: `{env_report['chgnet_version']}`\n"
        f"- Torch version: `{env_report['torch_version']}`\n"
        f"- CUDA available: {env_report['cuda_available']}\n"
        f"- Static success count: {sum(row['chgnet_static_status'] == 'ok' for row in static_rows)}/{len(static_rows)}\n"
        f"- Relaxation success count: {relaxed_summary['relaxation_success_count']}/{len(relax_rows)}\n"
        f"- Relaxation parameters: `{RELAXATION_PARAMETERS}`\n"
        f"- Median energy drop per atom: {relaxed_summary['median_energy_drop_per_atom']}\n"
        f"- Mean energy drop per atom: {relaxed_summary['mean_energy_drop_per_atom']}\n"
        f"- Median initial/final max force: {relaxed_summary['median_initial_max_force']} / {relaxed_summary['median_final_max_force']}\n"
        "\nCHGNet is a surrogate MLIP screen only; no DFT validation claim is made.\n"
    )


def render_pre_post_summary(static_rows: list[dict[str, Any]], relax_rows: list[dict[str, Any]], relaxed_summary: dict[str, Any]) -> str:
    non_preserved = relaxed_summary.get("prototype_not_preserved_rows", [])
    non_preserved_text = ", ".join(non_preserved) if non_preserved else "none"
    return (
        "# Paper Pre/Post Relax Summary\n\n"
        f"- Static success count: {sum(row['chgnet_static_status'] == 'ok' for row in static_rows)}/{len(static_rows)}\n"
        f"- Relaxation success count: {relaxed_summary['relaxation_success_count']}/{len(relax_rows)}\n"
        f"- Formula preservation after relaxation: {relaxed_summary['formula_preservation_count']}/{len(relax_rows)}\n"
        f"- Post-relax geometry/contact pass: {relaxed_summary['geometry_contact_pass_after_relax_count']}/{len(relax_rows)}\n"
        f"- Post-relax prototype preservation: {relaxed_summary['prototype_preserved_after_relax_count']}/{len(relax_rows)}\n"
        f"- Prototype not preserved after relaxation: {non_preserved_text}\n"
        f"- Median energy drop per atom: {relaxed_summary['median_energy_drop_per_atom']}\n"
        f"- Mean force reduction: {relaxed_summary['mean_force_reduction']}\n"
    )


def copy_top_level_artifacts(package_report: str, relaxation_report: str, pre_post_summary: str) -> None:
    (SKILL_ARTIFACTS / "PAPER_FINAL_CIF_PACKAGE_REPORT.md").write_text(package_report, encoding="utf-8")
    (SKILL_ARTIFACTS / "PAPER_CHGNET_RELAXATION_REPORT.md").write_text(relaxation_report, encoding="utf-8")
    shutil.copyfile(MANIFEST_DIR / "PRE_POST_RELAX_COMPARISON.csv", SKILL_ARTIFACTS / "PAPER_PRE_POST_RELAX_COMPARISON.csv")
    (SKILL_ARTIFACTS / "PAPER_PRE_POST_RELAX_SUMMARY.md").write_text(pre_post_summary, encoding="utf-8")


def append_final_summary(static_rows: list[dict[str, Any]], relax_rows: list[dict[str, Any]], relaxed_summary: dict[str, Any]) -> None:
    path = SKILL_ARTIFACTS / "PAPER_RESULTS_SUMMARY_TEXT_FINAL.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Paper Results Summary Text Final\n"
    marker = "\n## CHGNet MLIP Screen\n"
    if marker in existing:
        existing = existing.split(marker)[0].rstrip() + "\n"
    existing = existing.replace(
        " CHGNet static and relaxation layers were unavailable in this environment, and no DFT validation claim is made.",
        "",
    )
    non_preserved = relaxed_summary.get("prototype_not_preserved_rows", [])
    non_preserved_sentence = (
        f"The changed prototype row was {', '.join(non_preserved)}. "
        if non_preserved
        else ""
    )
    paragraph = (
        marker
        + "\n"
        + f"CHGNet static predictions succeeded for {sum(row['chgnet_static_status'] == 'ok' for row in static_rows)}/30 pre-relax CIFs, "
        + f"and CHGNet relaxation succeeded for {relaxed_summary['relaxation_success_count']}/30 CIFs. "
        + f"The median energy drop per atom was {relaxed_summary['median_energy_drop_per_atom']}, "
        + f"with median initial/final max force {relaxed_summary['median_initial_max_force']} / {relaxed_summary['median_final_max_force']}. "
        + f"After relaxation, formula preservation was {relaxed_summary['formula_preservation_count']}/30, "
        + f"geometry/contact pass was {relaxed_summary['geometry_contact_pass_after_relax_count']}/30, "
        + f"and prototype preservation was {relaxed_summary['prototype_preserved_after_relax_count']}/30. "
        + non_preserved_sentence
        + "These are CHGNet-relaxed candidate screens only; no DFT validation claim is made.\n"
    )
    path.write_text(existing.rstrip() + "\n" + paragraph, encoding="utf-8")


def analyze_symmetry(structure: Any) -> tuple[str, int | None, str]:
    try:
        analyzer = SpacegroupAnalyzer(structure, symprec=0.01, angle_tolerance=5.0)
        return analyzer.get_space_group_symbol(), analyzer.get_space_group_number(), analyzer.get_crystal_system()
    except Exception:
        return "", None, ""


def static_error_row(row: dict[str, Any], model_version: str, error: str) -> dict[str, Any]:
    return {column: "" for column in STATIC_COLUMNS} | {
        "experiment_id": row["experiment_id"],
        "row_id": row["row_id"],
        "formula": row["formula"],
        "pre_relax_cif_path": row["packaged_pre_relax_cif_path"],
        "chgnet_static_status": "failed",
        "model_version": model_version,
        "error_text": error,
    }


def relax_error_row(row: dict[str, Any], model_version: str, error: str) -> dict[str, Any]:
    return {column: "" for column in RELAX_COLUMNS} | {
        "experiment_id": row["experiment_id"],
        "row_id": row["row_id"],
        "formula": row["formula"],
        "pre_relax_cif_path": row["packaged_pre_relax_cif_path"],
        "relax_status": "failed",
        "converged": False,
        "error_text": error,
        "model_version": model_version,
        "relaxation_parameters": json.dumps(RELAXATION_PARAMETERS, sort_keys=True),
    }


def force_stats(forces: Any) -> dict[str, float | str]:
    if forces is None:
        return {"max": "", "mean": ""}
    if hasattr(forces, "detach"):
        forces = forces.detach()
    if hasattr(forces, "cpu"):
        forces = forces.cpu()
    if hasattr(forces, "tolist"):
        forces = forces.tolist()
    norms = []
    for row in forces:
        if hasattr(row, "tolist"):
            row = row.tolist()
        try:
            values = [float(item) for item in row]
        except TypeError:
            continue
        norms.append(math.sqrt(sum(item * item for item in values)))
    return {"max": max(norms) if norms else "", "mean": sum(norms) / len(norms) if norms else ""}


def stress_summary(stress: Any) -> str:
    if stress is None:
        return ""
    if hasattr(stress, "tolist"):
        stress = stress.tolist()
    try:
        values = [float(item) for item in stress]
    except TypeError:
        return ""
    return json.dumps({"min": min(values), "max": max(values), "mean_abs": sum(abs(item) for item in values) / len(values)})


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("._") or "value"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if hasattr(value, "item"):
        value = value.item()
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(str(value)))
    except ValueError:
        return None


def per_atom(total_energy: float, nsites: int) -> float | None:
    return total_energy / nsites if nsites else None


def percent_change(final: float, initial: float) -> float | None:
    return ((final - initial) / initial) * 100 if initial else None


def same_formula(left: str, right: str) -> bool:
    try:
        return CompositionLike(left) == CompositionLike(right)
    except Exception:
        return str(left).replace(" ", "") == str(right).replace(" ", "")


def CompositionLike(value: str) -> str:
    from pymatgen.core import Composition

    return Composition(value).reduced_formula


def numeric_diff(left: Any, right: Any) -> float | str:
    lval = as_float(left)
    rval = as_float(right)
    return lval - rval if lval is not None and rval is not None else ""


def mean(values: list[float | None | str]) -> float | None:
    clean = [float(value) for value in values if value not in (None, "")]
    return sum(clean) / len(clean) if clean else None


def median(values: list[float | None | str]) -> float | None:
    clean = sorted(float(value) for value in values if value not in (None, ""))
    if not clean:
        return None
    mid = len(clean) // 2
    return clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2


if __name__ == "__main__":
    raise SystemExit(main())
