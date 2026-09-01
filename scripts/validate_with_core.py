#!/usr/bin/env python3
"""Run DeterminFlow's side-effect-free Plugin preflight for catalog entries."""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    raw_core_root = os.environ.get("DETERMINFLOW_CORE_ROOT", "")
    if not raw_core_root:
        raise SystemExit("DETERMINFLOW_CORE_ROOT is required")
    core_root = Path(raw_core_root).resolve()
    if not (core_root / "src" / "extension_host" / "plugin_preflight.py").is_file():
        raise SystemExit("DETERMINFLOW_CORE_ROOT is not a valid Core checkout")
    sys.path.insert(0, str(core_root))

    from src.extension_host.plugin_preflight import validate_plugin_checkout

    with (ROOT / "plugin-repository.toml").open("rb") as handle:
        document = tomllib.load(handle)
    entries = document.get("plugins", [])
    for entry in entries:
        plugin_id = entry["id"]
        validate_plugin_checkout(plugin_id, ROOT / entry["subdirectory"])
    print(f"Core preflight validated {len(entries)} community Plugin entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
