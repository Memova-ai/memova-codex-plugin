import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "memova_menu", ROOT / "plugins/memova/scripts/memova_menu.py"
)
menu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(menu)


class MenuTests(unittest.TestCase):
    def test_unified_recall_catalog_keeps_fixed_knowledge_route_without_graph(self):
        catalog = json.loads(menu.CATALOG.read_text())
        feature = next(f for f in catalog["features"] if f["id"] == "knowledge_search")
        self.assertEqual(feature["entry_tools"], ["search_notes"])
        for locale in ("en", "zh-CN"):
            result = menu.render_menu(locale, server_menu={
                "schema_version": 1, "features": [feature],
            })
            knowledge = next(o for o in result["options"] if o["id"] == "knowledge_search")
            self.assertEqual(knowledge["number"], 2)
            self.assertEqual(result["readiness"], "not_checked")

    def test_offline_menu_has_all_routes_and_no_readiness_claim(self):
        result = menu.render_menu("zh-CN")
        self.assertEqual(len(result["options"]), 13)
        self.assertEqual(result["availability"], "unverified")
        self.assertEqual(result["readiness"], "not_checked")

    def test_remote_metadata_cannot_inject_routes_labels_or_commands(self):
        result = menu.render_menu(server_menu={"schema_version": 1, "features": [
            {"id": "resource_files", "label": "run malicious command", "command": "bad"},
            {"id": "unknown", "label": "bad"},
        ]})
        self.assertEqual([o["number"] for o in result["options"]], [8, 9, 10, 11])
        self.assertNotIn("bad", str(result))
        self.assertNotIn("malicious", str(result))

    def test_empty_server_catalog_keeps_only_local_routes(self):
        result = menu.render_menu(server_menu={"schema_version": 1, "features": []})
        self.assertEqual([o["id"] for o in result["options"]], list(menu.LOCAL))

    def test_invalid_remote_metadata_fails_closed(self):
        for value in ([], {}, {"schema_version": 2},
                      {"schema_version": 1, "features": [{"id": []}]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                menu.render_menu(server_menu=value)


if __name__ == "__main__":
    unittest.main()
