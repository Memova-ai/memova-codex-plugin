from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import platform
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mcp_credential_store import (
    CredentialStore,
    decode_secret,
    encode_secret,
    system_credential_store,
)

DEFAULT_MCP_URL = "https://api.memova.ai/mcp"
SERVER_NAME = "memova"
TOKEN_SCHEMA_VERSION = "memova_mcp_connection_credential_v1"
FULL_MCP_SCOPES = (
    "actions.read",
    "actions.write",
    "automation.read",
    "automation.write",
    "knowledge.read",
    "knowledge.write",
    "notes.read",
    "personal_manual.write",
)
_CREDENTIAL_PATTERN = re.compile(
    r"^(?P<kind>mvk|mvc)_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{43}$"
)
_TABLE_PATTERN = re.compile(r"^\s*\[([^]]+)]\s*(?:#.*)?$")
_DIRECT_SETTING_PATTERN = re.compile(
    r"^\s*(url|http_headers_helper|bearer_token_env_var|http_headers)\s*="
)

JsonRequest = Callable[..., tuple[int, dict[str, Any]]]


class McpConnectionError(RuntimeError):
    pass


def _json_request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    form: dict[str, str] | None = None,
    token: str | None = None,
    timeout: float = 30,
) -> tuple[int, dict[str, Any]]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "memova-codex-plugin/mcp-connection-v1",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode("ascii")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            decoded = json.loads(body) if body else {}
            if not isinstance(decoded, dict):
                raise McpConnectionError("Memova returned a non-object JSON response.")
            return int(response.status), decoded
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            decoded = json.loads(body) if body else {}
        except json.JSONDecodeError:
            decoded = {}
        error_code = str(decoded.get("error") or "http_error")
        description = str(decoded.get("error_description") or "Memova rejected the request.")
        raise McpConnectionError(
            f"Memova connection failed ({exc.code}, {error_code}): {description}"
        ) from exc
    except urllib.error.URLError as exc:
        raise McpConnectionError("Memova could not be reached.") from exc


