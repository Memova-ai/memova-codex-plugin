from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT_PATH = (
    ROOT / "plugins" / "memova" / "scripts" / "validate_resource_access_contract.py"
)
SPEC = importlib.util.spec_from_file_location("resource_access_contract_gate", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
contract_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract_gate)


class ResourceAccessContractGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.binding = contract_gate.load_binding()
        snapshot_path = (
            contract_gate.DEFAULT_BINDING.parent / self.binding["upstream_snapshot"]
        )
        self.provider = json.loads(snapshot_path.read_text(encoding="utf-8"))

    def test_checked_in_snapshot_and_plugin_pass_the_default_gate(self) -> None:
        result = contract_gate.validate_bundle()

        self.assertTrue(result["ok"])
        self.assertEqual(result["provider_contract_version"], "memova_resource_access_v1")
        self.assertEqual(result["minimum_mcp_public_contract_version"], "1.11.0")
        self.assertEqual(result["minimum_plugin_version"], "1.12.0")
        self.assertEqual(result["version_source"], "checked_in_binding")

        helper_constants = contract_gate._tuple_constants(
            contract_gate.PLUGIN_ROOT / "scripts" / "mcp_connection_auth.py"
        )
        self.assertTrue(
            set(self.binding["oauth_workflows"]["resource-download"]).issubset(
                helper_constants["FULL_MCP_SCOPES"]
            )
        )

    def test_explicit_upstream_requires_and_checks_the_public_mcp_version(self) -> None:
        snapshot_path = (
            contract_gate.DEFAULT_BINDING.parent / self.binding["upstream_snapshot"]
        )

        with self.assertRaisesRegex(contract_gate.ContractError, "requires"):
            contract_gate.validate_bundle(upstream_contract=snapshot_path)
        with self.assertRaisesRegex(contract_gate.ContractError, "below the plugin minimum"):
            contract_gate.validate_bundle(
                upstream_contract=snapshot_path,
                upstream_mcp_public_contract_version="1.10.0",
            )

        result = contract_gate.validate_bundle(
            upstream_contract=snapshot_path,
            upstream_mcp_public_contract_version="1.12.0",
        )
        self.assertEqual(result["version_source"], "explicit_upstream")

    def test_provider_surface_drift_fails_closed(self) -> None:
        mutations = {
            "renamed tool": lambda provider: provider["mcp_surface"]["tool_contracts"][0].update(
                name="search_everything"
            ),
            "new resource adapter": lambda provider: provider["resource_adapters"].append(
                copy.deepcopy(provider["resource_adapters"][0])
                | {"resource_type": "future_resource"}
            ),
            "expanded scope": lambda provider: provider["resource_adapters"][0][
                "domain_read_scopes"
            ].append("admin.read"),
            "removed credential family": lambda provider: provider["access_policy"].update(
                credential_types=["oauth"]
            ),
            "changed inline limit": lambda provider: provider["transfer_policy"].update(
                inline_text_max_bytes=100001
            ),
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                provider = copy.deepcopy(self.provider)
                mutate(provider)
                projection = contract_gate.project_provider(provider)
                self.assertNotEqual(projection, self.binding["provider_projection"])

    def test_oauth_workflow_order_and_scope_drift_fails_closed(self) -> None:
        binding = copy.deepcopy(self.binding)
        binding["oauth_workflows"]["resource-read"] = [
            "notes.read",
            "resources.read",
            "sparks.read",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "binding.json"
            path.write_text(json.dumps(binding), encoding="utf-8")
            with self.assertRaisesRegex(contract_gate.ContractError, "gateway and domain scopes"):
                contract_gate.load_binding(path)

        with self.assertRaisesRegex(contract_gate.ContractError, "RESOURCE_READ_SCOPES changed"):
            contract_gate.validate_plugin(binding)

    def test_binding_rejects_snapshot_paths_outside_its_contract_directory(self) -> None:
        cases = {
            "/developer/backend/app/contracts/resource.json": "absolute checkout path",
            "../backend/app/contracts/resource.json": "stay inside",
        }

        for snapshot_path, error in cases.items():
            with self.subTest(snapshot_path=snapshot_path):
                binding = copy.deepcopy(self.binding)
                binding["upstream_snapshot"] = snapshot_path
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = Path(temp_dir) / "binding.json"
                    path.write_text(json.dumps(binding), encoding="utf-8")
                    with self.assertRaisesRegex(contract_gate.ContractError, error):
                        contract_gate.load_binding(path)


if __name__ == "__main__":
    unittest.main()
