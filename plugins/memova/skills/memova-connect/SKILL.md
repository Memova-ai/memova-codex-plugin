---
name: memova-connect
description: Connect Memova MCP in Codex using a short-lived one-time Memova Connection Code or a reusable Memova Agent Key, without browser OAuth. Use when the user asks to connect, configure, authenticate, or log in to Memova and supplies an mvc_ Connection Code or mvk_ Agent Key.
---

# Connect Memova MCP

Use this skill only when the user explicitly asks to connect Memova and supplies either a Memova
Connection Code beginning with `mvc_` or an Agent Key beginning with `mvk_`. Never repeat the
credential in chat, logs, a command argument, a file, or a generated artifact.

Before any other step, run `python3 plugins/memova/scripts/version_check.py` from the plugin root.
If it returns `should_remind: true`, show its upgrade message and continue. If the check fails or
returns no reminder, continue silently. Never run the upgrade command without explicit user
confirmation.

## Connection flow

1. Start this helper without putting the credential in the command line:

   ```bash
   python3 plugins/memova/scripts/mcp_connection_auth.py connect
   ```

2. Send the exact credential to that process through standard input once. Do not use `echo`, a
   shell pipe, an environment variable, a temporary file, or command-line arguments for it.
3. The helper accepts only `https://api.memova.ai/mcp`. It stores the resulting credential in the
   operating system credential store and writes only a secret-free `http_headers_helper` command
   to Codex `config.toml`.
4. If the helper returns `connected_client_refresh_required`, tell the user that connection
   succeeded and that Codex must be fully restarted or a new task must be created to reload the MCP
   connection. Do not ask the user to log in again. Surface any returned warning exactly once; in
   particular, existing Codex OAuth credentials can take precedence until the returned logout
   command succeeds.
5. In the refreshed task, perform the user's requested bounded read, such as searching for one
   recent meeting, to verify access. Do not claim that this task can reload its frozen tool catalog.

A Connection Code is consumed once and exchanged for the existing OAuth access/refresh token
family. An Agent Key is reusable until it expires or is revoked. Both currently receive the full
V1 MCP scope set. The helper output and status are safe metadata and never include the credential.

If the code is expired or already used, ask the user to generate one new Connection Code. Do not
fall back to browser OAuth unless the user explicitly chooses the legacy OAuth path. For a safe
local status check, run:

```bash
python3 plugins/memova/scripts/mcp_connection_auth.py status
```

If the environment cannot provide standard input to a running process, tell the user to run the
same `connect` command in a normal system terminal and paste the credential only at the interactive
prompt. Do not weaken storage by writing a static Authorization header.
