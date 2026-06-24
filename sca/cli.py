"""Command line interface for SCA."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import typer
from click import ClickException
from rich.console import Console

from sca.backends import verify_optional_backends
from sca.benchmark import benchmark_folder, benchmark_manifest, benchmark_one
from sca.batch import evaluate_folder, evaluate_manifest, evaluate_many, evaluate_one
from sca.evaluators.alignn import AlignnEvaluator, DEFAULT_ALIGNN_MODEL
from sca.evaluators.novelty import load_reference_structures_with_stats
from sca.evaluators.registry import get_evaluator_spec, list_evaluator_specs
from sca.io import discover_cif_files, load_manifest, write_csv, write_jsonl, write_single_json, write_summary_csv
from sca.paper_benchmarks.manifest_builder import build_paper_run_manifest
from sca.paper_benchmarks.summary import build_paper_benchmark_summary, write_summary_outputs
from sca.pipelines.crystallm_style import evaluate_one_cif
from sca.schemas import AggregateSummary

app = typer.Typer(help="Structured Crystal Analyser.")
crystallm_app = typer.Typer(help="CrystaLLM-style pre-DFT crystal evaluation.")
alignn_app = typer.Typer(help="ALIGNN-based crystal structure evaluation.")
benchmark_app = typer.Typer(help="Modular generated-crystal benchmarking.")
app.add_typer(crystallm_app, name="crystallm-eval")
app.add_typer(alignn_app, name="alignn")
app.add_typer(benchmark_app, name="benchmark")
console = Console()


def _parse_bool(value: bool | str) -> bool:
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise typer.BadParameter(f"Expected true or false, got '{value}'")


def _parse_evaluators(value: str) -> list[str]:
    names = [name.strip() for name in value.split(",") if name.strip()]
    if not names:
        raise typer.BadParameter("At least one evaluator name is required")
    for name in names:
        try:
            get_evaluator_spec(name)
        except KeyError as exc:
            raise typer.BadParameter(str(exc)) from exc
    return names


@app.command("list-evaluators")
def list_evaluators() -> None:
    """List registered benchmark evaluators and optional dependency status."""

    rows = []
    for spec in list_evaluator_specs():
        rows.append(
            {
                "name": spec.name,
                "available": spec.available,
                "optional_dependencies": ",".join(spec.optional_dependencies),
                "missing_dependencies": ",".join(spec.missing_dependencies),
                "description": spec.description,
            }
        )
    console.print_json(data=rows)


@app.command("verify-backends")
def verify_backends(functional: bool = typer.Option(False, "--functional", help="Run tiny functional smoke checks where available.")) -> None:
    """Check optional benchmark backend imports and local model configuration."""

    console.print_json(data=verify_optional_backends(functional=functional))


@crystallm_app.command("one")
def crystallm_one(
    cif_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    target_formula: str | None = typer.Option(None, "--target-formula"),
    target_space_group: str | None = typer.Option(None, "--target-space-group"),
    out: Path = typer.Option(..., "--out", help="Output JSON path."),
    require_spacegroup: str = typer.Option("false", "--require-spacegroup"),
    alignn: str = typer.Option("false", "--alignn"),
    novelty: str = typer.Option("false", "--novelty"),
    reference_folder: Path | None = typer.Option(None, "--reference-folder", exists=True, file_okay=False, dir_okay=True),
    reference_manifest: Path | None = typer.Option(None, "--reference-manifest", exists=True, file_okay=True, dir_okay=False),
    reference_path_col: str = typer.Option("cif_path", "--reference-path-col"),
    reference_id_col: str | None = typer.Option(None, "--reference-id-col"),
) -> None:
    """Evaluate one CIF with CrystaLLM-style pre-DFT checks."""

    reference_structures = _load_references_for_cli(
        novelty=_parse_bool(novelty),
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        reference_path_col=reference_path_col,
        reference_id_col=reference_id_col,
    )
    record, _ = evaluate_one_cif(
        cif_path,
        target_formula=target_formula,
        target_space_group=target_space_group,
        require_spacegroup=_parse_bool(require_spacegroup),
        run_alignn=_parse_bool(alignn),
        reference_structures=reference_structures,
    )
    write_single_json(record, out)
    console.print_json(record.model_dump_json())


@crystallm_app.command("folder")
def crystallm_folder(
    folder_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, readable=True),
    out: Path = typer.Option(..., "--out", help="Output CSV path."),
    jsonl: Path = typer.Option(..., "--jsonl", help="Output JSONL path."),
    target_formula: str | None = typer.Option(None, "--target-formula"),
    target_space_group: str | None = typer.Option(None, "--target-space-group"),
    require_spacegroup: str = typer.Option("false", "--require-spacegroup"),
    alignn: str = typer.Option("false", "--alignn"),
    novelty: str = typer.Option("false", "--novelty"),
    reference_folder: Path | None = typer.Option(None, "--reference-folder", exists=True, file_okay=False, dir_okay=True),
    reference_manifest: Path | None = typer.Option(None, "--reference-manifest", exists=True, file_okay=True, dir_okay=False),
    reference_path_col: str = typer.Option("cif_path", "--reference-path-col"),
    reference_id_col: str | None = typer.Option(None, "--reference-id-col"),
    recursive: str = typer.Option("true", "--recursive"),
) -> None:
    """Evaluate all CIF files in a folder and write CSV plus JSONL reports."""

    reference_structures = _load_references_for_cli(
        novelty=_parse_bool(novelty),
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        reference_path_col=reference_path_col,
        reference_id_col=reference_id_col,
    )
    records = evaluate_folder(
        folder_path,
        target_formula=target_formula,
        target_space_group=target_space_group,
        require_spacegroup=_parse_bool(require_spacegroup),
        run_alignn=_parse_bool(alignn),
        recursive=_parse_bool(recursive),
        reference_structures=reference_structures,
    )
    write_csv(records, out)
    write_jsonl(records, jsonl)
    console.print(f"[green]Wrote {len(records)} records[/green] to {out} and {jsonl}")


@crystallm_app.command("manifest")
def crystallm_manifest(
    manifest_csv: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    path_col: str = typer.Option("cif_path", "--path-col"),
    formula_col: str = typer.Option("target_formula", "--formula-col"),
    spacegroup_col: str = typer.Option("target_space_group", "--spacegroup-col"),
    method_col: str = typer.Option("method", "--method-col"),
    query_id_col: str = typer.Option("query_id", "--query-id-col"),
    out: Path = typer.Option(..., "--out", help="Output CSV path."),
    jsonl: Path = typer.Option(..., "--jsonl", help="Output JSONL path."),
    require_spacegroup: str = typer.Option("false", "--require-spacegroup"),
    alignn: str = typer.Option("false", "--alignn"),
    novelty: str = typer.Option("false", "--novelty"),
    reference_folder: Path | None = typer.Option(None, "--reference-folder", exists=True, file_okay=False, dir_okay=True),
    reference_manifest: Path | None = typer.Option(None, "--reference-manifest", exists=True, file_okay=True, dir_okay=False),
    reference_path_col: str = typer.Option("cif_path", "--reference-path-col"),
    reference_id_col: str | None = typer.Option(None, "--reference-id-col"),
) -> None:
    """Evaluate CIF paths listed in a manifest."""

    reference_structures = _load_references_for_cli(
        novelty=_parse_bool(novelty),
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        reference_path_col=reference_path_col,
        reference_id_col=reference_id_col,
    )
    records = evaluate_manifest(
        manifest_csv,
        path_col=path_col,
        formula_col=formula_col,
        spacegroup_col=spacegroup_col,
        method_col=method_col,
        query_id_col=query_id_col,
        require_spacegroup=_parse_bool(require_spacegroup),
        run_alignn=_parse_bool(alignn),
        reference_structures=reference_structures,
    )
    write_csv(records, out)
    write_jsonl(records, jsonl)
    console.print(f"[green]Wrote {len(records)} records[/green] to {out} and {jsonl}")


@app.command("select-top-k")
def select_top_k(
    eval_csv: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    group_cols: str = typer.Option("method,query_id", "--group-cols"),
    k: int = typer.Option(5, "--k", min=1),
    out: Path = typer.Option(..., "--out", help="Output CSV path."),
) -> None:
    """Select up to k records per group for later DFT."""

    frame = pd.read_csv(eval_csv)
    columns = [column.strip() for column in group_cols.split(",") if column.strip()]
    for column in columns + ["pre_dft_rank_score"]:
        if column not in frame.columns:
            raise typer.BadParameter(f"Column '{column}' not found in {eval_csv}")
    selected = (
        frame.sort_values(columns + ["pre_dft_rank_score"], ascending=True)
        .groupby(columns, dropna=False, as_index=False, group_keys=False)
        .head(k)
        .copy()
    )
    selected["selected_for_dft"] = True
    out.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(out, index=False)
    console.print(f"[green]Selected {len(selected)} records[/green] into {out}")


@app.command("summarize")
def summarize(
    eval_csv: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    group_col: str = typer.Option("method", "--group-col"),
    out: Path = typer.Option(..., "--out", help="Output summary CSV path."),
) -> None:
    """Summarize an evaluation CSV by group."""

    frame = pd.read_csv(eval_csv)
    if group_col not in frame.columns:
        frame[group_col] = None
    summaries = [_summarize_group(str(group), group_frame) for group, group_frame in frame.groupby(group_col, dropna=False)]
    write_summary_csv(summaries, out)
    console.print(f"[green]Wrote {len(summaries)} summary rows[/green] to {out}")


@app.command("benchmark-summary")
def benchmark_summary(
    benchmark_csv: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    group_col: str = typer.Option("method", "--group-col"),
    out: Path = typer.Option(..., "--out", help="Output benchmark summary CSV path."),
) -> None:
    """Summarize modular benchmark CSV output by a grouping column."""

    frame = pd.read_csv(benchmark_csv)
    if group_col not in frame.columns:
        frame = frame.copy()
        frame[group_col] = "all"
    rows = [
        _benchmark_summary_group(str(group), group_frame)
        for group, group_frame in frame.groupby(group_col, dropna=False)
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False)
    console.print(f"[green]Wrote {len(rows)} benchmark summary rows[/green] to {out}")


@app.command("paper-benchmark-summary")
def paper_benchmark_summary(
    results_csv: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    manifest: Path = typer.Option(..., "--manifest", exists=True, file_okay=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", help="Output paper benchmark summary CSV."),
    json_out: Path = typer.Option(..., "--json", help="Output paper benchmark summary JSON."),
    markdown: Path | None = typer.Option(None, "--markdown", help="Optional Markdown report output."),
    group_col: str = typer.Option("benchmark_group", "--group-col"),
    id_col: str = typer.Option("benchmark_id", "--id-col"),
    attempt_col: str = typer.Option("attempt_id", "--attempt-col"),
    target_col: str = typer.Option("benchmark_id", "--target-col"),
    reference_required_policy: str = typer.Option("warn", "--reference-required-policy"),
    include_built_in_comparators: bool = typer.Option(False, "--include-built-in-comparators"),
    comparator_values: Path | None = typer.Option(None, "--comparator-values", exists=True, file_okay=True, dir_okay=False, readable=True),
) -> None:
    """Summarize SCA outputs against paper-comparable A-E benchmark metrics."""

    summary = build_paper_benchmark_summary(
        results_csv=results_csv,
        manifest_csv=manifest,
        comparator_values=comparator_values,
        include_built_in_comparators=include_built_in_comparators,
        group_col=group_col,
        id_col=target_col or id_col,
        attempt_col=attempt_col,
        reference_required_policy=reference_required_policy,
    )
    write_summary_outputs(summary, out_csv=out, out_json=json_out, markdown=markdown)
    console.print(f"[green]Wrote {len(summary.rows)} paper benchmark summary rows[/green] to {out} and {json_out}")


@app.command("build-paper-run-manifest")
def build_paper_run_manifest_cli(
    targets: Path = typer.Option(..., "--targets", exists=True, file_okay=True, dir_okay=False, readable=True),
    generated_folder: Path = typer.Option(..., "--generated-folder", exists=True, file_okay=False, dir_okay=True, readable=True),
    out: Path = typer.Option(..., "--out", help="Output generated benchmark manifest CSV."),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive"),
) -> None:
    """Map generated CIF files onto paper benchmark target rows."""

    frame = build_paper_run_manifest(
        targets_csv=targets,
        generated_folder=generated_folder,
        out_csv=out,
        recursive=recursive,
    )
    mapped = int((frame["mapping_status"] == "matched").sum()) if "mapping_status" in frame else 0
    console.print(
        f"[green]Wrote {len(frame)} manifest rows[/green] to {out} "
        f"({mapped} matched, {len(frame) - mapped} unmapped)"
    )


def _benchmark_summary_group(group_value: str, frame: pd.DataFrame) -> dict:
    alignn_values = _numeric(frame, "formation_energy_per_atom").dropna()
    if alignn_values.empty:
        alignn_values = _numeric(frame, "alignn_formation_energy_per_atom").dropna()
    chgnet_values = _numeric(frame, "chgnet_energy_per_atom").dropna()
    hull_values = _numeric(frame, "predicted_energy_above_hull").dropna()
    property_error_values = _numeric(frame, "property_error").dropna()
    return {
        "group_value": group_value,
        "num_generated": len(frame),
        "parse_valid_rate": _bool_rate(frame, "parse_ok"),
        "target_formula_match_rate": _bool_rate(frame, "target_formula_match"),
        "space_group_consistency_rate": _bool_rate(frame, "space_group_consistent"),
        "target_structure_match_rate": _bool_rate(frame, "structure_match"),
        "known_match_rate": _bool_rate(frame, "known_match"),
        "novel_rate": _bool_rate(frame, "novel_by_structure_matcher"),
        "duplicate_rate": _bool_rate(frame, "is_duplicate"),
        "median_alignn_formation_energy": (
            float(alignn_values.median()) if not alignn_values.empty else None
        ),
        "median_chgnet_energy_per_atom": (
            float(chgnet_values.median()) if not chgnet_values.empty else None
        ),
        "predicted_hull_ok_rate": _bool_rate(frame, "hull_ok"),
        "median_predicted_energy_above_hull": (
            float(hull_values.median()) if not hull_values.empty else None
        ),
        "property_target_ok_rate": _bool_rate(frame, "property_target_ok"),
        "median_abs_property_error": (
            float(property_error_values.abs().median()) if not property_error_values.empty else None
        ),
    }


def _summarize_group(group_value: str, frame: pd.DataFrame) -> AggregateSummary:
    alignn_values = _numeric(frame, "formation_energy_per_atom").dropna()
    return AggregateSummary(
        group_value=group_value,
        num_generated=len(frame),
        parse_valid_rate=_bool_rate(frame, "parse_ok"),
        target_formula_match_rate=_bool_rate(frame, "target_formula_match"),
        space_group_consistency_rate=_bool_rate(frame, "space_group_consistent"),
        multiplicity_consistency_rate=_bool_rate(frame, "multiplicity_consistent"),
        bond_reasonable_rate=_bool_rate(frame, "bond_lengths_reasonable"),
        geometry_ok_rate=_bool_rate(frame, "geometry_ok"),
        pre_dft_valid_rate=_bool_rate(frame, "pre_dft_valid"),
        unique_valid_count=_unique_valid_count(frame),
        duplicate_rate=_bool_rate(frame, "is_duplicate"),
        novelty_checked_count=int(_bool_series(frame, "novelty_checked").sum()) if "novelty_checked" in frame else 0,
        novel_rate=_bool_rate(frame, "novel_by_structure_matcher"),
        known_match_rate=_bool_rate(frame, "known_match"),
        median_alignn_formation_energy=float(alignn_values.median()) if not alignn_values.empty else None,
        best_alignn_formation_energy=float(alignn_values.min()) if not alignn_values.empty else None,
    )


def _load_references_for_cli(
    novelty: bool,
    reference_folder: Path | None,
    reference_manifest: Path | None,
    reference_path_col: str,
    reference_id_col: str | None,
):
    if not novelty:
        return None
    if reference_folder is None and reference_manifest is None:
        raise ClickException(
            "--novelty true requires --reference-folder or --reference-manifest"
        )
    load_result = load_reference_structures_with_stats(
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        path_col=reference_path_col,
        id_col=reference_id_col,
    )
    console.print(
        "[cyan]Loaded reference structures:[/cyan] "
        f"{load_result.loaded_count} loaded, {load_result.failed_count} failed"
    )
    return load_result.structures


def _bool_rate(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns:
        return None
    series = _bool_series(frame, column)
    non_null = series.dropna()
    if non_null.empty:
        return None
    return float(non_null.mean())


def _bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return frame[column].map(
        lambda value: None
        if pd.isna(value)
        else str(value).strip().lower() in {"true", "1", "yes"}
        if not isinstance(value, bool)
        else value
    )


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _unique_valid_count(frame: pd.DataFrame) -> int:
    if "pre_dft_valid" not in frame.columns:
        return 0
    valid = _bool_series(frame, "pre_dft_valid") == True  # noqa: E712
    if "is_unique_representative" not in frame.columns:
        return int(valid.sum())
    unique = _bool_series(frame, "is_unique_representative")
    return int((valid & (unique != False)).sum())  # noqa: E712


def _alignn(model: str) -> AlignnEvaluator:
    return AlignnEvaluator(model_name=model)


@benchmark_app.command("one")
def benchmark_cli_one(
    cif_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    target_formula: str | None = typer.Option(None, "--target-formula"),
    target_space_group: str | None = typer.Option(None, "--target-space-group"),
    target_cif_path: Path | None = typer.Option(None, "--target-cif-path", exists=True, file_okay=True, dir_okay=False),
    reference_id: str | None = typer.Option(None, "--reference-id"),
    structure_match_mode: str = typer.Option("both", "--structure-match-mode"),
    spp_artifact: Path | None = typer.Option(None, "--spp-artifact", exists=True, file_okay=True, dir_okay=False),
    hull_reference: Path | None = typer.Option(None, "--hull-reference", exists=True, file_okay=True, dir_okay=False),
    target_formation_energy_per_atom: float | None = typer.Option(None, "--target-formation-energy-per-atom"),
    target_energy_above_hull: float | None = typer.Option(None, "--target-energy-above-hull"),
    target_band_gap: float | None = typer.Option(None, "--target-band-gap"),
    target_property_name: str | None = typer.Option(None, "--target-property-name"),
    target_property_value: float | None = typer.Option(None, "--target-property-value"),
    method: str | None = typer.Option(None, "--method"),
    query_id: str | None = typer.Option(None, "--query-id"),
    evaluators: str = typer.Option("pre_dft_validity", "--evaluators", help="Comma-separated evaluator names."),
    out: Path = typer.Option(..., "--out", help="Output benchmark JSON path, or CSV path when --jsonl is used."),
    jsonl: Path | None = typer.Option(None, "--jsonl", help="Optional output benchmark JSONL path."),
    require_spacegroup: str = typer.Option("false", "--require-spacegroup"),
    alignn: str = typer.Option("false", "--alignn", help="Run ALIGNN inside pre_dft_validity."),
    novelty: str = typer.Option("false", "--novelty"),
    reference_folder: Path | None = typer.Option(None, "--reference-folder", exists=True, file_okay=False, dir_okay=True),
    reference_manifest: Path | None = typer.Option(None, "--reference-manifest", exists=True, file_okay=True, dir_okay=False),
    reference_path_col: str = typer.Option("cif_path", "--reference-path-col"),
    reference_id_col: str | None = typer.Option(None, "--reference-id-col"),
) -> None:
    """Benchmark one CIF with registered evaluators."""

    reference_structures = _load_references_for_cli(
        novelty=_parse_bool(novelty),
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        reference_path_col=reference_path_col,
        reference_id_col=reference_id_col,
    )
    record = benchmark_one(
        cif_path,
        evaluator_names=_parse_evaluators(evaluators),
        target_formula=target_formula,
        target_space_group=target_space_group,
        target_cif_path=target_cif_path,
        reference_id=reference_id,
        structure_match_mode=structure_match_mode,
        spp_artifact=spp_artifact,
        hull_reference_path=hull_reference,
        target_formation_energy_per_atom=target_formation_energy_per_atom,
        target_energy_above_hull=target_energy_above_hull,
        target_band_gap=target_band_gap,
        target_property_name=target_property_name,
        target_property_value=target_property_value,
        method=method,
        query_id=query_id,
        require_spacegroup=_parse_bool(require_spacegroup),
        run_alignn=_parse_bool(alignn),
        reference_structures=reference_structures,
    )
    if jsonl is None:
        write_single_json(record, out)
        console.print_json(record.model_dump_json())
        return
    write_csv([record], out)
    write_jsonl([record], jsonl)
    console.print(f"[green]Wrote 1 benchmark record[/green] to {out} and {jsonl}")


@benchmark_app.command("folder")
def benchmark_cli_folder(
    folder_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, readable=True),
    out: Path = typer.Option(..., "--out", help="Output benchmark CSV path."),
    jsonl: Path = typer.Option(..., "--jsonl", help="Output benchmark JSONL path."),
    target_formula: str | None = typer.Option(None, "--target-formula"),
    target_space_group: str | None = typer.Option(None, "--target-space-group"),
    target_cif_path: Path | None = typer.Option(None, "--target-cif-path", exists=True, file_okay=True, dir_okay=False),
    reference_id: str | None = typer.Option(None, "--reference-id"),
    structure_match_mode: str = typer.Option("both", "--structure-match-mode"),
    spp_artifact: Path | None = typer.Option(None, "--spp-artifact", exists=True, file_okay=True, dir_okay=False),
    hull_reference: Path | None = typer.Option(None, "--hull-reference", exists=True, file_okay=True, dir_okay=False),
    target_formation_energy_per_atom: float | None = typer.Option(None, "--target-formation-energy-per-atom"),
    target_energy_above_hull: float | None = typer.Option(None, "--target-energy-above-hull"),
    target_band_gap: float | None = typer.Option(None, "--target-band-gap"),
    target_property_name: str | None = typer.Option(None, "--target-property-name"),
    target_property_value: float | None = typer.Option(None, "--target-property-value"),
    method: str | None = typer.Option(None, "--method"),
    query_id: str | None = typer.Option(None, "--query-id"),
    evaluators: str = typer.Option("pre_dft_validity", "--evaluators", help="Comma-separated evaluator names."),
    require_spacegroup: str = typer.Option("false", "--require-spacegroup"),
    alignn: str = typer.Option("false", "--alignn", help="Run ALIGNN inside pre_dft_validity."),
    novelty: str = typer.Option("false", "--novelty"),
    reference_folder: Path | None = typer.Option(None, "--reference-folder", exists=True, file_okay=False, dir_okay=True),
    reference_manifest: Path | None = typer.Option(None, "--reference-manifest", exists=True, file_okay=True, dir_okay=False),
    reference_path_col: str = typer.Option("cif_path", "--reference-path-col"),
    reference_id_col: str | None = typer.Option(None, "--reference-id-col"),
    recursive: str = typer.Option("true", "--recursive"),
) -> None:
    """Benchmark all CIF files in a folder."""

    reference_structures = _load_references_for_cli(
        novelty=_parse_bool(novelty),
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        reference_path_col=reference_path_col,
        reference_id_col=reference_id_col,
    )
    records = benchmark_folder(
        folder_path,
        evaluator_names=_parse_evaluators(evaluators),
        target_formula=target_formula,
        target_space_group=target_space_group,
        target_cif_path=target_cif_path,
        reference_id=reference_id,
        structure_match_mode=structure_match_mode,
        spp_artifact=spp_artifact,
        hull_reference_path=hull_reference,
        target_formation_energy_per_atom=target_formation_energy_per_atom,
        target_energy_above_hull=target_energy_above_hull,
        target_band_gap=target_band_gap,
        target_property_name=target_property_name,
        target_property_value=target_property_value,
        method=method,
        query_id=query_id,
        require_spacegroup=_parse_bool(require_spacegroup),
        run_alignn=_parse_bool(alignn),
        recursive=_parse_bool(recursive),
        reference_structures=reference_structures,
    )
    write_csv(records, out)
    write_jsonl(records, jsonl)
    console.print(f"[green]Wrote {len(records)} benchmark records[/green] to {out} and {jsonl}")


@benchmark_app.command("manifest")
def benchmark_cli_manifest(
    manifest_csv: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    path_col: str = typer.Option("cif_path", "--path-col"),
    formula_col: str = typer.Option("target_formula", "--formula-col"),
    spacegroup_col: str = typer.Option("target_space_group", "--spacegroup-col"),
    target_cif_col: str = typer.Option("target_cif_path", "--target-cif-col"),
    target_reference_id_col: str = typer.Option("reference_id", "--target-reference-id-col"),
    structure_match_mode: str = typer.Option("both", "--structure-match-mode"),
    spp_artifact: Path | None = typer.Option(None, "--spp-artifact", exists=True, file_okay=True, dir_okay=False),
    hull_reference: Path | None = typer.Option(None, "--hull-reference", exists=True, file_okay=True, dir_okay=False),
    target_formation_energy_col: str = typer.Option("target_formation_energy_per_atom", "--target-formation-energy-col"),
    target_energy_above_hull_col: str = typer.Option("target_energy_above_hull", "--target-energy-above-hull-col"),
    target_band_gap_col: str = typer.Option("target_band_gap", "--target-band-gap-col"),
    target_property_name_col: str = typer.Option("target_property_name", "--target-property-name-col"),
    target_property_value_col: str = typer.Option("target_property_value", "--target-property-value-col"),
    method_col: str = typer.Option("method", "--method-col"),
    query_id_col: str = typer.Option("query_id", "--query-id-col"),
    evaluators: str = typer.Option("pre_dft_validity", "--evaluators", help="Comma-separated evaluator names."),
    out: Path = typer.Option(..., "--out", help="Output benchmark CSV path."),
    jsonl: Path = typer.Option(..., "--jsonl", help="Output benchmark JSONL path."),
    require_spacegroup: str = typer.Option("false", "--require-spacegroup"),
    alignn: str = typer.Option("false", "--alignn", help="Run ALIGNN inside pre_dft_validity."),
    novelty: str = typer.Option("false", "--novelty"),
    reference_folder: Path | None = typer.Option(None, "--reference-folder", exists=True, file_okay=False, dir_okay=True),
    reference_manifest: Path | None = typer.Option(None, "--reference-manifest", exists=True, file_okay=True, dir_okay=False),
    reference_path_col: str = typer.Option("cif_path", "--reference-path-col"),
    reference_id_col: str | None = typer.Option(None, "--reference-id-col"),
) -> None:
    """Benchmark CIF paths listed in a manifest."""

    reference_structures = _load_references_for_cli(
        novelty=_parse_bool(novelty),
        reference_folder=reference_folder,
        reference_manifest=reference_manifest,
        reference_path_col=reference_path_col,
        reference_id_col=reference_id_col,
    )
    records = benchmark_manifest(
        manifest_csv,
        evaluator_names=_parse_evaluators(evaluators),
        path_col=path_col,
        formula_col=formula_col,
        spacegroup_col=spacegroup_col,
        target_cif_col=target_cif_col,
        reference_id_col=target_reference_id_col,
        structure_match_mode=structure_match_mode,
        spp_artifact=spp_artifact,
        hull_reference_path=hull_reference,
        target_formation_energy_col=target_formation_energy_col,
        target_energy_above_hull_col=target_energy_above_hull_col,
        target_band_gap_col=target_band_gap_col,
        target_property_name_col=target_property_name_col,
        target_property_value_col=target_property_value_col,
        method_col=method_col,
        query_id_col=query_id_col,
        require_spacegroup=_parse_bool(require_spacegroup),
        run_alignn=_parse_bool(alignn),
        reference_structures=reference_structures,
    )
    write_csv(records, out)
    write_jsonl(records, jsonl)
    console.print(f"[green]Wrote {len(records)} benchmark records[/green] to {out} and {jsonl}")


@alignn_app.command("one")
def alignn_one(
    cif_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    out: Path = typer.Option(..., "--out", help="Output JSON path."),
    model: str = typer.Option(DEFAULT_ALIGNN_MODEL, "--model", help="ALIGNN model name."),
) -> None:
    """Evaluate one CIF and write a JSON result."""

    result = evaluate_one(cif_path, _alignn(model))
    write_single_json(result, out)
    console.print_json(result.model_dump_json())


@alignn_app.command("folder")
def alignn_folder(
    folder_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True, readable=True),
    out: Path = typer.Option(..., "--out", help="Output CSV path."),
    jsonl: Path = typer.Option(..., "--jsonl", help="Output JSONL path."),
    model: str = typer.Option(DEFAULT_ALIGNN_MODEL, "--model", help="ALIGNN model name."),
) -> None:
    """Evaluate all CIF files in a folder and write CSV plus JSONL outputs."""

    paths = discover_cif_files(folder_path)
    results = evaluate_many(paths, _alignn(model))
    write_csv(results, out)
    write_jsonl(results, jsonl)
    console.print(f"[green]Wrote {len(results)} results[/green] to {out} and {jsonl}")


@alignn_app.command("manifest")
def alignn_manifest(
    csv_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    path_col: str = typer.Option("cif_path", "--path-col", help="Manifest column containing CIF paths."),
    out: Path = typer.Option(..., "--out", help="Output CSV path."),
    jsonl: Path = typer.Option(..., "--jsonl", help="Output JSONL path."),
    model: str = typer.Option(DEFAULT_ALIGNN_MODEL, "--model", help="ALIGNN model name."),
) -> None:
    """Evaluate CIF paths listed in a CSV manifest."""

    paths = load_manifest(csv_path, path_col)
    results = evaluate_many(paths, _alignn(model))
    write_csv(results, out)
    write_jsonl(results, jsonl)
    console.print(f"[green]Wrote {len(results)} results[/green] to {out} and {jsonl}")


if __name__ == "__main__":
    app()
