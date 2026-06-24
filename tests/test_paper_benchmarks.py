from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from sca.benchmark import benchmark_manifest
from sca.cli import app
from sca.paper_benchmarks.manifest_builder import build_paper_run_manifest
from sca.paper_benchmarks.comparators import built_in_comparators
from sca.paper_benchmarks.summary import build_paper_benchmark_summary


FIXTURES = Path("tests/fixtures/paper_benchmarks")
runner = CliRunner()


def _rows_by_metric(summary):
    rows = [row for row in summary.rows if row["summary_scope"] == "global" and not row["comparator_name"]]
    return {row["metric_name"]: row for row in rows}


def test_validity_metrics_and_missing_composition() -> None:
    summary = build_paper_benchmark_summary(FIXTURES / "results_ae.csv", FIXTURES / "manifest.csv")
    rows = _rows_by_metric(summary)

    assert rows["parse_validity_rate"]["our_value"] == 0.8
    assert rows["pre_dft_validity_rate"]["our_value"] == 0.6
    assert rows["bad_contact_rate"]["our_value"] == 0.4
    assert rows["hard_fail_count"]["our_value"] == 2.0

    missing = build_paper_benchmark_summary(FIXTURES / "results_missing.csv", FIXTURES / "manifest.csv")
    missing_rows = _rows_by_metric(missing)
    assert missing_rows["composition_match_rate"]["our_value"] is None
    assert missing_rows["composition_match_rate"]["n_not_computable"] == 2


def test_structure_metrics_n1_nk_and_rms() -> None:
    summary = build_paper_benchmark_summary(FIXTURES / "results_ae.csv", FIXTURES / "manifest.csv")
    rows = _rows_by_metric(summary)

    assert rows["structure_match_rate"]["our_value"] == 0.5
    assert rows["match_rate_n1"]["our_value"] == 0.5
    assert rows["match_rate_nk"]["our_value"] == 1.0
    assert rows["best_rms_dist"]["our_value"] == 0.03
    assert rows["mean_rms_dist"]["our_value"] == 0.07

    missing = build_paper_benchmark_summary(FIXTURES / "results_missing.csv", FIXTURES / "manifest.csv")
    assert _rows_by_metric(missing)["structure_match_rate"]["n_not_computable"] == 2


def test_mlip_and_hull_metrics() -> None:
    summary = build_paper_benchmark_summary(FIXTURES / "results_ae.csv", FIXTURES / "manifest.csv")
    rows = _rows_by_metric(summary)

    assert rows["chgnet_ok_rate"]["our_value"] == 1.0
    assert rows["m3gnet_ok_rate"]["our_value"] == 0.6
    assert rows["mlip_consensus_stable_rate"]["our_value"] == 0.6
    assert rows["mlip_disagreement_rate"]["our_value"] == 0.2
    assert rows["predicted_ehull_rate_0_15"]["our_value"] == 0.6
    assert rows["predicted_metastable_rate_ehull_0_15"]["our_value"] == 0.6

    missing = build_paper_benchmark_summary(FIXTURES / "results_missing.csv", FIXTURES / "manifest.csv")
    assert _rows_by_metric(missing)["predicted_ehull_rate_0_15"]["our_value"] is None


def test_relaxation_metrics_not_faked_from_static_columns() -> None:
    summary = build_paper_benchmark_summary(FIXTURES / "results_ae.csv", FIXTURES / "manifest.csv")
    rows = _rows_by_metric(summary)

    assert rows["relax_success_rate"]["our_value"] == 0.75
    assert rows["median_energy_drop_per_atom"]["our_value"] == 0.10
    assert rows["force_threshold_success_rate_0_20"]["our_value"] == 1.0
    assert rows["rmse_improvement_rate"]["our_value"] == 1.0
    assert rows["median_rmse_delta"]["our_value"] == 0.04

    missing = build_paper_benchmark_summary(FIXTURES / "results_missing.csv", FIXTURES / "manifest.csv")
    assert _rows_by_metric(missing)["relax_success_rate"]["our_value"] is None


