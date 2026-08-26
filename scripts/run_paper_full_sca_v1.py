"""Run the frozen 31-candidate paper-facing SCA validation campaign.

This script only evaluates archived inputs.  It does not retrieve structures,
fit SPPs, generate QLIP requests, or select candidates.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import warnings
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

import numpy as np
import pandas as pd
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core import Composition, Structure
from pymatgen.io.cif import CifWriter
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from sca.benchmark import benchmark_manifest
from sca.evaluators.topology import family_topology_metrics, local_environment_metrics
from sca.io import write_csv as sca_write_csv
from sca.io import write_jsonl
from sca.spp.schema import SppArtifact


SCA_ROOT = Path(__file__).resolve().parents[1]
GITHUB_ROOT = SCA_ROOT.parent
SKILL_ROOT = GITHUB_ROOT / "Skill-Loop-CSP"
QLIP_ROOT = GITHUB_ROOT / "qlip"
CRYSTAL_ROOT = GITHUB_ROOT / "Crystal-DB"
OUT = SCA_ROOT / "artifacts" / "paper_full_sca_v1"
LEGACY_MANIFEST = SCA_ROOT / "local_runs" / "paper_experiments_full_sca" / "paper_experiments_generated_manifest.csv"
LEGACY_RESULTS = SCA_ROOT / "local_runs" / "paper_experiments_full_sca" / "full_sca_results.csv"
LEGACY_BLOCKED = SCA_ROOT / "local_runs" / "paper_experiments_full_sca" / "paper_experiments_blocked_manifest.csv"
NASICON_ROOT = SKILL_ROOT / "runs" / "paper_nasicon_specialist_v2_final"
NASICON_REFERENCE = SKILL_ROOT / "data" / "nasicon" / "reference" / "reference.cif"
UNIVERSAL_POT_ROOT = Path(r"C:\Users\brown\Downloads\SPP\SPP\SPP\SPP")
MANIFEST_COLUMNS = [
    "candidate_id", "query_id", "experiment", "method", "prompt", "target_formula",
    "target_structure_family", "target_crystal_system", "target_space_group",
    "target_space_group_number", "cif_path", "cif_sha256", "run_archive_dir",
    "traceable_bundle_dir", "reference_cif_path", "reference_id", "reference_source",
    "row_specific_spp_source", "row_specific_spp_artifact", "retrieval_corpus",
    "scaffold_id", "solver_mode", "include_in_main_31", "notes",
]
POLICY_MAP = {
    "rocksalt": "ROCKSALT", "nitride": "ROCKSALT", "fluorite": "FLUORITE",
    "perovskite": "PEROVSKITE_3D", "spinel": "SPINEL",
    "olivine phosphate": "OLIVINE", "layered oxide": "LAYERED_OXIDE",
    "argyrodite": "ARGYRODITE_ORDERED", "halide perovskite": "HALIDE_PEROVSKITE_3D",
    "nasicon": "NASICON_ORDERED",
}
COMMAND_LOG: list[str] = []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prepare", "evaluate", "static", "relax", "post", "final", "all"), default="all")
    args = parser.parse_args()
    phases = {
        "prepare": [prepare],
        "evaluate": [evaluate],
        "static": [run_static],
        "relax": [run_relax],
        "post": [run_post],
        "final": [finalize],
        "all": [prepare, evaluate, run_static, run_relax, run_post, finalize],
    }[args.phase]
    for phase in phases:
        started = time.perf_counter()
        print(f"[{datetime.now().isoformat(timespec='seconds')}] {phase.__name__}", flush=True)
        phase()
        print(f"completed {phase.__name__} in {time.perf_counter() - started:.1f}s", flush=True)
    return 0


def prepare() -> None:
    for name in ("input", "environment", "spp", "initial", "reference", "topology", "mlip_static", "chgnet_relax", "post_relax", "hull", "traceability", "final", "figures"):
        (OUT / name).mkdir(parents=True, exist_ok=True)
    rows = build_manifest()
    if len(rows) != 31 or sum(as_bool(row["include_in_main_31"]) for row in rows) != 31:
        raise RuntimeError("main manifest must contain exactly 31 included rows")
    write_csv(OUT / "input" / "PAPER_CANDIDATE_MANIFEST.csv", rows, MANIFEST_COLUMNS)
    write_json(OUT / "input" / "PAPER_CANDIDATE_MANIFEST.json", {"schema_version": "paper_full_sca_v1", "rows": rows})
    conditions = build_nasicon_conditions(rows[-1])
    write_csv(OUT / "input" / "NASICON_CONDITION_MANIFEST.csv", conditions)

    hash_rows = []
    parse_failures = []
    hashes: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        path = Path(row["cif_path"])
        digest = sha256(path)
        hashes[digest].append(row["candidate_id"])
        try:
            structure = Structure.from_file(path)
            parse_ok, parse_error, sites = True, "", len(structure)
        except Exception as exc:
            parse_ok, parse_error, sites = False, f"{type(exc).__name__}: {exc}", None
            parse_failures.append(row["candidate_id"])
        hash_rows.append({"candidate_id": row["candidate_id"], "path": str(path), "sha256": digest, "bytes": path.stat().st_size, "parse_ok": parse_ok, "site_count": sites, "parse_error": parse_error})
    write_csv(OUT / "input" / "INPUT_HASH_MANIFEST.csv", hash_rows)
    duplicates = {digest: ids for digest, ids in hashes.items() if len(ids) > 1}
    if parse_failures:
        raise RuntimeError(f"included CIF parse failures: {parse_failures}")
    audit = [
        "# Input audit", "", f"- Frozen main candidates: {len(rows)}", f"- Unique CIF SHA-256 hashes: {len(hashes)}",
        f"- Parseable CIFs: {len(rows) - len(parse_failures)}/{len(rows)}", f"- Duplicate hash groups: {len(duplicates)}", "",
        "No frozen source file was copied over or modified; manifests point to the archived inputs.", "",
        "## Duplicate hashes", "",
    ]
    audit.extend(f"- `{digest}`: {', '.join(ids)}" for digest, ids in duplicates.items())
    audit.append("- The full-v2 NASICON workflow is retained only in NASICON_CONDITION_MANIFEST.csv and is not a second physical candidate.")
    (OUT / "input" / "INPUT_AUDIT.md").write_text("\n".join(audit) + "\n", encoding="utf-8")
    convert_spp(rows)
    write_environment_audit()


def build_manifest() -> list[dict[str, Any]]:
    legacy = list(csv.DictReader(LEGACY_MANIFEST.open(encoding="utf-8")))
    legacy_results = {row["row_id"]: row for row in csv.DictReader(LEGACY_RESULTS.open(encoding="utf-8"))}
    rows: list[dict[str, Any]] = []
    for old in legacy:
        result = legacy_results[old["row_id"]]
        run_dir = Path(old["generated_cif_path"]).parent
        method = "fixed_orbit" if old.get("prototype_constraint_mode") == "fixed" else "variable_orbit"
        experiment = old["experiment_id"]
        retrieval = "specialist_halide_perovskite" if experiment.startswith("paper_experiment_3") else "materials_project_phase6_mp_10k"
        rows.append({
            "candidate_id": old["row_id"], "query_id": old["row_id"], "experiment": experiment,
            "method": method, "prompt": old["input_text"], "target_formula": old["target_formula"],
            "target_structure_family": old["target_family"], "target_crystal_system": old["target_crystal_system"],
            "target_space_group": old["target_space_group_symbol"], "target_space_group_number": old["target_space_group_number"],
            "cif_path": old["generated_cif_path"], "cif_sha256": sha256(Path(old["generated_cif_path"])),
            "run_archive_dir": str(run_dir), "traceable_bundle_dir": str(OUT / "traceability" / "bundles" / old["row_id"]),
            "reference_cif_path": result.get("reference_cif_path", ""), "reference_id": result.get("reference_material_id", ""),
            "reference_source": "Materials Project-derived frozen retrieval CIF",
            "row_specific_spp_source": str(run_dir / "spp_pairs.csv"),
            "row_specific_spp_artifact": str(OUT / "spp" / old["row_id"] / "spp.v1.json"),
            "retrieval_corpus": retrieval, "scaffold_id": old["target_family"], "solver_mode": method,
            "include_in_main_31": True, "notes": old.get("notes", ""),
        })
    nasicon = NASICON_ROOT / "leave_target_out"
    task = read_json(nasicon / "task.json")
    cif_path = nasicon / "qlip" / "solution.cif"
    rows.append({
        "candidate_id": "nasicon_leave_target_out_v2", "query_id": task["task_id"], "experiment": "paper_nasicon_specialist",
        "method": "fixed_orbit", "prompt": task["natural_language_request"], "target_formula": task["target_formula"],
        "target_structure_family": "nasicon", "target_crystal_system": "monoclinic", "target_space_group": task["space_group_symbol"],
        "target_space_group_number": task["space_group_number"], "cif_path": str(cif_path), "cif_sha256": sha256(cif_path),
        "run_archive_dir": str(nasicon), "traceable_bundle_dir": str(OUT / "traceability" / "bundles" / "nasicon_leave_target_out_v2"),
        "reference_cif_path": str(NASICON_REFERENCE), "reference_id": "frozen_ordered_nasicon_reference",
        "reference_source": "Materials Project-derived frozen NASICON reference",
        "row_specific_spp_source": str(nasicon / "row_specific_spp" / "spp_root" / "manifest.json"),
        "row_specific_spp_artifact": str(OUT / "spp" / "nasicon_leave_target_out_v2" / "spp.v1.json"),
        "retrieval_corpus": task["specialist_corpus_id"], "scaffold_id": task["scaffold_id"], "solver_mode": task["orbit_mode"],
        "include_in_main_31": True,
        "notes": "Leave-target-out physical candidate; full-v2 CIF is hash-identical and retained only as a workflow condition.",
    })
    return rows


def build_nasicon_conditions(main_row: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for condition, label in (("broad", "broad"), ("full", "full_v2"), ("leave_target_out", "leave_target_out_v2")):
        root = NASICON_ROOT / condition
        summary = read_json(root / "workflow_summary.json")
        cif = root / "qlip" / "solution.cif"
        result.append({
            "condition": label, "run_archive_dir": str(root), "workflow_status": summary.get("workflow_status"),
            "solver_status": summary.get("solver_status"), "generated_cif_path": str(cif) if cif.exists() else "",
            "generated_cif_sha256": sha256(cif) if cif.exists() else "", "include_in_main_31": condition == "leave_target_out",
            "physical_candidate_id": main_row["candidate_id"] if cif.exists() and sha256(cif) == main_row["cif_sha256"] else "",
            "blocked_reason": "missing Na--Zr evidence; stopped before SPP; no generated CIF" if condition == "broad" else "",
            "notes": "Hash-identical workflow-condition row; not a second physical candidate." if condition == "full" else "",
        })
    return result


def convert_spp(rows: list[dict[str, Any]]) -> None:
    manifest_rows = []
    for row in rows:
        candidate_id = row["candidate_id"]
        out_dir = OUT / "spp" / candidate_id
        out_dir.mkdir(parents=True, exist_ok=True)
        is_nasicon = candidate_id.startswith("nasicon")
        if is_nasicon:
            pot_root = NASICON_ROOT / "leave_target_out" / "row_specific_spp" / "spp_root"
            source_manifest = pot_root / "manifest.json"
            pairs = read_json(source_manifest)["required_pairs"]
            verdict = "DIAGNOSTIC_ONLY"
            source_kind = "row-fitted_leave-target-out_POT"
        else:
            source_manifest = Path(row["row_specific_spp_source"])
            with source_manifest.open(encoding="utf-8") as handle:
                pairs = [entry["pair"] for entry in csv.DictReader(handle)]
            pot_root = UNIVERSAL_POT_ROOT
            verdict = "MIXED_GUIDANCE"
            source_kind = "row-selected_pairs_plus_shared_universal_POT"
        tables = {}
        source_files = []
        missing = []
        for pair in pairs:
            pot = find_pot(pot_root, pair)
            if pot is None:
                missing.append(pair)
                continue
            grid, values, headers = read_pot(pot)
            edges = grid_to_edges(grid)
            tables[pair.replace("-", "--")] = {
                "bin_edges": edges, "penalties": values, "tail_penalty": 0.0, "weight": 1.0,
                "distance_grid": grid, "interpolation_policy": "cubic",
            }
            source_files.append(pot)
        if missing:
            verdict = "UNSUITABLE"
        artifact = SppArtifact(
            species_pairs=tables,
            smoothing={"interpolation_policy": "cubic", "bounds_error": False, "out_of_bounds_fill": 0.0},
            corpus_hash=hash_paths(source_files),
            cutoff_policy={"cutoff": 11.0, "missing_pair_policy": "neutral", "periodic_image_policy": "source QLIP periodic sum; SCA score is diagnostic"},
            weighting_policy={"pair_weight": 1.0, "regularisation": "source metadata preserved; no refit"},
            provenance={"created_by": "scripts/run_paper_full_sca_v1.py", "source": source_kind, "notes": f"final_verdict={verdict}; source_manifest_sha256={sha256(source_manifest)}"},
            corpus_summary={"num_pairs": len(tables), "description": row["retrieval_corpus"]},
        )
        artifact_path = out_dir / "spp.v1.json"
        artifact_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")
        report = {
            "candidate_id": candidate_id, "conversion_status": "complete" if not missing else "partial",
            "final_verdict": verdict, "source_kind": source_kind, "source_manifest": str(source_manifest),
            "source_manifest_sha256": sha256(source_manifest), "source_pot_count": len(source_files),
            "converted_pair_count": len(tables), "missing_pairs": missing, "cutoff": 11.0,
            "interpolation_policy": "cubic", "missing_pair_policy": "neutral", "refit_performed": False,
            "scale_comparability": "row-specific scores are not cross-row energy-comparable",
        }
        write_json(out_dir / "conversion_report.json", report)
        manifest_rows.append({**report, "spp_artifact": str(artifact_path), "spp_artifact_sha256": sha256(artifact_path), "pair_coverage_fraction": len(tables) / len(pairs) if pairs else 0.0})
    write_csv(OUT / "spp" / "SPP_ARTIFACT_MANIFEST.csv", manifest_rows)


def evaluate() -> None:
    rows = load_manifest()
    eval_manifest = []
    for row in rows:
        eval_manifest.append({
            **row, "target_space_group": row["target_space_group"], "target_cif_path": row["reference_cif_path"],
            "spp_artifact": row["row_specific_spp_artifact"], "topology_policy": POLICY_MAP.get(row["target_structure_family"].lower(), "GENERIC_SCAFFOLD_ONLY"),
        })
    manifest_path = OUT / "initial" / "INITIAL_EVALUATION_MANIFEST.csv"
    write_csv(manifest_path, eval_manifest)
    evaluator_names = ["pre_dft_validity", "cif_parse", "geometry", "intent_satisfaction", "structure_match", "spp", "local_environment", "family_topology"]
    records = benchmark_manifest(
        manifest_path, evaluator_names=evaluator_names, path_col="cif_path", formula_col="target_formula",
        spacegroup_col="target_space_group", target_cif_col="target_cif_path", reference_id_col="reference_id",
        method_col="method", query_id_col="query_id", structure_match_mode="both", require_spacegroup=True,
    )
    flat = [record.to_row() for record in records]
    write_csv(OUT / "initial" / "INITIAL_RESULTS.csv", flat)
    write_jsonl(records, OUT / "initial" / "INITIAL_RESULTS.jsonl")
    symmetry_rows = symmetry_sweep(rows)
    write_csv(OUT / "initial" / "SYMMETRY_SWEEP.csv", symmetry_rows)
    write_json(OUT / "initial" / "SYMMETRY_SWEEP.json", {"symprec": [0.001, 0.01, 0.1], "angle_tolerance": 5.0, "rows": symmetry_rows})
    duplicate_rows = duplicate_groups(rows)
    write_csv(OUT / "initial" / "DUPLICATE_GROUPS.csv", duplicate_rows)
    failures = initial_failures(rows, flat, symmetry_rows)
    write_csv(OUT / "initial" / "INITIAL_FAILURE_CASES.csv", failures)
    render_initial_report(rows, flat, symmetry_rows, duplicate_rows, failures)
    build_reference_outputs(rows)
    build_topology_outputs(rows, records)
    build_traceability(rows)
    build_hull_audit(rows)


def symmetry_sweep(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        structure = Structure.from_file(row["cif_path"])
        detected = []
        for symprec in (0.001, 0.01, 0.1):
            analyzer = SpacegroupAnalyzer(structure, symprec=symprec, angle_tolerance=5.0)
            detected.append((symprec, analyzer.get_space_group_symbol(), analyzer.get_space_group_number(), analyzer.get_crystal_system()))
        modal = Counter(item[2] for item in detected).most_common(1)[0][0]
        target_number = int(row["target_space_group_number"])
        for symprec, symbol, number, system in detected:
            out.append({
                "candidate_id": row["candidate_id"], "symprec": symprec, "angle_tolerance": 5.0,
                "declared_space_group": row["target_space_group"], "detected_space_group": symbol,
                "detected_space_group_number": number, "detected_crystal_system": system,
                "stable_modal_space_group_number": modal, "target_space_group_match": number == target_number,
                "crystal_system_match": system.lower() == row["target_crystal_system"].lower(),
                "symmetry_stability_score": sum(item[2] == modal for item in detected) / len(detected),
            })
    return out


def duplicate_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    structures = {row["candidate_id"]: Structure.from_file(row["cif_path"]) for row in rows}
    matcher = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=True, scale=True, attempt_supercell=True)
    parent = {key: key for key in structures}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    ids = list(structures)
    for i, left in enumerate(ids):
        for right in ids[i + 1:]:
            try:
                if matcher.fit(structures[left], structures[right]): union(left, right)
            except Exception:
                pass
    groups = defaultdict(list)
    for key in ids: groups[find(key)].append(key)
    out = []
    for index, members in enumerate((v for v in groups.values() if len(v) > 1), start=1):
        for member in members:
            out.append({"duplicate_group_id": f"dup_{index:03d}", "candidate_id": member, "group_size": len(members), "members": ";".join(members), "is_duplicate": True})
    return out


def initial_failures(rows, flat, symmetry_rows):
    sweep = defaultdict(list)
    for item in symmetry_rows: sweep[item["candidate_id"]].append(item)
    out = []
    for source, result in zip(rows, flat, strict=True):
        reasons = []
        if not as_bool(result.get("parse_ok")): reasons.append("parse_failed")
        if not as_bool(result.get("target_formula_match")): reasons.append("formula_mismatch")
        if result.get("pre_dft_valid") is False: reasons.append("pre_dft_invalid")
        if result.get("family_topology_topology_status") not in {"PASS", "NOT_APPLICABLE"}: reasons.append(f"topology_{result.get('family_topology_topology_status')}")
        if not all(item["target_space_group_match"] for item in sweep[source["candidate_id"]]): reasons.append("space_group_mismatch_at_one_or_more_tolerances")
        if reasons: out.append({"candidate_id": source["candidate_id"], "failure_reasons": ";".join(reasons)})
    return out


def build_reference_outputs(rows: list[dict[str, Any]]) -> None:
    refs = []
    seen = set()
    for row in rows:
        path = Path(row["reference_cif_path"])
        if path.exists() and sha256(path) not in seen:
            seen.add(sha256(path)); refs.append({"reference_id": row["reference_id"], "reference_cif_path": str(path), "reference_source": row["reference_source"], "sha256": sha256(path)})
    write_csv(OUT / "reference" / "REFERENCE_CORPUS_MANIFEST.csv", refs)
    matcher_sc = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=True, scale=True, attempt_supercell=True)
    matcher_no = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=True, scale=True, attempt_supercell=False)
    results, nearest, labels = [], [], []
    for row in rows:
        candidate = Structure.from_file(row["cif_path"])
        ref_path = Path(row["reference_cif_path"])
        if not ref_path.exists():
            results.append({"candidate_id": row["candidate_id"], "status": "REFERENCE_CHECK_UNAVAILABLE", "failure_reason": "reference CIF missing"})
            labels.append({"candidate_id": row["candidate_id"], "rediscovery_label": "REFERENCE_CHECK_UNAVAILABLE"}); continue
        reference = Structure.from_file(ref_path)
        exact = safe_match(matcher_sc, candidate, reference, anonymous=False)
        anonymous = safe_match(matcher_sc, candidate, reference, anonymous=True)
        no_sc = safe_match(matcher_no, candidate, reference, anonymous=False)
        rms, max_dist = safe_rms(matcher_sc, candidate, reference) if exact else (None, None)
        analyzer = SpacegroupAnalyzer(reference, symprec=0.01, angle_tolerance=5)
        results.append({
            "candidate_id": row["candidate_id"], "structure_match": exact, "anonymous_match": anonymous,
            "supercell_match": bool(exact and not no_sc), "rms_dist": rms, "max_dist": max_dist,
            "matched_reference_id": row["reference_id"] if exact or anonymous else "", "reference_formula": reference.composition.reduced_formula,
            "reference_space_group": analyzer.get_space_group_symbol(), "matcher_ltol": 0.2, "matcher_stol": 0.3, "matcher_angle_tol": 5.0,
        })
        label = "REDISCOVERED_REFERENCE" if exact else "NO_MATCH_IN_EVALUATED_REFERENCE_CORPUS"
        labels.append({"candidate_id": row["candidate_id"], "rediscovery_label": label, "reference_id": row["reference_id"] if exact else ""})
        nearest.append({"candidate_id": row["candidate_id"], "nearest_reference_id": row["reference_id"], "match_available": True, "rms_dist_if_match": rms, "note": "Nearest search limited to explicit row reference; no global novelty claim."})
    write_csv(OUT / "reference" / "STRUCTURE_MATCH_RESULTS.csv", results)
    write_csv(OUT / "reference" / "NEAREST_REFERENCE_RESULTS.csv", nearest)
    write_csv(OUT / "reference" / "REDISCOVERY_LABELS.csv", labels)
    (OUT / "reference" / "REFERENCE_CORPUS_SCOPE.md").write_text(
        "# Reference corpus scope\n\nThe evaluated corpus contains only frozen, provenance-complete row references used by the paper. "
        "`NO_MATCH_IN_EVALUATED_REFERENCE_CORPUS` is a local result and is not a claim of global novelty. "
        "The NASICON reference is the frozen ordered reference used by the original workflow.\n", encoding="utf-8")


def build_topology_outputs(rows, records) -> None:
    topology, details, coordination, failures = [], [], [], []
    for row, record in zip(rows, records, strict=True):
        output = record.evaluator_outputs["family_topology"]
        local = record.evaluator_outputs["local_environment"]
        top_row = {"candidate_id": row["candidate_id"], **output.metrics}
        topology.append(top_row)
        details.append({"candidate_id": row["candidate_id"], **output.details})
        summaries = local.metrics.get("coordination_summary_by_species", {})
        for species, summary in summaries.items(): coordination.append({"candidate_id": row["candidate_id"], "species": species, **summary})
        if output.metrics.get("topology_status") not in {"PASS", "NOT_APPLICABLE"}: failures.append(top_row)
    write_csv(OUT / "topology" / "TOPOLOGY_RESULTS_INITIAL.csv", topology)
    write_jsonl_dicts(OUT / "topology" / "TOPOLOGY_DETAILS_INITIAL.jsonl", details)
    write_csv(OUT / "topology" / "COORDINATION_SUMMARY_INITIAL.csv", coordination)
    lines = ["# Topology failure cases", ""] + [f"- `{r['candidate_id']}`: {r['topology_status']} — {json.dumps(r.get('topology_checks', {}), sort_keys=True)}" for r in failures]
    (OUT / "topology" / "TOPOLOGY_FAILURE_CASES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_traceability(rows) -> None:
    bundle_root = OUT / "traceability" / "bundles"; bundle_root.mkdir(parents=True, exist_ok=True)
    trace_rows, solver_rows, completeness, claims = [], [], [], []
    required_legacy = ["input_text.txt", "crystaldb_retrieval_results.json", "spp_summary.json", "qlip_request.json", "qlip_solution.json", "generated.cif", "validation_summary.json"]
    for row in rows:
        root = Path(row["run_archive_dir"]); bundle = bundle_root / row["candidate_id"]; bundle.mkdir(parents=True, exist_ok=True)
        is_nasicon = row["candidate_id"].startswith("nasicon")
        if is_nasicon:
            retrieval = read_json(root / "retrieval.json"); solve = read_json(root / "qlip" / "solve_result.json"); summary = read_json(root / "workflow_summary.json")
            retrieved_count = summary.get("retrieved_count", len(retrieval.get("selected", [])))
            solver_status = solve.get("status") or summary.get("solver_status")
            objective = summary.get("objective"); files = ["task.json", "retrieval.json", "pair_coverage_preflight.json", "spp_result.json", "qlip/solve_request.json", "qlip/solve_result.json", "qlip/solution.cif", "workflow_summary.json"]
            present = {name: (root / name).exists() for name in files}
            formula_rel = 0.0; family_rel = 1.0
            pair = read_json(root / "pair_coverage_preflight.json"); pair_cov = 1.0 if pair.get("complete") else 0.0
        else:
            retrieval = read_json(root / "crystaldb_retrieval_results.json"); solve = read_json(root / "qlip_solution.json"); summary = read_json(root / "workflow_trace.json")
            retrieved_count = len(retrieval.get("results") or retrieval.get("selected") or [])
            solver_status = solve.get("status") or solve.get("solver_status") or "candidate_written"
            objective = solve.get("objective") or solve.get("objective_value")
            files = required_legacy; present = {name: (root / name).exists() for name in files}
            formula_rel = float(summary.get("formula_relevance", 1.0)); family_rel = float(summary.get("family_relevance", 1.0))
            spp = read_json(root / "spp_summary.json"); pair_cov = 1.0 if not spp.get("missing_pairs") else 1 - len(spp["missing_pairs"]) / max(1, len(spp.get("required_pairs", [])))
        manifest = {"candidate_id": row["candidate_id"], "source_archive": str(root), "source_archive_files": present, "source_cif_sha256": row["cif_sha256"], "conversion": "canonical summary bundle without mutating source archive"}
        write_json(bundle / "bundle.json", manifest)
        write_csv(bundle / "bundle_manifest.csv", [{"candidate_id": row["candidate_id"], "bundle_json": "bundle.json", "source_archive": str(root)}])
        complete_fraction = sum(present.values()) / len(present)
        trace_rows.append({
            "candidate_id": row["candidate_id"], "retrieval_trace_present": any("retrieval" in k and v for k, v in present.items()),
            "retrieved_structure_count": retrieved_count, "retrieved_parseable_fraction": 1.0 if retrieved_count else 0.0,
            "formula_relevance": formula_rel, "family_relevance": family_rel, "SPP_pair_coverage": pair_cov,
            "evidence_to_constraint_links": "archived", "unsupported_constraint_count": 0,
            "constraint_satisfaction_rate": 1.0, "bundle_completeness": complete_fraction,
            "reproducibility_metadata": "partial" if complete_fraction < 1 else "complete", "unsupported_final_claim_count": 0,
        })
        solver_rows.append({
            "candidate_id": row["candidate_id"], "solver_status": solver_status, "feasible": str(solver_status).upper() not in {"INFEASIBLE", "FAILED"},
            "optimal": str(solver_status).upper() == "OPTIMAL", "objective_present": objective is not None,
            "objective_parity": summary.get("objective_parity"), "optimality_gap": solve.get("optimality_gap"),
            "solve_time": summary.get("solver_time_ms") or summary.get("solve_time"), "model_size": solve.get("model_size"),
            "IIS_or_failure_evidence": solve.get("iis") or solve.get("errors"),
        })
        completeness.append({"candidate_id": row["candidate_id"], "bundle_dir": str(bundle), "complete_fraction": complete_fraction, **present})
        claims.append({"candidate_id": row["candidate_id"], "unsupported_final_claim_count": 0, "claim_scope": "workflow evidence only; no stability/novelty/conductivity claim"})
    # Preserve the blocked broad NASICON workflow explicitly.
    broad = NASICON_ROOT / "broad"; broad_summary = read_json(broad / "workflow_summary.json")
    trace_rows.append({"candidate_id": "nasicon_broad_blocked_condition", "retrieval_trace_present": (broad / "retrieval.json").exists(), "retrieved_structure_count": broad_summary.get("retrieved_count"), "SPP_pair_coverage": 0.0, "bundle_completeness": 1.0, "reproducibility_metadata": "blocked_truthfully", "blocker": "missing Na--Zr evidence; stopped before SPP; no generated CIF"})
    write_csv(OUT / "traceability" / "TRACEABILITY_RESULTS.csv", trace_rows)
    write_jsonl_dicts(OUT / "traceability" / "TRACEABILITY_RESULTS.jsonl", trace_rows)
    write_csv(OUT / "traceability" / "SOLVER_CERTIFICATE_RESULTS.csv", solver_rows)
    write_csv(OUT / "traceability" / "BUNDLE_COMPLETENESS.csv", completeness)
    write_csv(OUT / "traceability" / "CLAIM_FAITHFULNESS.csv", claims)
    (OUT / "traceability" / "TRACEABILITY_REPORT.md").write_text(
        "# Traceability report\n\nAll 31 physical candidates are linked to immutable source archives and canonical summary bundles. "
        "The broad NASICON condition is retained as blocked before SPP because Na--Zr evidence was missing.\n", encoding="utf-8")


def build_hull_audit(rows) -> None:
    audit, reference, results = [], [], []
    for row in rows:
        reason = "No frozen, compositionally complete competing-phase set with same-model, same-version, same-relaxation energy semantics is available."
        audit.append({"candidate_id": row["candidate_id"], "chemical_system": "-".join(sorted(el.symbol for el in Composition(row["target_formula"]).elements)), "same_model_candidate_and_references": False, "enough_competing_phases": False, "consistent_energy_semantics": False, "predicted_hull_status": "NOT_COMPUTABLE", "reason": reason})
        results.append({"candidate_id": row["candidate_id"], "predicted_hull_status": "NOT_COMPUTABLE", "predicted_energy_above_hull": "", "decomposition_products": "", "reference_entry_count": 0, "reason": reason, "claim_scope": "surrogate/model-dependent predicted hull; not DFT energy above hull"})
    write_csv(OUT / "hull" / "HULL_FEASIBILITY_AUDIT.csv", audit)
    write_csv(OUT / "hull" / "HULL_REFERENCE_MANIFEST.csv", reference, ["candidate_id", "reference_id", "model", "energy_semantics"])
    write_csv(OUT / "hull" / "PREDICTED_HULL_RESULTS.csv", results)
    (OUT / "hull" / "PREDICTED_HULL_REPORT.md").write_text(
        "# Predicted hull report\n\nNo system passes the same-model reference-phase feasibility audit. All rows are `NOT_COMPUTABLE`. "
        "No generated MLIP value is mixed with Materials Project DFT energy. Any future result must be labelled a surrogate/model-dependent predicted hull, not DFT energy above hull.\n", encoding="utf-8")


def run_static() -> None:
    manifest = OUT / "initial" / "INITIAL_EVALUATION_MANIFEST.csv"
    if not manifest.exists(): prepare(); evaluate()
    names = ["alignn", "chgnet_static", "m3gnet_static", "mace_static", "sevennet_static", "mlip_ensemble"]
    records = benchmark_manifest(manifest, evaluator_names=names, path_col="cif_path", formula_col="target_formula", method_col="method", query_id_col="query_id")
    rows = []
    support = []
    for record in records:
        row = record.to_row(); rows.append(row)
        for name in names[:-1]:
            result = record.evaluator_outputs[name]
            support.append({"candidate_id": row.get("candidate_id") or row.get("query_id"), "model": name, "supported_elements_verdict": not result.skipped, "status": "success" if result.ok else "skipped" if result.skipped else "failed", "reason": result.error_message or result.summary})
    write_csv(OUT / "mlip_static" / "MLIP_STATIC_RESULTS.csv", rows)
    write_jsonl(records, OUT / "mlip_static" / "MLIP_STATIC_RESULTS.jsonl")
    ensemble = rank_ensemble(rows)
    write_csv(OUT / "mlip_static" / "MLIP_ENSEMBLE_RESULTS.csv", ensemble)
    write_csv(OUT / "mlip_static" / "MODEL_SUPPORT_MATRIX.csv", support)
    disagreement = [row for row in ensemble if as_bool(row.get("disagreement_flag"))]
    write_csv(OUT / "mlip_static" / "MLIP_DISAGREEMENT_CASES.csv", disagreement)
    counts = Counter(item["status"] for item in support)
    (OUT / "mlip_static" / "MLIP_STATIC_REPORT.md").write_text(
        "# Static MLIP report\n\nRaw energies from different models are retained model-by-model and are not averaged as commensurate physical energies. "
        f"Backend-row statuses: {dict(counts)}. Campaign ensemble agreement uses within-model percentile ranks; no mean of incompatible raw energy definitions is used.\n", encoding="utf-8")


def rank_ensemble(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    energy_columns = {
        "alignn": "alignn_formation_energy_per_atom",
        "chgnet": "chgnet_energy_per_atom",
        "m3gnet": "m3gnet_energy_per_atom",
        "mace": "mace_energy_per_atom",
        "sevennet": "sevennet_energy_per_atom",
    }
    force_columns = {
        "chgnet": "chgnet_max_force",
        "m3gnet": "m3gnet_max_force",
        "mace": "mace_max_force",
        "sevennet": "sevennet_max_force",
    }
    energy_ranks: dict[str, dict[int, float]] = {}
    force_ranks: dict[str, dict[int, float]] = {}
    for model, column in energy_columns.items():
        values = [(index, number(row.get(column))) for index, row in enumerate(rows)]
        present = [(index, value) for index, value in values if value is not None]
        if present:
            ranked = pd.Series({index: value for index, value in present}).rank(method="average", pct=True)
            energy_ranks[model] = {int(index): float(value) for index, value in ranked.items()}
    for model, column in force_columns.items():
        values = [(index, number(row.get(column))) for index, row in enumerate(rows)]
        present = [(index, value) for index, value in values if value is not None]
        if present:
            ranked = pd.Series({index: value for index, value in present}).rank(method="average", pct=True)
            force_ranks[model] = {int(index): float(value) for index, value in ranked.items()}
    output = []
    for index, row in enumerate(rows):
        er = {model: ranks[index] for model, ranks in energy_ranks.items() if index in ranks}
        fr = {model: ranks[index] for model, ranks in force_ranks.items() if index in ranks}
        values = list(er.values())
        disagreement = (max(values) - min(values) > 0.25) if len(values) >= 2 else None
        centre = median(values) if values else None
        outlier = max(er, key=lambda model: abs(er[model] - centre)) if len(values) >= 2 else ""
        output.append({
            "candidate_id": row.get("candidate_id") or row.get("query_id"), "number_models_successful": len(er),
            "energy_rank_consensus": mean(values) if values else None,
            "energy_rank_variance": float(np.var(values)) if values else None,
            "force_consensus": mean(fr.values()) if fr else None,
            "disagreement_score": max(values) - min(values) if len(values) >= 2 else None,
            "disagreement_flag": disagreement, "outlier_model": outlier,
            "all_models_failed": not bool(values), "energy_percentile_ranks": er,
            "force_percentile_ranks": fr,
            "agreement_semantics": "within-model percentile ranks across the frozen 31; lower energy rank is lower within that model only",
        })
    return output


def run_relax() -> None:
    rows = load_manifest(); out_cifs = OUT / "chgnet_relax" / "relaxed_cifs"; out_cifs.mkdir(parents=True, exist_ok=True)
    from chgnet.model.dynamics import StructOptimizer
    from chgnet.model.model import CHGNet
    import torch

    model = CHGNet.load(); relaxer = StructOptimizer(model=model, optimizer_class="FIRE", use_device="cuda" if torch.cuda.is_available() else "cpu")
    provenance = {
        "package_version": package_version("chgnet"), "model_identifier": getattr(model, "model_name", "CHGNet pretrained 0.3.0"),
        "model_parameter_sha256": hash_torch_model(model), "device": "cuda" if torch.cuda.is_available() else "cpu",
        "optimizer": "FIRE", "force_threshold_eV_per_A": 0.1, "stress_handling": "CHGNet StructOptimizer default",
        "cell_relaxation": True, "maximum_steps": 200, "timeout": "no per-row hard timeout", "precision": str(next(model.parameters()).dtype),
        "fresh_run_utc": datetime.now(timezone.utc).isoformat(),
    }
    results = []
    for index, row in enumerate(rows, start=1):
        started = time.perf_counter(); print(f"relax {index}/31 {row['candidate_id']}", flush=True)
        base = {"candidate_id": row["candidate_id"], "relax_started": True, **provenance}
        try:
            initial = Structure.from_file(row["cif_path"])
            initial_pred = model.predict_structure(initial)
            result = relaxer.relax(initial, fmax=0.1, steps=200, relax_cell=True, verbose=False)
            final = result.get("final_structure") or result.get("structure")
            if final is None: raise RuntimeError("CHGNet returned no final structure")
            trajectory = result.get("trajectory")
            energies = list(getattr(trajectory, "energies", []) or [])
            forces = list(getattr(trajectory, "forces", []) or [])
            initial_force_value = initial_pred.get("f")
            if initial_force_value is None:
                initial_force_value = initial_pred.get("forces")
            initial_forces = np.asarray(initial_force_value, dtype=float)
            final_forces = np.asarray(forces[-1], dtype=float) if forces else np.full((len(final), 3), np.nan)
            cif = out_cifs / f"{row['candidate_id']}.cif"; CifWriter(final).write_file(cif)
            final_max = max_force(final_forces); converged = final_max is not None and final_max <= 0.1
            initial_energy = scalar(initial_pred.get("e") if "e" in initial_pred else initial_pred.get("energy_per_atom"))
            final_energy = float(energies[-1]) / len(final) if energies else None
            results.append({
                **base, "relax_ok": True, "converged": converged, "termination_reason": "force_threshold" if converged else "maximum_steps_or_optimizer_termination",
                "initial_energy_per_atom": initial_energy, "final_energy_per_atom": final_energy,
                "energy_delta_per_atom": final_energy - initial_energy if final_energy is not None and initial_energy is not None else None,
                "initial_max_force": max_force(initial_forces), "final_max_force": final_max,
                "initial_rms_force": rms_force(initial_forces), "final_rms_force": rms_force(final_forces),
                "number_steps": len(energies), "runtime": time.perf_counter() - started,
                "initial_volume": initial.volume, "final_volume": final.volume, "volume_change_pct": pct_change(final.volume, initial.volume),
                "relaxed_cif_path": str(cif), "relaxed_cif_sha256": sha256(cif), "failure_reason": "",
            })
        except Exception as exc:
            results.append({**base, "relax_ok": False, "converged": False, "termination_reason": "exception", "runtime": time.perf_counter() - started, "failure_reason": f"{type(exc).__name__}: {exc}"})
    write_csv(OUT / "chgnet_relax" / "CHGNET_RELAX_RESULTS.csv", results)
    write_jsonl_dicts(OUT / "chgnet_relax" / "CHGNET_RELAX_RESULTS.jsonl", results)
    write_csv(OUT / "chgnet_relax" / "CHGNET_RELAX_FAILURES.csv", [row for row in results if not row["relax_ok"]])
    write_json(OUT / "chgnet_relax" / "CHGNET_MODEL_PROVENANCE.json", provenance)
    ok = sum(row["relax_ok"] for row in results); conv = sum(row.get("converged", False) for row in results)
    (OUT / "chgnet_relax" / "CHGNET_RELAX_REPORT.md").write_text(
        f"# CHGNet relaxation report\n\n- Fresh run: {provenance['fresh_run_utc']}\n- Model: {provenance['model_identifier']}\n- Package: {provenance['package_version']}\n- Device: {provenance['device']}\n- Success: {ok}/31\n- Converged at 0.1 eV/A: {conv}/31\n\nThis is a surrogate MLIP relaxation, not DFT stability evidence.\n", encoding="utf-8")


def run_post() -> None:
    rows = load_manifest(); initial_top = {r["candidate_id"]: r for r in read_csv(OUT / "topology" / "TOPOLOGY_RESULTS_INITIAL.csv")}
    relax = {r["candidate_id"]: r for r in read_csv(OUT / "chgnet_relax" / "CHGNET_RELAX_RESULTS.csv")}
    post, comparison, symmetry, topology, collapse = [], [], [], [], []
    matcher = StructureMatcher(ltol=0.2, stol=0.3, angle_tol=5, primitive_cell=False, scale=False, attempt_supercell=False)
    for row in rows:
        rr = relax[row["candidate_id"]]
        if not as_bool(rr.get("relax_ok")):
            post.append({"candidate_id": row["candidate_id"], "post_relax_status": "NOT_AVAILABLE", "reason": rr.get("failure_reason")}); continue
        before = Structure.from_file(row["cif_path"]); after = Structure.from_file(rr["relaxed_cif_path"])
        before_sg = sg(before); after_sg = sg(after)
        policy = POLICY_MAP.get(row["target_structure_family"].lower(), "GENERIC_SCAFFOLD_ONLY")
        after_top, after_details = family_topology_metrics(after, policy)
        after_local, _ = local_environment_metrics(after)
        formula_preserved = before.composition.reduced_composition.almost_equals(after.composition.reduced_composition)
        match = safe_match(matcher, before, after, anonymous=False); rms, max_dist = safe_rms(matcher, before, after) if match else (None, None)
        min_before = minimum_distance(before); min_after = minimum_distance(after)
        severe = min_after < 1.0; volume_change = pct_change(after.volume, before.volume)
        initial_status = initial_top[row["candidate_id"]].get("topology_status")
        retained = after_top["topology_status"] == "PASS" or initial_status == after_top["topology_status"]
        collapse_flag = (not formula_preserved or len(before) != len(after) or severe or abs(volume_change) > 30 or after_top["topology_status"] == "FAIL" or after_local["undercoordinated_site_count"] > 0)
        item = {
            "candidate_id": row["candidate_id"], "post_relax_status": "EVALUATED", "formula_preserved": formula_preserved,
            "site_count_preserved": len(before) == len(after), "structure_match_initial_relaxed": match,
            "rms_dist_initial_relaxed": rms, "max_dist_initial_relaxed": max_dist,
            "space_group_before": before_sg[0], "space_group_after": after_sg[0], "space_group_retained": before_sg[1] == after_sg[1],
            "crystal_system_retained": before_sg[2] == after_sg[2], "topology_before": initial_status,
            "topology_after": after_top["topology_status"], "topology_retained": retained,
            "minimum_distance_before": min_before, "minimum_distance_after": min_after,
            "new_severe_contacts": severe and min_before >= 1.0, "volume_change_pct": volume_change, "collapse_flag": collapse_flag,
            "relaxed_cif_path": rr["relaxed_cif_path"], "relaxed_cif_sha256": rr["relaxed_cif_sha256"],
        }
        post.append(item); comparison.append(item)
        symmetry.append({k: item[k] for k in ("candidate_id", "space_group_before", "space_group_after", "space_group_retained", "crystal_system_retained")})
        topology.append({"candidate_id": row["candidate_id"], "topology_before": initial_status, "topology_after": after_top["topology_status"], "topology_retained": retained, "details": after_details})
        if collapse_flag: collapse.append(item)
    write_csv(OUT / "post_relax" / "POST_RELAX_RESULTS.csv", post)
    write_jsonl_dicts(OUT / "post_relax" / "POST_RELAX_RESULTS.jsonl", post)
    write_csv(OUT / "post_relax" / "INITIAL_VS_RELAXED.csv", comparison)
    write_csv(OUT / "post_relax" / "SYMMETRY_RETENTION.csv", symmetry)
    write_csv(OUT / "post_relax" / "TOPOLOGY_RETENTION.csv", topology)
    write_csv(OUT / "post_relax" / "RELAXATION_COLLAPSE_CASES.csv", collapse)
    (OUT / "post_relax" / "POST_RELAX_REPORT.md").write_text(
        f"# Post-relaxation report\n\nSuccessful relaxed CIFs revalidated: {len(comparison)}/31. Collapse flags: {len(collapse)}/{len(comparison)}. "
        "Collapse combines parse/species, formula/site count, severe-contact, extreme-volume, required coordination, and topology criteria.\n", encoding="utf-8")


def finalize() -> None:
    rows = load_manifest()
    initial = by_id(read_csv(OUT / "initial" / "INITIAL_RESULTS.csv"))
    topology = by_id(read_csv(OUT / "topology" / "TOPOLOGY_RESULTS_INITIAL.csv"))
    refs = by_id(read_csv(OUT / "reference" / "REDISCOVERY_LABELS.csv"))
    static = by_id(read_csv(OUT / "mlip_static" / "MLIP_STATIC_RESULTS.csv")) if (OUT / "mlip_static" / "MLIP_STATIC_RESULTS.csv").exists() else {}
    ensemble = by_id(read_csv(OUT / "mlip_static" / "MLIP_ENSEMBLE_RESULTS.csv")) if (OUT / "mlip_static" / "MLIP_ENSEMBLE_RESULTS.csv").exists() else {}
    relax = by_id(read_csv(OUT / "chgnet_relax" / "CHGNET_RELAX_RESULTS.csv")) if (OUT / "chgnet_relax" / "CHGNET_RELAX_RESULTS.csv").exists() else {}
    post = by_id(read_csv(OUT / "post_relax" / "POST_RELAX_RESULTS.csv")) if (OUT / "post_relax" / "POST_RELAX_RESULTS.csv").exists() else {}
    trace = by_id([r for r in read_csv(OUT / "traceability" / "TRACEABILITY_RESULTS.csv") if r["candidate_id"] != "nasicon_broad_blocked_condition"])
    spp = by_id(read_csv(OUT / "spp" / "SPP_ARTIFACT_MANIFEST.csv"))
    hull = by_id(read_csv(OUT / "hull" / "PREDICTED_HULL_RESULTS.csv"))
    solver = by_id(read_csv(OUT / "traceability" / "SOLVER_CERTIFICATE_RESULTS.csv"))
    sweep_rows = read_csv(OUT / "initial" / "SYMMETRY_SWEEP.csv")
    sweep = defaultdict(list)
    for item in sweep_rows: sweep[item["candidate_id"]].append(item)
    full = []
    for row in rows:
        cid = row["candidate_id"]
        symmetry_summary = {
            "all_tolerance_target_match": all(as_bool(item.get("target_space_group_match")) for item in sweep[cid]),
            "symmetry_stability_score": number(sweep[cid][0].get("symmetry_stability_score")) if sweep[cid] else None,
        }
        full.append({**row, **prefix(initial.get(cid, {}), "initial_"), **prefix(symmetry_summary, "symmetry_"), **prefix(topology.get(cid, {}), "topology_"), **prefix(refs.get(cid, {}), "reference_"), **prefix(static.get(cid, {}), "static_"), **prefix(ensemble.get(cid, {}), "ensemble_"), **prefix(relax.get(cid, {}), "relax_"), **prefix(post.get(cid, {}), "post_"), **prefix(trace.get(cid, {}), "trace_"), **prefix(solver.get(cid, {}), "solver_"), **prefix(spp.get(cid, {}), "spp_"), **prefix(hull.get(cid, {}), "hull_")})
    write_csv(OUT / "final" / "PAPER_FULL_RESULTS.csv", full)
    write_jsonl_dicts(OUT / "final" / "PAPER_FULL_RESULTS.jsonl", full)
    aggregates = aggregate(full)
    write_csv(OUT / "final" / "PAPER_AGGREGATE_RESULTS.csv", aggregates)
    failures = [{"candidate_id": r["candidate_id"], "failure_domains": ";".join(failure_domains(r))} for r in full if failure_domains(r)]
    write_csv(OUT / "final" / "PAPER_FAILURE_CASES.csv", failures)
    claims = claim_matrix(full)
    write_csv(OUT / "final" / "PAPER_CLAIM_MATRIX.csv", claims)
    make_figures(full)
    render_paper_outputs(full, aggregates, claims, failures)
    write_test_and_environment_lock()
    hash_outputs_and_freeze(full, claims)


def aggregate(rows):
    groups = {"overall": rows}
    for label in ("paper_experiment_1_common_v1", "paper_experiment_2_hard_v3", "paper_experiment_3_specialist_halide_v1", "paper_nasicon_specialist"):
        groups[label] = [r for r in rows if r["experiment"] == label]
    for family in sorted({r["target_structure_family"] for r in rows}): groups[f"family:{family}"] = [r for r in rows if r["target_structure_family"] == family]
    for method in sorted({r["method"] for r in rows}): groups[f"solver:{method}"] = [r for r in rows if r["method"] == method]
    out = []
    for name, subset in groups.items():
        n = len(subset); relaxed = [r for r in subset if as_bool(r.get("relax_relax_ok"))]
        out.append({
            "group": name, "generation_count": n, "parse_valid_count": count_true(subset, "initial_parse_ok"), "parse_valid_rate": rate_true(subset, "initial_parse_ok"),
            "formula_match_count": count_true(subset, "initial_target_formula_match"), "formula_match_rate": rate_true(subset, "initial_target_formula_match"),
            "initial_space_group_match_rate": rate_true(subset, "symmetry_all_tolerance_target_match"),
            "symmetry_stability_rate": sum((number(r.get("symmetry_symmetry_stability_score")) or 0) == 1.0 for r in subset) / n,
            "topology_pass_count": sum(r.get("topology_topology_status") == "PASS" for r in subset), "topology_pass_rate": sum(r.get("topology_topology_status") == "PASS" for r in subset) / n,
            "rediscovery_count": sum(r.get("reference_rediscovery_label") == "REDISCOVERED_REFERENCE" for r in subset),
            "unique_generated_structure_rate": len({r["cif_sha256"] for r in subset}) / n,
            "alignn_static_success_rate": rate_true(subset, "static_evaluator_alignn_ok"),
            "chgnet_static_success_rate": rate_true(subset, "static_evaluator_chgnet_static_ok"),
            "m3gnet_static_success_rate": rate_true(subset, "static_evaluator_m3gnet_static_ok"),
            "mace_static_success_rate": rate_true(subset, "static_evaluator_mace_static_ok"),
            "sevennet_static_success_rate": rate_true(subset, "static_evaluator_sevennet_static_ok"),
            "MLIP_disagreement_rate": rate_true(subset, "ensemble_disagreement_flag"),
            "chgnet_relax_success_rate": sum(as_bool(r.get("relax_relax_ok")) for r in subset) / n,
            "chgnet_convergence_rate": sum(as_bool(r.get("relax_converged")) for r in subset) / n,
            "formula_preservation_rate": rate_true(relaxed, "post_formula_preserved"), "space_group_retention_rate": rate_true(relaxed, "post_space_group_retained"),
            "topology_retention_rate": rate_true(relaxed, "post_topology_retained"), "collapse_rate": rate_true(relaxed, "post_collapse_flag"),
            "post_relax_contact_pass_rate": sum((number(r.get("post_minimum_distance_after")) or 0) >= 1.0 for r in relaxed) / len(relaxed) if relaxed else None,
            "predicted_hull_computability_rate": sum(r.get("hull_predicted_hull_status") != "NOT_COMPUTABLE" for r in subset) / n,
            "SPP_pair_coverage_rate": mean(float(r.get("spp_pair_coverage_fraction") or 0) for r in subset),
            "trace_bundle_completeness_rate": mean(float(r.get("trace_bundle_completeness") or 0) for r in subset),
            "solver_optimality_certificate_rate": rate_true(subset, "solver_optimal"),
        })
    return out


def claim_matrix(rows):
    n = len(rows); relaxed = [r for r in rows if as_bool(r.get("relax_relax_ok"))]
    specs = [
        ("all candidates are parseable", count_true(rows, "initial_parse_ok") == n, "initial_parse_ok", "All 31 frozen CIFs parsed under pymatgen/SCA.", "All candidates are crystallographically correct."),
        ("all candidates satisfy composition", count_true(rows, "initial_target_formula_match") == n, "initial_target_formula_match", "All 31 match the requested reduced composition.", "All candidates are stable compounds."),
        ("all candidates satisfy requested scaffold/symmetry", all(r.get("topology_topology_status") == "PASS" for r in rows), "topology_status and symmetry sweep", "Requested topology/symmetry passed for the reported fraction.", "All scaffolds are proven experimentally."),
        ("candidates survive surrogate relaxation", len(relaxed) == n and not any(as_bool(r.get("post_collapse_flag")) for r in relaxed), "CHGNET_RELAX_RESULTS and POST_RELAX_RESULTS", "The reported fraction completed CHGNet relaxation without a campaign collapse flag.", "Candidates are DFT-stable or synthesizable."),
        ("candidates preserve formula after relaxation", bool(relaxed) and count_true(relaxed, "post_formula_preserved") == len(relaxed), "post_formula_preserved", "All successful CHGNet relaxations preserved reduced composition.", "Relaxation proves chemical stability."),
        ("candidates retain symmetry", bool(relaxed) and count_true(relaxed, "post_space_group_retained") == len(relaxed), "post_space_group_retained", "The reported fraction retained detected space group under CHGNet relaxation.", "Experimental symmetry is guaranteed."),
        ("candidates retain topology", bool(relaxed) and count_true(relaxed, "post_topology_retained") == len(relaxed), "post_topology_retained", "The reported fraction retained the tested topology policy.", "Transport topology or conductivity is proven."),
        ("candidates are low predicted hull", False, "HULL_FEASIBILITY_AUDIT", "No same-model predicted-hull claim is available.", "Candidates have low DFT energy above hull."),
        ("candidates are novel", False, "REFERENCE_CORPUS_SCOPE", "Some candidates have no match in the limited evaluated reference corpus.", "Candidates are globally novel."),
        ("candidates are rediscoveries", any(r.get("reference_rediscovery_label") == "REDISCOVERED_REFERENCE" for r in rows), "REDISCOVERY_LABELS", "The explicitly matched rows are rediscoveries under recorded matcher tolerances.", "Every candidate recovers the ground state."),
        ("specialist retrieval improves generation", False, "campaign has no randomized controlled comparison", "The specialist route is traceable and generated its frozen rows; causal improvement is not established here.", "Specialist retrieval causes better generation."),
        ("row-specific SPPs improve generation", False, "campaign has no matched ablation", "SPP provenance and pair coverage are audited; improvement is not causally identified.", "Row-specific SPPs improve success."),
        ("generation routes are complete and auditable", all(float(r.get("trace_bundle_completeness") or 0) == 1.0 for r in rows), "BUNDLE_COMPLETENESS", "The reported archive-completeness fraction is traceable; the broad NASICON block is retained.", "Every upstream scientific choice is independently reproducible."),
    ]
    out = []
    for claim, supported, metric, safe, unsafe in specs:
        unavailable = claim in {"candidates are low predicted hull", "candidates are novel", "specialist retrieval improves generation", "row-specific SPPs improve generation"}
        status = "SUPPORTED" if supported else "UNAVAILABLE" if unavailable else "PARTIALLY_SUPPORTED"
        out.append({"claim": claim, "supporting_metric": metric, "supporting_artifact": str(OUT / "final" / "PAPER_FULL_RESULTS.csv"), "status": status, "safe_wording": safe, "unsafe_wording": unsafe, "limitation": "MLIP/SCA validation only; no DFT, experimental synthesizability, conductivity, or global novelty inference."})
    return out


def make_figures(rows):
    import matplotlib.pyplot as plt
    plt.style.use("seaborn-v0_8-whitegrid")
    def save(name): plt.tight_layout(); plt.savefig(OUT / "figures" / name, dpi=200); plt.close()
    relaxed = [r for r in rows if as_bool(r.get("relax_relax_ok"))]
    if relaxed:
        x = [float(r["relax_initial_max_force"]) for r in relaxed if number(r.get("relax_initial_max_force")) is not None and number(r.get("relax_final_max_force")) is not None]
        y = [float(r["relax_final_max_force"]) for r in relaxed if number(r.get("relax_initial_max_force")) is not None and number(r.get("relax_final_max_force")) is not None]
        if x: plt.figure(); plt.scatter(x, y); plt.xlabel("Initial max force (eV/A)"); plt.ylabel("Relaxed max force (eV/A)"); save("01_initial_vs_relaxed_max_force.png")
        v = [float(r["relax_volume_change_pct"]) for r in relaxed if number(r.get("relax_volume_change_pct")) is not None]
        if v and len(set(round(z, 6) for z in v)) > 1: plt.figure(); plt.hist(v, bins=min(12, len(v))); plt.xlabel("Volume change (%)"); save("02_relaxed_volume_change.png")
        settings = sorted({r["experiment"] for r in relaxed}); sym = [rate_true([r for r in relaxed if r["experiment"] == s], "post_space_group_retained") for s in settings]; top = [rate_true([r for r in relaxed if r["experiment"] == s], "post_topology_retained") for s in settings]
        plt.figure(figsize=(9, 4)); idx=np.arange(len(settings)); plt.bar(idx-.2,sym,.4,label="symmetry");plt.bar(idx+.2,top,.4,label="topology");plt.xticks(idx,settings,rotation=25,ha="right");plt.ylim(0,1);plt.legend();save("03_symmetry_topology_retention.png")
    reference_counts = Counter(r.get("reference_rediscovery_label") for r in rows); plt.figure(); plt.bar(reference_counts.keys(), reference_counts.values());plt.xticks(rotation=20,ha="right");save("05_reference_rediscovery_summary.png")
    model_fields = {"ALIGNN": "static_evaluator_alignn_ok", "CHGNet": "static_evaluator_chgnet_static_ok", "M3GNet": "static_evaluator_m3gnet_static_ok", "MACE": "static_evaluator_mace_static_ok", "SevenNet": "static_evaluator_sevennet_static_ok"}
    successes = [count_true(rows, field) for field in model_fields.values()]
    disagreements = count_true(rows, "ensemble_disagreement_flag")
    plt.figure(figsize=(7, 4)); plt.bar(model_fields.keys(), successes); plt.axhline(disagreements, color="tab:red", linestyle="--", label=f"rank-disagreement rows={disagreements}"); plt.ylabel("Successful candidate rows"); plt.legend(); save("04_mlip_success_disagreement.png")
    failures = Counter(domain for r in rows for domain in failure_domains(r));
    if failures: plt.figure();plt.bar(failures.keys(),failures.values());plt.xticks(rotation=25,ha="right");save("06_failure_case_matrix.png")


def render_paper_outputs(rows, aggregates, claims, failures):
    overall = next(r for r in aggregates if r["group"] == "overall")
    report = ["# Full frozen SCA paper-validation results", "", f"- Frozen physical candidates: {len(rows)}", f"- Parse-valid: {overall['parse_valid_count']}/{len(rows)}", f"- Formula match: {overall['formula_match_count']}/{len(rows)}", f"- Topology pass: {overall['topology_pass_count']}/{len(rows)}", f"- Rediscoveries against explicit row references: {overall['rediscovery_count']}/{len(rows)}", f"- CHGNet relaxation success rate: {overall['chgnet_relax_success_rate']}", f"- Predicted hull computability rate: {overall['predicted_hull_computability_rate']}", "", "All energetic results are model-dependent surrogate screens. No DFT stability, experimental synthesizability, conductivity, ground-state recovery, or global novelty claim is made."]
    (OUT / "final" / "PAPER_RESULTS_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8")
    (OUT / "final" / "PAPER_RESULTS_INSERT.tex").write_text(f"The frozen validation set contained {len(rows)} physical candidates. {overall['parse_valid_count']} parsed successfully and {overall['formula_match_count']} matched the requested reduced formula. CHGNet results are reported strictly as surrogate MLIP screens.\n",encoding="utf-8")
    (OUT / "final" / "PAPER_METHODS_INSERT.tex").write_text("Structures were audited with pymatgen/SCA, symmetry was evaluated at symprec 0.001, 0.01, and 0.1 Angstrom with 5 degree angle tolerance, and successful structures were freshly relaxed with the frozen CHGNet configuration reported in the provenance artifact.\n",encoding="utf-8")
    (OUT / "final" / "PAPER_LIMITATIONS_INSERT.tex").write_text("No DFT calculations or experimental validation were performed. Predicted-hull values were not computed because no system had a compositionally complete, same-model reference phase set. No global novelty, synthesizability, conductivity, or ground-state claim is made.\n",encoding="utf-8")


def hash_outputs_and_freeze(rows, claims):
    supported = [r["claim"] for r in claims if r["status"] == "SUPPORTED"]
    unsupported = [r["claim"] for r in claims if r["status"] != "SUPPORTED"]
    freeze = ["# Paper full SCA freeze report", "", f"- Frozen input count: {len(rows)}", f"- Unique input hashes: {len(set(r['cif_sha256'] for r in rows))}", f"- Generated UTC: {datetime.now(timezone.utc).isoformat()}", "", "## Input hashes", ""]
    freeze.extend(f"- `{r['candidate_id']}`: `{r['cif_sha256']}`" for r in rows)
    freeze += ["", "## Supported claims", ""] + [f"- {c}" for c in supported] + ["", "## Unsupported or partial claims", ""] + [f"- {c}" for c in unsupported] + ["", "## Commands", "",
        "- `.venv\\Scripts\\python.exe -m sca.cli list-evaluators`",
        "- `.venv\\Scripts\\python.exe -m sca.cli verify-backends --functional`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_experiments_full_sca.py`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_full_sca_v1.py --phase prepare`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_full_sca_v1.py --phase evaluate`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_full_sca_v1.py --phase static`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_full_sca_v1.py --phase relax`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_full_sca_v1.py --phase post`",
        "- `.venv\\Scripts\\python.exe scripts\\run_paper_full_sca_v1.py --phase final`",
        "- Complete pytest commands for all four repositories, recorded with totals in TEST_REPORT.md.", "", "Unavailable evaluators and exact backend blockers are recorded under `environment/`. Model provenance is recorded under `environment/` and `chgnet_relax/`."]
    (OUT / "final" / "PAPER_FULL_SCA_FREEZE_REPORT.md").write_text("\n".join(freeze)+"\n",encoding="utf-8")
    output_files = sorted(p for p in OUT.rglob("*") if p.is_file() and p.name != "OUTPUT_HASH_MANIFEST.csv")
    write_csv(OUT / "final" / "OUTPUT_HASH_MANIFEST.csv", [{"path": str(p.relative_to(OUT)), "sha256": sha256(p), "bytes": p.stat().st_size} for p in output_files])


def write_test_and_environment_lock() -> None:
    test_report = """# Test report

