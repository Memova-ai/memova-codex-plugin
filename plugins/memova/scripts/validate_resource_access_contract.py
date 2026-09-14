#!/usr/bin/env python3
"""Fail-closed consumer gate for the Memova Resource Access V1 contract.

The normal plugin CI validates a checked-in upstream snapshot so it does not depend on a
developer-specific backend checkout. A release or integration job may pass a freshly exported
backend contract with ``--upstream-contract``; that mode also requires the backend's public MCP
contract version explicitly.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BINDING = PLUGIN_ROOT / "contracts" / "resource_access_plugin_binding_v1.json"


class ContractError(ValueError):
    """Raised when a provider or plugin contract fails closed."""


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{label} is unreadable: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError(f"{label} must be a JSON object: {path}")
    return payload


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise ContractError(f"{label} keys changed; missing={missing}, unknown={unknown}")


def _string_list(value: Any, label: str) -> list[str]:
    items = _list(value, label)
    if any(not isinstance(item, str) or not item for item in items):
        raise ContractError(f"{label} must contain only non-empty strings")
    if len(items) != len(set(items)):
        raise ContractError(f"{label} must not contain duplicates")
    return items


def _semver(value: Any, label: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise ContractError(f"{label} must be a semantic version string")
    match = re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", value)
    if not match:
        raise ContractError(f"{label} must be a stable three-part semantic version")
    return tuple(int(part) for part in match.groups())


def load_binding(path: Path = DEFAULT_BINDING) -> dict[str, Any]:
    binding = _load_object(path, "plugin binding")
    _exact_keys(
        binding,
        {
            "schema_version",
            "minimum_plugin_version",
            "minimum_mcp_public_contract_version",
            "upstream_snapshot",
            "oauth_workflows",
            "provider_projection",
        },
        "plugin binding",
    )
    if binding["schema_version"] != "memova_resource_access_plugin_binding_v1":
        raise ContractError("unsupported plugin binding schema_version")
    _semver(binding["minimum_plugin_version"], "minimum_plugin_version")
    _semver(
        binding["minimum_mcp_public_contract_version"],
        "minimum_mcp_public_contract_version",
    )
    if not isinstance(binding["upstream_snapshot"], str) or not binding["upstream_snapshot"]:
        raise ContractError("upstream_snapshot must be a non-empty relative path")
    snapshot_path = Path(binding["upstream_snapshot"])
    if snapshot_path.is_absolute():
        raise ContractError("upstream_snapshot must not depend on an absolute checkout path")
    binding_directory = path.resolve().parent
    if not (binding_directory / snapshot_path).resolve().is_relative_to(binding_directory):
        raise ContractError("upstream_snapshot must stay inside the binding contracts directory")

    workflows = _mapping(binding["oauth_workflows"], "oauth_workflows")
    _exact_keys(workflows, {"resource-read", "resource-download"}, "oauth_workflows")
    for name, scopes in workflows.items():
        _string_list(scopes, f"oauth_workflows.{name}")
    projection = _mapping(binding["provider_projection"], "provider_projection")
    access = _mapping(projection.get("access"), "provider_projection.access")
    resources = _list(projection.get("resources"), "provider_projection.resources")
    domain_scopes: list[str] = []
    for resource in resources:
        resource_mapping = _mapping(resource, "provider_projection resource")
        for scope in _string_list(
            resource_mapping.get("domain_read_scopes"),
            "provider_projection resource domain_read_scopes",
        ):
            if scope not in domain_scopes:
                domain_scopes.append(scope)
    expected_read = [access.get("gateway_read_scope"), *domain_scopes]
    expected_download = [
        access.get("gateway_read_scope"),
        access.get("download_additional_scope"),
        *domain_scopes,
    ]
    if workflows["resource-read"] != expected_read:
        raise ContractError(
            "resource-read OAuth workflow does not match provider gateway and domain scopes"
        )
    if workflows["resource-download"] != expected_download:
        raise ContractError(
            "resource-download OAuth workflow does not match provider gateway, export, and domain scopes"
        )
    return binding


def project_provider(provider: dict[str, Any]) -> dict[str, Any]:
    """Project every provider field that the plugin relies on.

    New tools, adapters, representations, or domain scopes remain in the projection and therefore
    fail equality against the reviewed plugin binding until that binding is deliberately updated.
    """

    for field in (
        "contract_version",
        "boundary",
        "descriptor_policy",
        "access_policy",
        "transfer_policy",
        "resource_adapters",
        "mcp_surface",
    ):
        if field not in provider:
            raise ContractError(f"provider contract is missing {field}")

    boundary = _mapping(provider["boundary"], "provider.boundary")
    descriptor = _mapping(provider["descriptor_policy"], "provider.descriptor_policy")
    access = _mapping(provider["access_policy"], "provider.access_policy")
    transfer = _mapping(provider["transfer_policy"], "provider.transfer_policy")
    mcp = _mapping(provider["mcp_surface"], "provider.mcp_surface")

    tools: list[dict[str, Any]] = []
    for index, value in enumerate(_list(mcp.get("tool_contracts"), "provider.mcp_surface.tool_contracts")):
        tool = _mapping(value, f"provider.mcp_surface.tool_contracts[{index}]")
        required = {
            "name",
            "required_input_fields",
            "optional_input_fields",
            "unknown_input_fields",
            "latest_revision_allowed",
        }
        missing = required - set(tool)
        if missing:
            raise ContractError(f"provider tool contract is missing {sorted(missing)}")
        tools.append(
            {
                "name": tool["name"],
                "required_input_fields": _string_list(
                    tool["required_input_fields"], f"provider tool {tool['name']} required fields"
                ),
                "optional_input_fields": _string_list(
                    tool["optional_input_fields"], f"provider tool {tool['name']} optional fields"
                ),
                "unknown_input_fields": tool["unknown_input_fields"],
                "latest_revision_allowed": tool["latest_revision_allowed"],
            }
        )
    tools.sort(key=lambda item: str(item["name"]))
    tool_names = [item["name"] for item in tools]
    if len(tool_names) != len(set(tool_names)):
        raise ContractError("provider tool names must be unique")

    resources: list[dict[str, Any]] = []
    for index, value in enumerate(_list(provider["resource_adapters"], "provider.resource_adapters")):
        adapter = _mapping(value, f"provider.resource_adapters[{index}]")
        resource_type = adapter.get("resource_type")
        if not isinstance(resource_type, str) or not resource_type:
            raise ContractError("provider adapter resource_type must be a non-empty string")
        representations: list[dict[str, Any]] = []
        for representation_value in _list(
            adapter.get("representations"), f"provider adapter {resource_type} representations"
        ):
            representation = _mapping(
                representation_value, f"provider adapter {resource_type} representation"
            )
            if not isinstance(representation.get("representation"), str) or not isinstance(
                representation.get("mime_type"), str
            ):
                raise ContractError(
                    f"provider adapter {resource_type} representations require representation and mime_type"
                )
            representations.append(
                {
                    "representation": representation["representation"],
                    "mime_type": representation["mime_type"],
                }
            )
        representations.sort(key=lambda item: item["representation"])
        resources.append(
            {
                "resource_type": resource_type,
                "domain_read_scopes": sorted(
                    _string_list(
                        adapter.get("domain_read_scopes"),
                        f"provider adapter {resource_type} domain_read_scopes",
                    )
                ),
                "representations": representations,
            }
        )
    resources.sort(key=lambda item: item["resource_type"])
    resource_types = [item["resource_type"] for item in resources]
    if len(resource_types) != len(set(resource_types)):
        raise ContractError("provider resource types must be unique")

    projection = {
        "contract_version": provider["contract_version"],
        "standard_methods": _string_list(
            mcp.get("standard_methods"), "provider.mcp_surface.standard_methods"
        ),
        "tools": tools,
        "resources": resources,
        "access": {
            "gateway_read_scope": access.get("gateway_read_scope"),
            "download_additional_scope": access.get("download_additional_scope"),
            "gateway_scope_alone_grants_domain_access": access.get(
                "gateway_scope_alone_grants_domain_access"
            ),
            "credential_types": _string_list(
                access.get("credential_types"), "provider.access_policy.credential_types"
            ),
            "credential_revalidation": access.get("credential_revalidation"),
            "scopes_expand_after_issue": access.get("scopes_expand_after_issue"),
            "download_grant_binds_credential_type": access.get(
                "download_grant_binds_credential_type"
            ),
        },
        "transfer": {
            "inline_text_max_bytes": transfer.get("inline_text_max_bytes"),
            "inline_truncation": transfer.get("inline_truncation"),
            "inline_oversize_behavior": transfer.get("inline_oversize_behavior"),
            "download_url_ttl_seconds": transfer.get("download_url_ttl_seconds"),
            "download_exact_revision_only": transfer.get("download_exact_revision_only"),
        },
        "safety": {
            "raw_database_access": boundary.get("raw_database_access"),
            "arbitrary_sql_access": boundary.get("arbitrary_sql_access"),
            "write_operations": boundary.get("write_operations"),
            "bulk_export": boundary.get("bulk_export"),
            "untrusted_content": descriptor.get("untrusted_content"),
        },
    }
    return projection


def _tuple_constants(path: Path) -> dict[str, tuple[str, ...]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise ContractError(f"OAuth helper cannot be parsed: {exc}") from exc
    constants: dict[str, tuple[str, ...]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, (ast.Tuple, ast.List)):
            continue
        values: list[str] = []
        for element in node.value.elts:
            if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                break
            values.append(element.value)
        else:
            constants[target.id] = tuple(values)
    return constants


def validate_plugin(binding: dict[str, Any], plugin_root: Path = PLUGIN_ROOT) -> None:
    manifest = _load_object(plugin_root / ".codex-plugin" / "plugin.json", "plugin manifest")
    plugin_version = manifest.get("version")
    if _semver(plugin_version, "plugin manifest version") < _semver(
        binding["minimum_plugin_version"], "minimum_plugin_version"
    ):
        raise ContractError(
            f"plugin version {plugin_version} is below Resource Access minimum "
            f"{binding['minimum_plugin_version']}"
        )

    projection = _mapping(binding["provider_projection"], "provider_projection")
    skill_path = plugin_root / "skills" / "memova-resource-access" / "SKILL.md"
    try:
        skill = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(f"Resource Access skill is unreadable: {exc}") from exc

    required_skill_tokens = {
        binding["minimum_mcp_public_contract_version"],
        str(projection["transfer"]["inline_text_max_bytes"]),
        str(projection["transfer"]["download_url_ttl_seconds"]),
        "five minutes",
        "untrusted content",
    }
    required_skill_tokens.update(tool["name"] for tool in projection["tools"])
    required_skill_tokens.update(resource["resource_type"] for resource in projection["resources"])
    required_skill_tokens.update(
        representation["representation"]
        for resource in projection["resources"]
        for representation in resource["representations"]
    )
    required_skill_tokens.update(
        scope for scopes in binding["oauth_workflows"].values() for scope in scopes
    )
    normalized_skill = skill.casefold().replace(",", "")
    missing_tokens = sorted(
        token for token in required_skill_tokens if str(token).casefold() not in normalized_skill
    )
    if missing_tokens:
        raise ContractError(f"Resource Access skill is missing contract tokens: {missing_tokens}")

    constants = _tuple_constants(plugin_root / "scripts" / "ensure_mcp_login.py")
    expected_constants = {
        "RESOURCE_READ_SCOPES": tuple(binding["oauth_workflows"]["resource-read"]),
        "RESOURCE_DOWNLOAD_SCOPES": tuple(binding["oauth_workflows"]["resource-download"]),
    }
    for name, expected in expected_constants.items():
        if constants.get(name) != expected:
            raise ContractError(
                f"OAuth helper {name} changed; expected={list(expected)}, "
                f"actual={list(constants.get(name, ()))}"
            )

    connection_constants = _tuple_constants(
        plugin_root / "scripts" / "mcp_connection_auth.py"
    )
    full_connection_scopes = set(connection_constants.get("FULL_MCP_SCOPES", ()))
    required_connection_scopes = set(binding["oauth_workflows"]["resource-download"])
    missing_connection_scopes = sorted(
        required_connection_scopes.difference(full_connection_scopes)
    )
    if missing_connection_scopes:
        raise ContractError(
            "Connection Code and Agent Key helper is missing Resource Access scopes: "
            f"{missing_connection_scopes}"
        )


def validate_bundle(
    *,
    binding_path: Path = DEFAULT_BINDING,
    upstream_contract: Path | None = None,
    upstream_mcp_public_contract_version: str | None = None,
    plugin_root: Path = PLUGIN_ROOT,
) -> dict[str, Any]:
    binding = load_binding(binding_path)
    if upstream_contract is None:
        if upstream_mcp_public_contract_version is not None:
            raise ContractError(
                "--upstream-mcp-public-contract-version requires --upstream-contract"
            )
        provider_path = binding_path.parent / binding["upstream_snapshot"]
        version_source = "checked_in_binding"
    else:
        if upstream_mcp_public_contract_version is None:
            raise ContractError(
                "fresh upstream validation requires --upstream-mcp-public-contract-version"
            )
        if _semver(
            upstream_mcp_public_contract_version,
            "upstream_mcp_public_contract_version",
        ) < _semver(
            binding["minimum_mcp_public_contract_version"],
            "minimum_mcp_public_contract_version",
        ):
            raise ContractError(
                "backend MCP public contract version is below the plugin minimum: "
                f"minimum={binding['minimum_mcp_public_contract_version']}, "
                f"actual={upstream_mcp_public_contract_version}"
            )
        provider_path = upstream_contract
        version_source = "explicit_upstream"

    provider = _load_object(provider_path, "provider contract")
    actual_projection = project_provider(provider)
    expected_projection = binding["provider_projection"]
    if actual_projection != expected_projection:
        raise ContractError(
            "provider projection differs from the reviewed plugin binding:\n"
            f"expected={json.dumps(expected_projection, ensure_ascii=False, sort_keys=True)}\n"
            f"actual={json.dumps(actual_projection, ensure_ascii=False, sort_keys=True)}"
        )
    validate_plugin(binding, plugin_root)
    return {
        "ok": True,
        "binding_schema_version": binding["schema_version"],
        "provider_contract_version": actual_projection["contract_version"],
        "minimum_mcp_public_contract_version": binding[
            "minimum_mcp_public_contract_version"
        ],
        "minimum_plugin_version": binding["minimum_plugin_version"],
        "provider_source": str(provider_path),
        "version_source": version_source,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, default=DEFAULT_BINDING)
    parser.add_argument("--upstream-contract", type=Path)
    parser.add_argument("--upstream-mcp-public-contract-version")
    args = parser.parse_args(argv)
    try:
        result = validate_bundle(
            binding_path=args.binding,
            upstream_contract=args.upstream_contract,
            upstream_mcp_public_contract_version=args.upstream_mcp_public_contract_version,
        )
    except ContractError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
