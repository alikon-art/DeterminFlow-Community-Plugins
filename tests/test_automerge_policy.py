from __future__ import annotations

import unittest

from scripts.automerge_policy import community_pr_automerge_decision


def files(*paths: str, rename: tuple[str, str] | None = None) -> list[dict[str, str]]:
    items = [{"filename": path} for path in paths]
    if rename is not None:
        items.append({"filename": rename[1], "previous_filename": rename[0]})
    return items


class AutomergePolicyTest(unittest.TestCase):
    def test_merges_single_plugin_and_index(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="FIRST_TIME_CONTRIBUTOR",
            files=files(
                "plugin-repository.toml",
                "plugins/demo-plugin/extension.toml",
                "plugins/demo-plugin/README.md",
            ),
        )
        self.assertEqual((action, reason), ("merge", ""))

    def test_skips_infrastructure_paths(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="CONTRIBUTOR",
            files=files(
                "plugin-repository.toml",
                "plugins/demo-plugin/extension.toml",
                ".github/workflows/validate.yml",
            ),
        )
        self.assertEqual((action, reason), ("skip", "paths"))

    def test_skips_multiple_plugin_directories(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="CONTRIBUTOR",
            files=files(
                "plugins/one-plugin/extension.toml",
                "plugins/two-plugin/extension.toml",
            ),
        )
        self.assertEqual((action, reason), ("skip", "single_plugin"))

    def test_skips_index_only_changes(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="CONTRIBUTOR",
            files=files("plugin-repository.toml"),
        )
        self.assertEqual((action, reason), ("skip", "single_plugin"))

    def test_skips_plugins_readme(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="CONTRIBUTOR",
            files=files("plugins/README.md", "plugin-repository.toml"),
        )
        self.assertEqual((action, reason), ("skip", "paths"))

    def test_trusted_maintainer_may_change_infrastructure(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="OWNER",
            files=files(".github/workflows/automerge.yml", "scripts/automerge_policy.py"),
        )
        self.assertEqual((action, reason), ("merge", ""))

    def test_skips_draft_and_conflicts(self) -> None:
        draft_action, draft_reason = community_pr_automerge_decision(
            draft=True,
            merged=False,
            base_ref="main",
            author_association="OWNER",
            files=files("plugins/demo-plugin/extension.toml"),
        )
        conflict_action, conflict_reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="OWNER",
            files=files("plugins/demo-plugin/extension.toml"),
            mergeable_state="dirty",
        )
        self.assertEqual((draft_action, draft_reason), ("skip", "draft"))
        self.assertEqual((conflict_action, conflict_reason), ("skip", "conflict"))

    def test_tracks_renames_within_one_plugin(self) -> None:
        action, reason = community_pr_automerge_decision(
            draft=False,
            merged=False,
            base_ref="main",
            author_association="CONTRIBUTOR",
            files=files(rename=(
                "plugins/demo-plugin/old.md",
                "plugins/demo-plugin/README.md",
            )),
        )
        self.assertEqual((action, reason), ("merge", ""))


if __name__ == "__main__":
    unittest.main()
