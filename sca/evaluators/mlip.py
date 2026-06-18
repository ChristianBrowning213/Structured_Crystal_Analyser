"""Optional MLIP-depth benchmark evaluator skeletons."""

from __future__ import annotations

import os
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from sca.evaluators.cif_parse import parse_cif
from sca.evaluators.chgnet import _extract_energy_per_atom, _extract_forces_max
from sca.schemas import BenchmarkEvaluatorResult


class M3GNetStaticBenchmarkEvaluator:
    name = "m3gnet_static"
    prefix = "m3gnet"
    description = "Optional MatGL/M3GNet static surrogate-energy evaluator."

    def evaluate_path(self, cif_path: str | Path) -> BenchmarkEvaluatorResult:
        structure, parsed = parse_cif(cif_path)
        if structure is None:
            return _mlip_result(self.name, self.prefix, False, "parse failed", parsed.error_message, parsed.error_type)
        try:
            import matgl
            from matgl.ext.pymatgen import Structure2Graph
        except Exception as exc:
            return _mlip_result(self.name, self.prefix, False, "unavailable", str(exc), type(exc).__name__, skipped=True)
        try:
            model = matgl.load_model(os.environ.get("SCA_M3GNET_MODEL", "M3GNet-MP-2021.2.8-PES"))
            graph_converter = Structure2Graph(element_types=model.element_types, cutoff=5.0)
            graph, lattice, state_attr = graph_converter.get_graph(structure)
            prediction = model(graph, lattice, state_attr)
            energy_per_atom = _extract_energy_per_atom({"energy": prediction}, len(structure))
        except Exception as exc:
            return _mlip_result(self.name, self.prefix, False, "failed", str(exc), type(exc).__name__)
        return _mlip_result(self.name, self.prefix, True, "ok", None, None, model=type(model).__name__, energy_per_atom=energy_per_atom)


class MaceStaticBenchmarkEvaluator:
    name = "mace_static"
    prefix = "mace"
    description = "Optional MACE ASE static surrogate-energy evaluator."

    def evaluate_path(self, cif_path: str | Path) -> BenchmarkEvaluatorResult:
        model_path = os.environ.get("SCA_MACE_MODEL")
        if not model_path:
            return _mlip_result(self.name, self.prefix, False, "unavailable", "SCA_MACE_MODEL is not configured", "RuntimeError", skipped=True)
        return _ase_calculator_result(self.name, self.prefix, cif_path, "mace", model_path)


class SevenNetStaticBenchmarkEvaluator:
    name = "sevennet_static"
    prefix = "sevennet"
    description = "Optional SevenNet ASE static surrogate-energy evaluator."

    def evaluate_path(self, cif_path: str | Path) -> BenchmarkEvaluatorResult:
        model_path = os.environ.get("SCA_SEVENNET_MODEL")
        if not model_path:
            return _mlip_result(self.name, self.prefix, False, "unavailable", "SCA_SEVENNET_MODEL is not configured", "RuntimeError", skipped=True)
        return _ase_calculator_result(self.name, self.prefix, cif_path, "sevenn", model_path)


class MlipEnsembleBenchmarkEvaluator:
    name = "mlip_ensemble"
    description = "Consensus and disagreement metrics across available MLIP energy columns."

    def evaluate_row(self, row: dict) -> BenchmarkEvaluatorResult:
        energies = []
        for key in (
            "formation_energy_per_atom",
            "alignn_formation_energy_per_atom",
            "chgnet_energy_per_atom",
            "m3gnet_energy_per_atom",
            "mace_energy_per_atom",
            "sevennet_energy_per_atom",
        ):
            value = _float_or_none(row.get(key))
            if value is not None:
                energies.append(value)
        if len(energies) < 2:
            return BenchmarkEvaluatorResult(
                name=self.name,
                ok=False,
                skipped=True,
                summary="insufficient models",
                metrics={
                    "mlip_energy_mean": mean(energies) if energies else None,
                    "mlip_energy_std": None,
                    "mlip_rank_mean": None,
                    "mlip_rank_variance": None,
                    "mlip_disagreement_flag": None,
                    "mlip_consensus_stable_flag": None,
                },
            )
        energy_mean = mean(energies)
        energy_std = pstdev(energies)
        disagreement = energy_std > float(os.environ.get("SCA_MLIP_DISAGREEMENT_THRESHOLD", "0.5"))
        return BenchmarkEvaluatorResult(
            name=self.name,
            ok=True,
            summary="ok",
            metrics={
                "mlip_energy_mean": energy_mean,
                "mlip_energy_std": energy_std,
                "mlip_rank_mean": None,
                "mlip_rank_variance": None,
                "mlip_disagreement_flag": disagreement,
                "mlip_consensus_stable_flag": energy_mean < 0 and not disagreement,
            },
            flags={
                "mlip_disagreement_flag": disagreement,
                "mlip_consensus_stable_flag": energy_mean < 0 and not disagreement,
            },
        )


def _ase_calculator_result(
    name: str,
    prefix: str,
    cif_path: str | Path,
    module_name: str,
    model_path: str,
) -> BenchmarkEvaluatorResult:
    structure, parsed = parse_cif(cif_path)
    if structure is None:
        return _mlip_result(name, prefix, False, "parse failed", parsed.error_message, parsed.error_type)
    try:
        module = __import__(module_name)
    except Exception as exc:
        return _mlip_result(name, prefix, False, "unavailable", str(exc), type(exc).__name__, skipped=True)
    try:
        from pymatgen.io.ase import AseAtomsAdaptor
        calculator_factory = getattr(module, "MACECalculator", None) or getattr(module, "SevenNetCalculator", None)
        if calculator_factory is None:
            raise RuntimeError(f"No supported ASE calculator found in {module_name}")
        atoms = AseAtomsAdaptor.get_atoms(structure)
        atoms.calc = calculator_factory(model_path=model_path)
        energy_per_atom = float(atoms.get_potential_energy()) / len(atoms)
        forces_max = _extract_forces_max({"forces": atoms.get_forces()})
    except Exception as exc:
        return _mlip_result(name, prefix, False, "failed", str(exc), type(exc).__name__)
    return _mlip_result(name, prefix, True, "ok", None, None, model=model_path, energy_per_atom=energy_per_atom, forces_max=forces_max)


def _mlip_result(
    name: str,
    prefix: str,
    ok: bool,
    summary: str,
    error_message: str | None,
    error_type: str | None,
    skipped: bool = False,
    model: str | None = None,
    energy_per_atom: float | None = None,
    forces_max: float | None = None,
) -> BenchmarkEvaluatorResult:
    return BenchmarkEvaluatorResult(
        name=name,
        ok=ok,
        skipped=skipped,
        model=model,
        summary=summary,
        metrics={
            f"{prefix}_ok": ok,
            f"{prefix}_model": model,
            f"{prefix}_energy_per_atom": energy_per_atom,
            f"{prefix}_forces_max": forces_max,
            f"{prefix}_error": error_message,
        },
        flags={f"{prefix}_ok": ok},
        error_type=error_type,
        error_message=error_message,
    )


def _float_or_none(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