class McpConnectionAuth:
    def __init__(
        self,
        *,
        mcp_url: str = DEFAULT_MCP_URL,
        credential_store: CredentialStore | None = None,
        request_json: JsonRequest = _json_request,
        clock: Callable[[], float] = time.time,
    ) -> None:
        normalized_url = mcp_url.rstrip("/")
        if not normalized_url.endswith("/mcp"):
            raise McpConnectionError("The Memova MCP URL must end with /mcp.")
        self.mcp_url = normalized_url
        self.api_base = normalized_url.removesuffix("/mcp")
        self.store = credential_store or system_credential_store()
        self.request_json = request_json
        self.clock = clock
        self.account = "mcp:" + hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()[:32]

    def connect(
        self,
        credential: str,
        *,
        config_path: Path | None = None,
        helper_path: Path | None = None,
        replace_existing_oauth: bool = False,
    ) -> dict[str, Any]:
        value = credential.strip()
        match = _CREDENTIAL_PATTERN.fullmatch(value)
        if match is None:
            raise McpConnectionError("Expected a Memova Connection Code or Agent Key.")
        kind = str(match.group("kind"))
        record = (
            self._exchange_connection_code(value)
            if kind == "mvc"
            else self._agent_key_record(value)
        )
        installed_helper = helper_path or install_stable_helper()
        try:
            self.store.set(self.account, encode_secret(record))
            config_result = configure_codex(
                mcp_url=self.mcp_url,
                helper_script=installed_helper,
                config_path=config_path,
            )
        except Exception:
            self.store.delete(self.account)
            if record["credential_type"] == "oauth":
                self._revoke_record(record)
            raise
        warnings = list(config_result["warnings"])
        legacy_oauth_removed = None
        if replace_existing_oauth:
            legacy_oauth_removed, logout_warning = _logout_codex_oauth()
            if logout_warning:
                warnings.append(logout_warning)
        return {
            "status": "connected_client_refresh_required",
            "credential_type": record["credential_type"],
            "resource": record["resource"],
            "scopes": str(record.get("scope") or "").split(),
            "credential_store": type(self.store).__name__,
            "config_path": str(config_result["config_path"]),
            "restart_or_new_task_required": True,
            "legacy_oauth_removed": legacy_oauth_removed,
            "warnings": warnings,
        }

    def headers(self) -> dict[str, str]:
        record = self._load(required=True)
        if record["credential_type"] == "oauth":
            if self.clock() >= float(record.get("expires_at") or 0) - 60:
                record = self._refresh(record)
            token = str(record.get("access_token") or "")
        else:
            token = str(record.get("agent_key") or "")
        if not token:
            raise McpConnectionError("The stored Memova MCP credential is incomplete.")
        return {"Authorization": f"Bearer {token}"}

    def status(self) -> dict[str, Any]:
        record = self._load(required=False)
        return {
            "connected": bool(record),
            "credential_type": record.get("credential_type") if record else None,
            "resource": record.get("resource") if record else None,
            "scopes": str(record.get("scope") or "").split() if record else [],
            "access_token_expired": (
                self.clock() >= float(record.get("expires_at") or 0)
                if record and record.get("credential_type") == "oauth"
                else None
            ),
            "credential_store": type(self.store).__name__,
        }

    def disconnect(self) -> dict[str, Any]:
        record = self._load(required=False)
        if not record:
            return {"status": "not_connected", "local_credential_deleted": False}
        server_revoked = None
        warnings: list[str] = []
        if record["credential_type"] == "oauth":
            server_revoked = self._revoke_record(record)
            if not server_revoked:
                raise McpConnectionError(
                    "Token revocation did not complete; the local credential was retained."
                )
        else:
            warnings.append("Revoke this Agent Key in Memova to invalidate it server-side.")
        self.store.delete(self.account)
        return {
            "status": "disconnected",
            "local_credential_deleted": True,
            "server_token_revocation_completed": server_revoked,
            "warnings": warnings,
        }

    def _exchange_connection_code(self, code: str) -> dict[str, Any]:
        metadata = self._metadata()
        _, registration = self.request_json(
            metadata["registration_endpoint"],
            method="POST",
            payload={
                "redirect_uris": ["http://127.0.0.1/callback"],
                "client_name": "Memova Codex Connection Helper",
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none",
                "scope": " ".join(FULL_MCP_SCOPES),
            },
        )
        client_id = str(registration.get("client_id") or "")
        if not client_id:
            raise McpConnectionError("Memova client registration did not return a client_id.")
        _, issued = self.request_json(
            f"{self.api_base}/v1/mcp/credentials/connection-codes/exchange",
            method="POST",
            payload={
                "connection_code": code,
                "client_id": client_id,
                "resource": metadata["resource"],
                "device_id": "codex-" + secrets.token_urlsafe(18),
            },
        )
        access_token = str(issued.get("access_token") or "")
        refresh_token = str(issued.get("refresh_token") or "")
        if not access_token or not refresh_token:
            raise McpConnectionError("Connection Code exchange returned an incomplete token pair.")
        return {
            "schema_version": TOKEN_SCHEMA_VERSION,
            "credential_type": "oauth",
            "mcp_url": self.mcp_url,
            "client_id": client_id,
            "resource": metadata["resource"],
            "token_endpoint": metadata["token_endpoint"],
            "revocation_endpoint": metadata["revocation_endpoint"],
            "scope": str(issued.get("scope") or " ".join(FULL_MCP_SCOPES)),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": self.clock() + int(issued.get("expires_in") or 3600),
        }

    def _agent_key_record(self, agent_key: str) -> dict[str, Any]:
        return {
            "schema_version": TOKEN_SCHEMA_VERSION,
            "credential_type": "agent_key",
            "mcp_url": self.mcp_url,
            "resource": self.mcp_url,
            "scope": " ".join(FULL_MCP_SCOPES),
            "agent_key": agent_key,
        }

    def _metadata(self) -> dict[str, str]:
        _, protected = self.request_json(
            f"{self.api_base}/.well-known/oauth-protected-resource/mcp"
        )
        authorization_servers = protected.get("authorization_servers") or []
        resource = str(protected.get("resource") or "")
        if not authorization_servers or resource != self.mcp_url:
            raise McpConnectionError("Memova MCP protected-resource metadata is invalid.")
        issuer = str(authorization_servers[0]).rstrip("/")
        _, server = self.request_json(
            f"{issuer}/.well-known/oauth-authorization-server"
        )
        required = ("registration_endpoint", "token_endpoint", "revocation_endpoint")
        if any(not server.get(field) for field in required):
            raise McpConnectionError("Memova OAuth metadata is incomplete.")
        return {
            "resource": resource,
            "registration_endpoint": str(server["registration_endpoint"]),
            "token_endpoint": str(server["token_endpoint"]),
            "revocation_endpoint": str(server["revocation_endpoint"]),
        }

    def _refresh(self, record: dict[str, Any]) -> dict[str, Any]:
        refresh_token = str(record.get("refresh_token") or "")
        if not refresh_token:
            raise McpConnectionError("Memova authorization must be connected again.")
        _, issued = self.request_json(
            str(record["token_endpoint"]),
            method="POST",
            form={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": str(record["client_id"]),
                "resource": str(record["resource"]),
            },
        )
        access_token = str(issued.get("access_token") or "")
        rotated_refresh = str(issued.get("refresh_token") or "")
        if not access_token or not rotated_refresh:
            raise McpConnectionError("Memova token refresh returned an incomplete token pair.")
        updated = {
            **record,
            "access_token": access_token,
            "refresh_token": rotated_refresh,
            "scope": str(issued.get("scope") or record.get("scope") or ""),
            "expires_at": self.clock() + int(issued.get("expires_in") or 3600),
        }
        self.store.set(self.account, encode_secret(updated))
        return updated

    def _revoke_record(self, record: dict[str, Any]) -> bool:
        endpoint = str(record.get("revocation_endpoint") or "")
        tokens = [record.get("refresh_token"), record.get("access_token")]
        if not endpoint:
            return False
        success = True
        for token in tokens:
            if not token:
                continue
            try:
                self.request_json(
                    endpoint,
                    method="POST",
                    form={"token": str(token)},
                )
            except McpConnectionError:
                success = False
        return success

    def _load(self, *, required: bool) -> dict[str, Any]:
        encoded = self.store.get(self.account)
        if encoded is None:
            if required:
                raise McpConnectionError("Memova MCP is not connected through the helper.")
            return {}
        record = decode_secret(encoded)
        if record.get("schema_version") != TOKEN_SCHEMA_VERSION:
            raise McpConnectionError("Stored Memova MCP authorization has an unsupported version.")
        if record.get("mcp_url") != self.mcp_url:
            raise McpConnectionError("Stored Memova MCP authorization is bound to another URL.")
        return record