def test_novelty_sun_metrics_use_hull_then_mlip_fallback() -> None:
    summary = build_paper_benchmark_summary(FIXTURES / "results_ae.csv", FIXTURES / "manifest.csv")
    rows = _rows_by_metric(summary)

    assert rows["unique_rate"]["our_value"] == 0.8
    assert rows["local_novelty_rate"]["our_value"] == 0.8
    assert rows["sun_count"]["our_value"] == 3.0
    assert rows["sun_rate"]["our_value"] == 0.6
    assert "local novelty" in rows["local_novelty_rate"]["notes"]

    no_hull = pd.read_csv(FIXTURES / "results_ae.csv").drop(columns=["predicted_energy_above_hull"])
    temp = FIXTURES / "_tmp_no_hull.csv"
    no_hull.to_csv(temp, index=False)
    try:
        fallback = build_paper_benchmark_summary(temp, FIXTURES / "manifest.csv")
        assert _rows_by_metric(fallback)["sun_rate"]["our_value"] == 0.6
    finally:
        temp.unlink(missing_ok=True)


def test_comparator_logic_and_built_ins() -> None:
    summary = build_paper_benchmark_summary(
        FIXTURES / "results_ae.csv",
        FIXTURES / "manifest.csv",
        include_built_in_comparators=True,
    )
    comparator_rows = [row for row in summary.rows if row["comparator_name"]]
    names = {row["comparator_name"] for row in comparator_rows}

    assert "fixture_validity" in names
    assert "Lang2Str_MP20" in names
    assert any(row["beats_comparator"] is True for row in comparator_rows if row["comparator_name"] == "fixture_validity")
    assert built_in_comparators()


def test_paper_benchmark_summary_cli_writes_csv_json_and_markdown(tmp_path: Path) -> None:
    out_csv = tmp_path / "summary.csv"
    out_json = tmp_path / "summary.json"
    out_md = tmp_path / "summary.md"

    result = runner.invoke(
        app,
        [
            "paper-benchmark-summary",
            str(FIXTURES / "results_ae.csv"),
            "--manifest",
            str(FIXTURES / "manifest.csv"),
            "--include-built-in-comparators",
            "--out",
            str(out_csv),
            "--json",
            str(out_json),
            "--markdown",
            str(out_md),
        ],
    )

    assert result.exit_code == 0
    assert out_csv.exists()
    assert out_json.exists()
    assert out_md.exists()
    assert "SCA Paper-Comparable Benchmark Report" in out_md.read_text(encoding="utf-8")


def test_build_paper_run_manifest_maps_generated_cifs(tmp_path: Path) -> None:
    targets = tmp_path / "targets.csv"
    targets.write_text(
        "benchmark_id,benchmark_group,target_formula,target_structure_family,target_space_group,prompt\n"
        "sanity_nacl,A_validity,NaCl,rocksalt,Fm-3m,Generate NaCl.\n",
        encoding="utf-8",
    )
    generated = tmp_path / "generated"
    generated.mkdir()
    (generated / "challenge_001_nacl_rocksalt_solution.cif").write_text(
        Path("tests/fixtures/tiny_valid.cif").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    out = tmp_path / "generated_manifest.csv"

    frame = build_paper_run_manifest(targets, generated, out)

    assert out.exists()
    assert frame.loc[0, "benchmark_id"] == "sanity_nacl"
    assert frame.loc[0, "attempt_id"] == 1
    assert frame.loc[0, "target_formula"] == "NaCl"
    assert frame.loc[0, "mapping_status"] == "matched"


def test_benchmark_manifest_preserves_paper_metadata(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "cif_path,benchmark_id,benchmark_group,attempt_id,target_formula,target_structure_family,paper_source\n"
        f"{Path('tests/fixtures/tiny_valid.cif').resolve()},sanity_nacl,A_validity,1,NaCl,rocksalt,fixture\n",
        encoding="utf-8",
    )

    records = benchmark_manifest(
        manifest,
        evaluator_names=["pre_dft_validity"],
        formula_col="target_formula",
        method_col="paper_source",
        query_id_col="benchmark_id",
    )

    row = records[0].to_row()
    assert row["benchmark_id"] == "sanity_nacl"
    assert row["benchmark_group"] == "A_validity"
    assert str(row["attempt_id"]) == "1"
    assert row["target_structure_family"] == "rocksalt"
    assert row["target_formula_match"] is True
