from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).parents[1]
SCRIPT_DIR = ROOT / "plugins" / "memova" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from mcp_connection_auth import (
    DEFAULT_MCP_URL,
    FULL_MCP_SCOPES,
    TOKEN_SCHEMA_VERSION,
    McpConnectionAuth,
    McpConnectionError,
    _logout_codex_oauth,
    _read_credential_from_stdin,
    _upsert_mcp_server_table,
)
from mcp_credential_store import (
    MemoryCredentialStore,
    decode_secret,
    encode_secret,
)


class McpConnectionAuthTests(unittest.TestCase):
    def test_agent_key_connects_without_writing_the_secret_to_codex_config(self) -> None:
        key = f"mvk_{'A' * 16}_{'B' * 43}"
        store = MemoryCredentialStore()
        auth = McpConnectionAuth(credential_store=store)
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Path(temp_dir) / "config.toml"
            result = auth.connect(
                key,
                config_path=config,
                helper_path=SCRIPT_DIR / "mcp_connection_auth.py",
            )
            configured = config.read_text(encoding="utf-8")

        self.assertEqual(result["credential_type"], "agent_key")
        self.assertTrue(result["restart_or_new_task_required"])
        self.assertNotIn(key, configured)
        self.assertIn('url = "https://api.memova.ai/mcp"', configured)
        self.assertIn("http_headers_helper", configured)
        self.assertEqual(auth.headers(), {"Authorization": f"Bearer {key}"})

    def test_connection_code_is_exchanged_and_is_not_retained(self) -> None:
        code = f"mvc_{'A' * 16}_{'B' * 43}"
        calls: list[tuple[str, dict]] = []

        def request_json(url: str, **kwargs):
            calls.append((url, kwargs))
            if url.endswith("/.well-known/oauth-protected-resource/mcp"):
                return 200, {
                    "resource": DEFAULT_MCP_URL,
                    "authorization_servers": ["https://api.memova.ai"],
                }
            if url.endswith("/.well-known/oauth-authorization-server"):
                return 200, {
                    "registration_endpoint": "https://api.memova.ai/v1/mcp/oauth/register",
                    "token_endpoint": "https://api.memova.ai/v1/mcp/oauth/token",
                    "revocation_endpoint": "https://api.memova.ai/v1/mcp/oauth/revoke",
                }
            if url.endswith("/register"):
                self.assertEqual(
                    set(kwargs["payload"]["scope"].split()),
                    set(FULL_MCP_SCOPES),
                )
                self.assertTrue(
                    {"resources.read", "resources.export", "sparks.read"}.issubset(
                        FULL_MCP_SCOPES
                    )
                )
                return 201, {"client_id": "registered-client"}
            if url.endswith("/connection-codes/exchange"):
                self.assertEqual(kwargs["payload"]["connection_code"], code)
                self.assertEqual(kwargs["payload"]["resource"], DEFAULT_MCP_URL)
                return 200, {
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                    "expires_in": 3600,
                    "scope": " ".join(FULL_MCP_SCOPES),
                }
            self.fail(f"unexpected URL: {url}")

        store = MemoryCredentialStore()
        auth = McpConnectionAuth(
            credential_store=store,
            request_json=request_json,
            clock=lambda: 1000,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            result = auth.connect(
                code,
                config_path=Path(temp_dir) / "config.toml",
                helper_path=SCRIPT_DIR / "mcp_connection_auth.py",
            )

        record = decode_secret(next(iter(store.values.values())))
        self.assertEqual(result["credential_type"], "oauth")
        self.assertEqual(record["access_token"], "access-token")
        self.assertEqual(record["refresh_token"], "refresh-token")
        self.assertNotIn(code, json.dumps(record))
        self.assertEqual(len(calls), 4)

    def test_expiring_oauth_token_is_refreshed_and_rotated(self) -> None:
        store = MemoryCredentialStore()
        refresh_calls: list[dict] = []

        def request_json(url: str, **kwargs):
            self.assertEqual(url, "https://api.memova.ai/v1/mcp/oauth/token")
            refresh_calls.append(kwargs)
            return 200, {
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "scope": "notes.read",
            }

        auth = McpConnectionAuth(
            credential_store=store,
            request_json=request_json,
            clock=lambda: 1000,
        )
        store.set(
            auth.account,
            encode_secret(
                {
                    "schema_version": TOKEN_SCHEMA_VERSION,
                    "credential_type": "oauth",
                    "mcp_url": DEFAULT_MCP_URL,
                    "client_id": "client",
                    "resource": DEFAULT_MCP_URL,
                    "token_endpoint": "https://api.memova.ai/v1/mcp/oauth/token",
                    "revocation_endpoint": "https://api.memova.ai/v1/mcp/oauth/revoke",
                    "scope": "notes.read",
                    "access_token": "old-access",
                    "refresh_token": "old-refresh",
                    "expires_at": 1010,
                }
            ),
        )

        headers = auth.headers()

        self.assertEqual(headers, {"Authorization": "Bearer new-access"})
        self.assertEqual(refresh_calls[0]["form"]["refresh_token"], "old-refresh")
        record = decode_secret(store.get(auth.account) or "{}")
        self.assertEqual(record["refresh_token"], "new-refresh")

    def test_unexpired_oauth_token_does_not_refresh(self) -> None:
        store = MemoryCredentialStore()
        request_json = Mock()
        auth = McpConnectionAuth(
            credential_store=store,
            request_json=request_json,
            clock=lambda: 1000,
        )
        store.set(
            auth.account,
            encode_secret(
                {
                    "schema_version": TOKEN_SCHEMA_VERSION,
                    "credential_type": "oauth",
                    "mcp_url": DEFAULT_MCP_URL,
                    "access_token": "current-access",
                    "expires_at": 2000,
                }
            ),
        )

        self.assertEqual(
            auth.headers(),
            {"Authorization": "Bearer current-access"},
        )
        request_json.assert_not_called()

    def test_failed_oauth_revocation_retains_the_local_credential(self) -> None:
        store = MemoryCredentialStore()

        def request_json(url: str, **kwargs):
            del url, kwargs
            raise McpConnectionError("offline")

        auth = McpConnectionAuth(credential_store=store, request_json=request_json)
        store.set(
            auth.account,
            encode_secret(
                {
                    "schema_version": TOKEN_SCHEMA_VERSION,
                    "credential_type": "oauth",
                    "mcp_url": DEFAULT_MCP_URL,
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "revocation_endpoint": "https://api.memova.ai/v1/mcp/oauth/revoke",
                }
            ),
        )

        with self.assertRaises(McpConnectionError):
            auth.disconnect()

        self.assertIsNotNone(store.get(auth.account))

    def test_agent_key_disconnect_warns_about_server_revocation(self) -> None:
        key = f"mvk_{'A' * 16}_{'B' * 43}"
        store = MemoryCredentialStore()
        auth = McpConnectionAuth(credential_store=store)
        store.set(
            auth.account,
            encode_secret(
                {
                    "schema_version": TOKEN_SCHEMA_VERSION,
                    "credential_type": "agent_key",
                    "mcp_url": DEFAULT_MCP_URL,
                    "agent_key": key,
                }
            ),
        )

        result = auth.disconnect()

        self.assertTrue(result["local_credential_deleted"])
        self.assertIn("Revoke this Agent Key", result["warnings"][0])
        self.assertIsNone(store.get(auth.account))

    def test_config_update_preserves_unrelated_values_and_warns_on_precedence(self) -> None:
        before = """model = \"gpt-5.6\"

[mcp_servers.memova]
url = \"https://old.example/mcp\"
bearer_token_env_var = \"MEMOVA_TOKEN\"
startup_timeout_sec = 20

[mcp_servers.other]
url = \"https://other.example/mcp\"
"""

        after, warnings = _upsert_mcp_server_table(
            before,
            {
                "url": json.dumps(DEFAULT_MCP_URL),
                "http_headers_helper": json.dumps("python3 /safe/helper.py headers"),
            },
        )

        self.assertEqual(after.count("[mcp_servers.memova]"), 1)
        self.assertIn(f'url = "{DEFAULT_MCP_URL}"', after)
        self.assertIn("startup_timeout_sec = 20", after)
        self.assertIn("[mcp_servers.other]", after)
        self.assertIn("bearer_token_env_var", warnings[0])

    def test_only_the_canonical_memova_mcp_url_is_the_cli_default(self) -> None:
        with self.assertRaises(McpConnectionError):
            McpConnectionAuth(mcp_url="https://example.com/not-mcp")

        source = (SCRIPT_DIR / "mcp_connection_auth.py").read_text(encoding="utf-8")
        self.assertNotIn('parser.add_argument("--mcp-url"', source)
        self.assertIn('DEFAULT_MCP_URL = "https://api.memova.ai/mcp"', source)

    def test_source_never_accepts_credential_command_arguments(self) -> None:
        source = (SCRIPT_DIR / "mcp_connection_auth.py").read_text(encoding="utf-8")
        self.assertIn("_read_credential_from_stdin", source)
        self.assertNotIn("--connection-code", source)
        self.assertNotIn("--agent-key", source)

    def test_interactive_credential_input_is_not_echoed(self) -> None:
        credential = "mvk_" + "A" * 16 + "_" + "B" * 43
        with (
            patch("mcp_connection_auth.sys.stdin.isatty", return_value=True),
            patch(
                "mcp_connection_auth.getpass.getpass",
                return_value=f"  {credential}  ",
            ) as secure_prompt,
        ):
            value = _read_credential_from_stdin()

        secure_prompt.assert_called_once()
        self.assertEqual(value, credential)

    def test_existing_codex_oauth_logout_uses_no_secret_arguments(self) -> None:
        completed = Mock(returncode=0)
        with patch("mcp_connection_auth.subprocess.run", return_value=completed) as run:
            succeeded, warning = _logout_codex_oauth()

        self.assertTrue(succeeded)
        self.assertIsNone(warning)
        self.assertEqual(run.call_args.args[0], ["codex", "mcp", "logout", "memova"])


if __name__ == "__main__":
    unittest.main()