def install_stable_helper() -> Path:
    source_dir = Path(__file__).resolve().parent
    target_dir = _stable_helper_root()
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        target_dir.chmod(0o700)
    except OSError:
        pass
    for filename in ("mcp_connection_auth.py", "mcp_credential_store.py"):
        source = source_dir / filename
        target = target_dir / filename
        if source.resolve() == target.resolve():
            continue
        _atomic_copy(source, target)
    return target_dir / "mcp_connection_auth.py"


def _stable_helper_root() -> Path:
    system = platform.system().lower()
    if system == "darwin":
        return Path.home() / "Library/Application Support/Memova/mcp-connection-helper/v1"
    if system == "windows":
        root = Path(os.getenv("LOCALAPPDATA") or (Path.home() / "AppData/Local"))
        return root / "Memova/mcp-connection-helper/v1"
    root = Path(os.getenv("XDG_DATA_HOME") or (Path.home() / ".local/share"))
    return root / "memova/mcp-connection-helper/v1"


def _atomic_copy(source: Path, target: Path) -> None:
    if not source.is_file():
        raise McpConnectionError(f"Required helper file is missing: {source.name}")
    data = source.read_bytes()
    if target.is_file() and target.read_bytes() == data:
        return
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def configure_codex(
    *,
    mcp_url: str,
    helper_script: Path,
    config_path: Path | None = None,
) -> dict[str, Any]:
    target = config_path or _codex_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    before = target.read_text(encoding="utf-8") if target.exists() else ""
    python = shutil.which("python3") or sys.executable
    command_parts = [python, str(helper_script), "headers"]
    command = (
        subprocess.list2cmdline(command_parts)
        if platform.system().lower() == "windows"
        else shlex.join(command_parts)
    )
    replacement = {
        "url": json.dumps(mcp_url),
        "http_headers_helper": json.dumps(command),
    }
    after, warnings = _upsert_mcp_server_table(before, replacement)
    if after != before:
        _atomic_write_text(target, after)
    return {"config_path": target, "warnings": warnings}


