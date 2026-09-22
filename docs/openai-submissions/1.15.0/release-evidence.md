# Release evidence and limits

Checked 2026-09-21. No new CI, release, deployment or remote business write was triggered.

| Evidence | Result |
| --- | --- |
| [Plugin release v1.15.0](https://github.com/Memova-ai/memova-codex-plugin/releases/tag/v1.15.0) | Published, exact source `6830a8c0` |
| [Plugin exact-main CI](https://github.com/Memova-ai/memova-codex-plugin/actions/runs/35578922974) | Success, reused unchanged-source evidence |
| [Backend production deployment](https://github.com/Memova-ai/memova/actions/runs/35577393193) | Success at `361b1406`, dual-region release |
| Prior release acceptance | 16 actual Spark messages matched DB in one-page and six-page reads; exact content/order/metadata preserved |
| Fresh initialize | Public MCP reports 1.14.0; mcp-initialize.json |
| Fresh tool discovery | 43 anonymous and 43 authenticated tools; equal name sets; all output schemas present |
| Local manifest/Skill structure | Official plugin-creator validator passed |
| Focused unit regression | 17 public-plugin-boundary cases passed; 0 failed |
| Resource binding validation | Passed against checked-in upstream resource contract |
| Public website/support/privacy/terms | Browser anonymous access successful; raw urllib probes returned 403, not treated as browser failure |
| OAuth metadata | Both authorization-server and protected-resource discovery HTTP 200; login/refresh/revoke NOT tested |
| Source package | 46 tracked files / 10 Skills, byte equality to exact commit; receipt contains size/hash |
| Portal | Login page reached only; identity, domain, current form, scans and prior draft details not inspected |

Historical release details are retained outside the public package at
`~/Documents/Codex/archives/2026-09-21-spark-full-comparison/release.md`. Do not upload its private
MCP/DB receipts or real account content as reviewer fixtures. The previous 132 cross-platform test
executions were explicitly authorized in the release task; they were not repeated here.

## Commands executed for local verification

```sh
python /Users/gxyfred/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/memova
python3 -m unittest discover -s tests -p test_public_plugin_boundary.py -v
python3 plugins/memova/scripts/validate_resource_access_contract.py
python3 docs/openai-submissions/1.15.0/scripts/build_evidence.py
```

The validator used a disposable venv with PyYAML because system/bundled Python lacked it. No project
dependency or user configuration changed. Tool calls were initialize/tools-list only; no production
search, verification update, import, task run, proposal, publication or download grant was invoked.

## Remaining evidence

- Full downstream behavior/annotation and response-field minimization audit; close confirmed findings.
- Supported-host/script-path and final Portal Skill package validation.
- Reviewer credentials, scopes, existing fixture inspection and synthetic account acceptance.
- Source/deployed/Portal catalog parity after any approved repair; use a new patch tag if bytes change.
- Fresh live recording and owner acceptance; current Portal scans and persisted-field audit.

Readiness is **NO-GO for submit**, **GO for preparation and scoped remediation planning**.
