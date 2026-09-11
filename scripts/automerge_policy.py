"""Decide whether a community Plugin pull request may be merged automatically."""

from __future__ import annotations

from typing import Iterable, Mapping


TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
ALLOWED_INDEX = "plugin-repository.toml"
DEFAULT_BASE = "main"


def changed_paths(files: Iterable[Mapping[str, object]]) -> list[str]:
    paths: list[str] = []
    for item in files:
        filename = item.get("filename")
        if isinstance(filename, str) and filename:
            paths.append(filename)
        previous = item.get("previous_filename")
        if isinstance(previous, str) and previous:
            paths.append(previous)
    return paths


def plugin_directory_id(path: str) -> str | None:
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "plugins" and parts[1]:
        return parts[1]
    return None


def community_pr_automerge_decision(
    *,
    draft: bool,
    merged: bool,
    base_ref: str,
    author_association: str,
    files: Iterable[Mapping[str, object]],
    mergeable_state: str = "",
) -> tuple[str, str]:
    """Return ('merge', '') or ('skip', reason)."""
    if merged:
        return "skip", "already_merged"
    if draft:
        return "skip", "draft"
    if base_ref != DEFAULT_BASE:
        return "skip", "base"
    if mergeable_state == "dirty":
        return "skip", "conflict"
    if author_association in TRUSTED_ASSOCIATIONS:
        return "merge", ""

    plugin_ids: set[str] = set()
    has_plugin_file = False
    for path in changed_paths(files):
        if path == ALLOWED_INDEX:
            continue
        plugin_id = plugin_directory_id(path)
        if plugin_id is None:
            return "skip", "paths"
        plugin_ids.add(plugin_id)
        has_plugin_file = True
    if len(plugin_ids) != 1 or not has_plugin_file:
        return "skip", "single_plugin"
    return "merge", ""