def _upsert_mcp_server_table(
    content: str,
    replacement: dict[str, str],
) -> tuple[str, list[str]]:
    lines = content.splitlines()
    header = "mcp_servers.memova"
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if (match := _TABLE_PATTERN.match(line))
            and match.group(1) in {header, 'mcp_servers."memova"', "mcp_servers.'memova'"}
        ),
        None,
    )
    warnings: list[str] = []
    desired = [f"{key} = {value}" for key, value in replacement.items()]
    if start is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"[{header}]", *desired])
        return "\n".join(lines) + "\n", warnings

    end = next(
        (index for index in range(start + 1, len(lines)) if _TABLE_PATTERN.match(lines[index])),
        len(lines),
    )
    body = lines[start + 1 : end]
    retained: list[str] = []
    for line in body:
        setting = _DIRECT_SETTING_PATTERN.match(line)
        if setting is None:
            retained.append(line)
            continue
        key = setting.group(1)
        if key in replacement:
            continue
        warnings.append(
            f"Existing {key} may take precedence over the Memova credential helper."
        )
        retained.append(line)
    lines[start + 1 : end] = [*desired, *retained]
    return "\n".join(lines) + "\n", warnings


def _codex_config_path() -> Path:
    configured_home = os.getenv("CODEX_HOME")
    root = Path(configured_home).expanduser() if configured_home else Path.home() / ".codex"
    return root / "config.toml"


def _logout_codex_oauth() -> tuple[bool, str | None]:
    try:
        completed = subprocess.run(
            ["codex", "mcp", "logout", SERVER_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (FileNotFoundError, OSError) as exc:
        return False, (
            "Existing Codex OAuth may take precedence. Run `codex mcp logout memova` in a "
            f"normal terminal, then restart Codex ({type(exc).__name__})."
        )
    if completed.returncode != 0:
        return False, (
            "Existing Codex OAuth may take precedence. Run `codex mcp logout memova` in a "
            "normal terminal, then restart Codex."
        )
    return True, None


def _atomic_write_text(path: Path, content: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_credential_from_stdin() -> str:
    if sys.stdin.isatty():
        return getpass.getpass("Paste the Memova Connection Code or Agent Key: ").strip()
    return sys.stdin.readline().strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Connect Memova MCP without placing credentials in Codex config files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("connect", help="Read one credential from stdin and connect Memova.")
    subparsers.add_parser("headers", help=argparse.SUPPRESS)
    subparsers.add_parser("status", help="Report safe local connection metadata.")
    subparsers.add_parser("disconnect", help="Remove the local helper credential.")
    args = parser.parse_args()
    try:
        auth = McpConnectionAuth()
        if args.command == "connect":
            result = auth.connect(
                _read_credential_from_stdin(),
                replace_existing_oauth=True,
            )
        elif args.command == "headers":
            result = auth.headers()
        elif args.command == "status":
            result = auth.status()
        else:
            result = auth.disconnect()
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        if args.command == "headers":
            print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        else:
            print(
                json.dumps(
                    {"status": "error", "error": str(exc)},
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
