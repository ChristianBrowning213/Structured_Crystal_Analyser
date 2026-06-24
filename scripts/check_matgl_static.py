"""Smoke-check MatGL/M3GNet static energy predictions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sca.evaluators.mlip import m3gnet_static_smoke  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MatGL/M3GNet static energy and forces.")
    parser.add_argument("--cif", type=Path, help="Optional CIF to evaluate instead of built-in NaCl.")
    args = parser.parse_args()

    try:
        import matgl
    except Exception as exc:
        print(json.dumps({"ok": False, "error_type": type(exc).__name__, "error_message": str(exc)}, indent=2))
        return 1

    print(f"MatGL version: {getattr(matgl, '__version__', 'unknown')}")
    available_loader = getattr(matgl, "get_available_pretrained_models", None)
    if callable(available_loader):
        try:
            print("Available pretrained models:")
            for name in available_loader():
                print(f"  {name}")
        except Exception as exc:
            print(f"Could not list pretrained models: {type(exc).__name__}: {exc}")
    else:
        print("Available pretrained models: unavailable")

    result = m3gnet_static_smoke(args.cif)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