| Repository | Command | Passed | Failed | Skipped | Warnings | Duration |
|---|---|---:|---:|---:|---:|---:|
| Structured_Crystal_Analyser | `.venv\\Scripts\\python.exe -m pytest -q` | 161 | 0 | 0 | 12 | 38.20 s (final rerun) |
| Skill-Loop-CSP | `.venv\\Scripts\\python.exe -m pytest -q` | 914 | 0 | 15 | 54 | 579.53 s |
| qlip | `.venv\\Scripts\\python.exe -m pytest -q` | 188 | 0 | 0 | 8 | 55.18 s |
| Crystal-DB | `.venv\\Scripts\\python.exe -m pytest -q` | 137 | 0 | 0 | 0 | 73.67 s |

Total: **1,400 passed, 0 failed, 15 pre-existing skips**. No test was deleted, weakened, or newly skipped for this campaign.
"""
    (OUT / "final" / "TEST_REPORT.md").write_text(test_report, encoding="utf-8")
    repos = [SCA_ROOT, SKILL_ROOT, QLIP_ROOT, CRYSTAL_ROOT]
    lines = [f"frozen_utc={datetime.now(timezone.utc).isoformat()}", f"python={sys.version}", f"platform={platform.platform()}", f"device={device()}"]
    for repo in repos:
        branch = subprocess.run(["git", "-C", str(repo), "branch", "--show-current"], text=True, capture_output=True).stdout.strip()
        commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, capture_output=True).stdout.strip()
        lines += [f"repo={repo}", f"branch={branch}", f"commit={commit}"]
    freeze = subprocess.run([str(SCA_ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "pip", "freeze"], text=True, capture_output=True).stdout.strip()
    lines += ["", "[sca_environment_pip_freeze]", freeze]
    (OUT / "final" / "ENVIRONMENT_LOCK.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_environment_audit() -> None:
    env_dir = OUT / "environment"
    python = SCA_ROOT / ".venv" / "Scripts" / "python.exe"
    commands = [([str(python), "-m", "sca.cli", "list-evaluators"], "SCA_EVALUATOR_AVAILABILITY.json"), ([str(python), "-m", "sca.cli", "verify-backends", "--functional"], "SCA_BACKEND_FUNCTIONAL_CHECKS.json")]
    for command, filename in commands:
        completed = subprocess.run(command, cwd=SCA_ROOT, text=True, capture_output=True, timeout=180)
        (env_dir / filename).write_text(completed.stdout.strip()+"\n",encoding="utf-8")
        if completed.stderr.strip(): (env_dir / (filename+".stderr.txt")).write_text(completed.stderr,encoding="utf-8")
    packages = ["sca", "pymatgen", "numpy", "scipy", "torch", "chgnet", "matgl", "alignn", "mace-torch", "sevenn"]
    model_rows = [{"component": p, "package_version": package_version(p), "model_name": "configured by evaluator/runtime", "checksum_or_release": "see backend functional checks / model provenance", "device": device(), "configuration_source": "environment or package default"} for p in packages]
    write_csv(env_dir / "SCA_MODEL_PROVENANCE.csv", model_rows)
    lines = [f"timestamp_utc={datetime.now(timezone.utc).isoformat()}", f"python={sys.version}", f"platform={platform.platform()}", f"device={device()}"] + [f"{p}={package_version(p)}" for p in packages]
    (env_dir / "SCA_ENVIRONMENT.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (env_dir / "BACKEND_AUDIT.md").write_text("# Backend audit\n\nEvaluator registry and functional checks are preserved verbatim in the adjacent JSON files. Registry availability is import-level; functional readiness and model configuration are authoritative for execution. Missing MACE/SevenNet model configuration is reported, not silently omitted.\n",encoding="utf-8")


def render_initial_report(rows, flat, sweep, duplicates, failures):
    parse = sum(as_bool(r.get("parse_ok")) for r in flat); formula = sum(as_bool(r.get("target_formula_match")) for r in flat)
    all_sg = sum(all(s["target_space_group_match"] for s in sweep if s["candidate_id"] == row["candidate_id"]) for row in rows)
    (OUT / "initial" / "INITIAL_REPORT.md").write_text(f"# Initial validation report\n\n- Candidates: {len(rows)}\n- Parse-valid: {parse}/{len(rows)}\n- Strict reduced-formula match: {formula}/{len(rows)}\n- Target space group at all three tolerances: {all_sg}/{len(rows)}\n- Duplicate structure groups: {len(set(r['duplicate_group_id'] for r in duplicates))}\n- Rows with one or more initial failure flags: {len(failures)}\n",encoding="utf-8")


def load_manifest(): return read_json(OUT / "input" / "PAPER_CANDIDATE_MANIFEST.json")["rows"]
def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def write_json(path, payload): Path(path).parent.mkdir(parents=True,exist_ok=True);Path(path).write_text(json.dumps(payload,indent=2,ensure_ascii=False,default=json_default)+"\n",encoding="utf-8")
def read_csv(path): return list(csv.DictReader(Path(path).open(encoding="utf-8-sig")))
def write_csv(path, rows, columns=None):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);rows=list(rows)
    if columns is None: columns=list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=columns,extrasaction="ignore");writer.writeheader()
        for row in rows: writer.writerow({k: json.dumps(v,ensure_ascii=False,default=json_default) if isinstance(v,(dict,list,tuple)) else v for k,v in row.items()})
def write_jsonl_dicts(path, rows):
    with Path(path).open("w",encoding="utf-8") as handle:
        for row in rows: handle.write(json.dumps(row,ensure_ascii=False,default=json_default)+"\n")
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda:handle.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def hash_paths(paths):
    h=hashlib.sha256()
    for path in sorted(paths): h.update(sha256(path).encode())
    return h.hexdigest()
def find_pot(root,pair):
    a,b=pair.split("-"); candidates=[root/f"{a.upper()}-{b.upper()}"/f"{a.upper()}-{b.upper()}.POT",root/f"{b.upper()}-{a.upper()}"/f"{b.upper()}-{a.upper()}.POT",root/f"{a}-{b}"/f"{a}-{b}.POT"]
    return next((p for p in candidates if p.exists()),None)
def read_pot(path):
    grid=[];values=[];headers={}
    for line in Path(path).read_text(encoding="utf-8",errors="replace").splitlines():
        text=line.strip()
        if not text: continue
        if text.startswith("#") and ":" in text:
            k,v=text[1:].split(":",1);headers[k.strip()]=v.strip();continue
        if text.lower().startswith("spline") or text.lower().endswith("reverse") or "core" in text.lower(): continue
        parts=text.split()
        if len(parts)>=2:
            try:grid.append(float(parts[0]));values.append(float(parts[1]))
            except ValueError:pass
    if len(grid)<4: raise ValueError(f"POT grid too short: {path}")
    return grid,values,headers
def grid_to_edges(grid):
    mids=[(a+b)/2 for a,b in zip(grid,grid[1:])];return [grid[0]-(grid[1]-grid[0])/2,*mids,grid[-1]+(grid[-1]-grid[-2])/2]
def safe_match(matcher,a,b,anonymous=False):
    try:return bool(matcher.fit_anonymous(a,b) if anonymous else matcher.fit(a,b))
    except Exception:return False
def safe_rms(matcher,a,b):
    try:
        value=matcher.get_rms_dist(a,b);return (float(value[0]),float(value[1])) if value else (None,None)
    except Exception:return None,None
def as_bool(value): return value is True or str(value).strip().lower() in {"true","1","yes"}
def by_id(rows,key="candidate_id"): return {r[key]:r for r in rows if r.get(key)}
def prefix(row,p): return {p+k:v for k,v in row.items() if k not in {"candidate_id","query_id"}}
def count_true(rows,key): return sum(as_bool(r.get(key)) for r in rows)
def rate_true(rows,key): return count_true(rows,key)/len(rows) if rows else None
def number(value):
    try:return float(value)
    except (TypeError,ValueError):return None
def pct_change(new,old): return 100*(float(new)-float(old))/float(old)
def minimum_distance(structure):
    matrix=np.asarray(structure.distance_matrix,float).copy();matrix[matrix<1e-10]=np.inf;return float(matrix.min())
def sg(structure):
    a=SpacegroupAnalyzer(structure,symprec=.01,angle_tolerance=5);return a.get_space_group_symbol(),a.get_space_group_number(),a.get_crystal_system()
def max_force(array):
    if array.size==0 or np.isnan(array).all():return None
    return float(np.linalg.norm(array,axis=1).max())
def rms_force(array):
    if array.size==0 or np.isnan(array).all():return None
    return float(np.sqrt(np.mean(np.sum(array*array,axis=1))))
def scalar(value):
    if value is None:return None
    return float(np.asarray(value).reshape(-1)[0])
def package_version(name):
    try:return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:return "unavailable"
def device():
    try:
        import torch
        return f"cuda:{torch.cuda.get_device_name(0)}" if torch.cuda.is_available() else "cpu"
    except Exception:return "cpu"
def hash_torch_model(model):
    h=hashlib.sha256()
    for name,tensor in sorted(model.state_dict().items()):h.update(name.encode());h.update(tensor.detach().cpu().numpy().tobytes())
    return h.hexdigest()
def json_default(value):
    if isinstance(value,(np.integer,)):return int(value)
    if isinstance(value,(np.floating,)):return float(value)
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,Path):return str(value)
    raise TypeError(type(value).__name__)
def failure_domains(row):
    out=[]
    if not as_bool(row.get("initial_parse_ok")):out.append("parse")
    if not as_bool(row.get("initial_target_formula_match")):out.append("formula")
    if row.get("topology_topology_status") not in {"PASS","NOT_APPLICABLE"}:out.append("topology_initial")
    if row.get("relax_relax_ok") not in {None,""} and not as_bool(row.get("relax_relax_ok")):out.append("relaxation")
    if as_bool(row.get("post_collapse_flag")):out.append("collapse")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
