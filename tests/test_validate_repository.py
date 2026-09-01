from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_repository


class ValidateRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "plugins").mkdir()
        self.constants = patch.multiple(
            validate_repository,
            ROOT=self.root,
            INDEX_FILE=self.root / "plugin-repository.toml",
            PLUGINS_DIR=self.root / "plugins",
        )
        self.constants.start()

    def tearDown(self) -> None:
        self.constants.stop()
        self.temporary.cleanup()

    def write_index(self, body: str = "") -> None:
        (self.root / "plugin-repository.toml").write_text(
            'schema_version = "1"\nname = "Test Plugins"\n' + body,
            encoding="utf-8",
        )

    def write_plugin(self, plugin_id: str = "demo-plugin") -> Path:
        plugin = self.root / "plugins" / plugin_id
        plugin.mkdir()
        (plugin / "README.md").write_text("# Demo\n", encoding="utf-8")
        (plugin / "LICENSE").write_text("Test license\n", encoding="utf-8")
        (plugin / "extension.toml").write_text(
            "\n".join(
                [
                    "[extension]",
                    f'id = "{plugin_id}"',
                    'name = "Demo Plugin"',
                    'version = "0.1.0"',
                    'api_version = "1"',
                    'description = "Demo"',
                    "",
                    "[resource_namespace]",
                    'prefix = "demo"',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return plugin

    def test_accepts_empty_initial_catalog(self) -> None:
        self.write_index()

        self.assertEqual(validate_repository.main(), 0)

    def test_accepts_indexed_plugin(self) -> None:
        self.write_index(
            '\n[[plugins]]\nid = "demo-plugin"\n'
            'subdirectory = "plugins/demo-plugin"\n'
        )
        self.write_plugin()

        self.assertEqual(validate_repository.main(), 0)

    def test_rejects_manifest_id_mismatch(self) -> None:
        self.write_index(
            '\n[[plugins]]\nid = "demo-plugin"\n'
            'subdirectory = "plugins/demo-plugin"\n'
        )
        plugin = self.write_plugin()
        manifest = plugin / "extension.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                'id = "demo-plugin"', 'id = "other-plugin"'
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_repository.main()

    def test_rejects_unindexed_plugin_directory(self) -> None:
        self.write_index()
        self.write_plugin()

        with self.assertRaisesRegex(ValueError, "missing from catalog"):
            validate_repository.main()

    def test_accepts_resource_path_arrays(self) -> None:
        self.write_index(
            '\n[[plugins]]\nid = "demo-plugin"\n'
            'subdirectory = "plugins/demo-plugin"\n'
        )
        plugin = self.write_plugin()
        resources = plugin / "resources"
        resources.mkdir()
        (resources / "one.json").write_text('{"agents": []}\n', encoding="utf-8")
        (resources / "two.json").write_text('{"agents": []}\n', encoding="utf-8")
        with (plugin / "extension.toml").open("a", encoding="utf-8") as handle:
            handle.write(
                '[resources]\nagents = ["resources/one.json", "resources/two.json"]\n'
            )

        self.assertEqual(validate_repository.main(), 0)

    def test_rejects_reserved_plugin_id(self) -> None:
        self.write_index(
            '\n[[plugins]]\nid = "public-api"\n'
            'subdirectory = "plugins/public-api"\n'
        )
        self.write_plugin("public-api")

        with self.assertRaisesRegex(ValueError, "reserved Plugin id"):
            validate_repository.main()


if __name__ == "__main__":
    unittest.main()
