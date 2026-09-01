#!/usr/bin/env python3
"""Validate the community Plugin catalog without executing Plugin code."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "plugin-repository.toml"
PLUGINS_DIR = ROOT / "plugins"
PLUGIN_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESOURCE_PREFIX = PLUGIN_ID
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ID_LENGTH = 128
RESERVED_PLUGIN_IDS = {
    "bishu-novel",
    "hindsight-memory",
    "novel-teardown",
    "public-api",
}
SUPPORTED_RESOURCE_TYPES = {
    "agents",
    "prompts",
    "skills",
    "skill_bundles",
    "rules",
    "rule_bundles",
    "preset_phrases",
    "workflows",
    "script_libraries",
}
FORBIDDEN_FILENAMES = {
    ".ds_store",
    ".env",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
}
FORBIDDEN_SUFFIXES = {".db", ".key", ".p12", ".pem", ".pfx", ".pyc", ".pyo", ".sqlite", ".sqlite3"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[opusr]_[A-Za-z0-9_]{20,}"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
)


def fail(message: str) -> None:
    raise ValueError(message)


def load_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        fail(f"cannot read valid TOML: {path.relative_to(ROOT)}: {exc}")


def validate_relative_path(raw: object, label: str) -> PurePosixPath:
    if not isinstance(raw, str) or not raw:
        fail(f"{label} must be a non-empty string")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        fail(f"{label} must be a safe relative path")
    if "\\" in raw:
        fail(f"{label} must use forward slashes")
    return path


def require_string(table: dict, key: str, label: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        fail(f"{label}.{key} must be a non-empty string")
    return value.strip()


def validate_string_list(raw: object, label: str) -> list[str]:
    if not isinstance(raw, list) or any(
        not isinstance(item, str) or not item.strip() for item in raw
    ):
        fail(f"{label} must be an array of non-empty strings")
    return [item.strip() for item in raw]


def declared_paths(raw: object, label: str) -> list[tuple[str, PurePosixPath]]:
    values = raw if isinstance(raw, list) else [raw]
    if not values:
        fail(f"{label} cannot be an empty array")
    return [
        (f"{label}[{index}]" if isinstance(raw, list) else label, validate_relative_path(value, label))
        for index, value in enumerate(values)
    ]


def validate_plugin(plugin_id: str, subdirectory: str) -> None:
    plugin_root = ROOT / subdirectory
    if not plugin_root.is_dir():
        fail(f"Plugin directory is missing: {subdirectory}")
    if plugin_root.is_symlink():
        fail(f"Plugin directory cannot be a symlink: {subdirectory}")

    for path in plugin_root.rglob("*"):
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            fail(f"symlinks are not allowed: {relative}")
        if not path.is_file():
            continue
        if path.stat().st_size > MAX_FILE_SIZE:
            fail(f"file exceeds 10 MiB: {relative}")
        lowered_name = path.name.lower()
        if (
            lowered_name in FORBIDDEN_FILENAMES
            or lowered_name.startswith(".env.")
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            fail(f"runtime or secret-like file is not allowed: {relative}")
        if path.stat().st_size <= 2 * 1024 * 1024:
            content = path.read_bytes()
            if any(pattern.search(content) for pattern in SECRET_PATTERNS):
                fail(f"possible secret material is not allowed: {relative}")

    for required in ("extension.toml", "README.md", "LICENSE"):
        required_path = plugin_root / required
        if not required_path.is_file():
            fail(f"{subdirectory}/{required} is required")
        if required_path.stat().st_size == 0:
            fail(f"{subdirectory}/{required} cannot be empty")

    document = load_toml(plugin_root / "extension.toml")
    extension = document.get("extension")
    if not isinstance(extension, dict):
        fail(f"{subdirectory}/extension.toml must contain [extension]")
    if require_string(extension, "id", f"{plugin_id}.extension") != plugin_id:
        fail(f"Plugin id does not match catalog entry: {plugin_id}")
    require_string(extension, "name", f"{plugin_id}.extension")
    require_string(extension, "version", f"{plugin_id}.extension")
    require_string(extension, "description", f"{plugin_id}.extension")
    if require_string(extension, "api_version", f"{plugin_id}.extension") != "1":
        fail(f"{plugin_id}.extension.api_version must be 1")

    dependencies = validate_string_list(
        extension.get("dependencies", []), f"{plugin_id}.extension.dependencies"
    )
    for dependency in dependencies:
        if len(dependency) > MAX_ID_LENGTH or not PLUGIN_ID.fullmatch(dependency):
            fail(f"invalid dependency Plugin id: {dependency}")
    if len(set(dependencies)) != len(dependencies):
        fail(f"{plugin_id}.extension.dependencies cannot contain duplicates")
    validate_string_list(
        extension.get("capabilities", []), f"{plugin_id}.extension.capabilities"
    )

    namespace = document.get("resource_namespace")
    if not isinstance(namespace, dict):
        fail(f"{plugin_id}.resource_namespace is required")
    prefix = require_string(namespace, "prefix", f"{plugin_id}.resource_namespace")
    if len(prefix) > MAX_ID_LENGTH or not RESOURCE_PREFIX.fullmatch(prefix):
        fail(f"invalid resource namespace prefix: {prefix}")

    paths_to_check: list[tuple[str, PurePosixPath]] = []
    resources = document.get("resources")
    if resources is not None:
        if not isinstance(resources, dict):
            fail(f"{plugin_id}.resources must be a table")
        unknown = sorted(set(resources) - SUPPORTED_RESOURCE_TYPES)
        if unknown:
            fail(f"unsupported resource types: {', '.join(unknown)}")
        for key, value in resources.items():
            paths_to_check.extend(
                declared_paths(value, f"{plugin_id}.resources.{key}")
            )
    installation = document.get("installation")
    if installation is not None:
        if not isinstance(installation, dict):
            fail(f"{plugin_id}.installation must be a table")
        if "requirements" in installation:
            paths_to_check.extend(
                declared_paths(
                    installation["requirements"],
                    f"{plugin_id}.installation.requirements",
                )
            )
    settings = document.get("settings")
    if settings is not None:
        if not isinstance(settings, dict):
            fail(f"{plugin_id}.settings must be a table")
        if "schema" in settings:
            paths_to_check.extend(
                declared_paths(settings["schema"], f"{plugin_id}.settings.schema")
            )

    page = document.get("page")
    if page is not None:
        if not isinstance(page, dict):
            fail(f"{plugin_id}.page must be a table")
        static_dir = validate_relative_path(
            page.get("static_dir"), f"{plugin_id}.page.static_dir"
        )
        entrypoint = validate_relative_path(
            page.get("entrypoint", "index.html"), f"{plugin_id}.page.entrypoint"
        )
        static_root = plugin_root.joinpath(*static_dir.parts)
        if not static_root.is_dir():
            fail(f"declared page directory does not exist: {static_dir}")
        if not static_root.joinpath(*entrypoint.parts).is_file():
            fail(f"declared page entrypoint does not exist: {static_dir / entrypoint}")

    processes = document.get("processes", [])
    if not isinstance(processes, list):
        fail(f"{plugin_id}.processes must be an array of tables")
    for index, process in enumerate(processes):
        if not isinstance(process, dict):
            fail(f"{plugin_id}.processes[{index}] must be a table")
        working_directory = validate_relative_path(
            process.get("working_directory", "."),
            f"{plugin_id}.processes[{index}].working_directory",
        )
        if working_directory.as_posix() != "." and not plugin_root.joinpath(
            *working_directory.parts
        ).is_dir():
            fail(f"process working directory does not exist: {working_directory}")

    for label, path in paths_to_check:
        target = plugin_root.joinpath(*path.parts)
        if not target.exists():
            fail(f"declared path does not exist: {label}={path}")


def main() -> int:
    document = load_toml(INDEX_FILE)
    if document.get("schema_version") != "1":
        fail("plugin-repository.toml schema_version must be 1")
    require_string(document, "name", "repository")
    entries = document.get("plugins", [])
    if not isinstance(entries, list):
        fail("plugin-repository.toml plugins must be an array")

    seen: set[str] = set()
    indexed_directories: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            fail("each [[plugins]] entry must be a table")
        plugin_id = entry.get("id")
        if (
            not isinstance(plugin_id, str)
            or len(plugin_id) > MAX_ID_LENGTH
            or not PLUGIN_ID.fullmatch(plugin_id)
        ):
            fail(f"invalid Plugin id: {plugin_id!r}")
        if plugin_id in RESERVED_PLUGIN_IDS or plugin_id.startswith("determinflow-"):
            fail(f"reserved Plugin id: {plugin_id}")
        if plugin_id in seen:
            fail(f"duplicate Plugin id: {plugin_id}")
        seen.add(plugin_id)
        subdirectory = validate_relative_path(entry.get("subdirectory"), f"{plugin_id}.subdirectory").as_posix()
        expected = f"plugins/{plugin_id}"
        if subdirectory != expected:
            fail(f"{plugin_id}.subdirectory must be {expected}")
        indexed_directories.add(subdirectory)
        validate_plugin(plugin_id, subdirectory)

    discovered = {
        path.parent.relative_to(ROOT).as_posix()
        for path in PLUGINS_DIR.glob("*/extension.toml")
    }
    unindexed = sorted(discovered - indexed_directories)
    if unindexed:
        fail(f"Plugin directories missing from catalog: {', '.join(unindexed)}")

    print(f"validated {len(entries)} community Plugin entries")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
