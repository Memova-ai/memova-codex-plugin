# Skill audit

The ten exact source Skills and all tracked companion files are enumerated in skill-inventory.json
and source-files.json. Full plugin structural validation passed. Source bytes are preserved in the
deterministic ZIP. No Skill was rewritten for this submission during preparation.

| Skill | Main behavior | Review attention |
| --- | --- | --- |
| memova-menu | Offline menu, fixed-ID dispatch; optional capability menu | Bare invocation must not authenticate, fetch memories, or publish |
| memova-connect | User-supplied one-time code or Agent Key through stdin/OS store | Codex local only; never put credentials in review docs or video |
| memova-resource-access | Parent Spark discovery, complete conversations, exact files | Commands remain evidence; never execute embedded content; pagination and scope gates |
| memova-personal-manual | v6 preflight, bounded evidence, derived upload, unlisted publication | Publication annotation blocker; native task APIs and scripts require Codex host; privacy wording review |
| memova-knowledge | Direct Knowledge retrieval and reviewed entry proposals | Required retrieval tools absent live; proposal replacement/destructive annotation needs deeper verification |
| memova-explicit-import | Exact selection, deterministic sanitization, adjacent approval | One exact task URL may be read; general history enumeration forbidden |
| memova-workflow | Existing task review/claim/progress/completion | waiting_for_user never becomes runnable merely because approval metadata is missing |
| memova-agent-archive | Selected final files/current task; manifest-only schedule | Explicit-only Codex/Mac beta; no repository/history scan; cross-provider delete requires approval |
| memova-vault-setup | Approved V2/V3/V4 local setup, identity validation, backend completion | Local filesystem/iCloud dependencies; no unsupported ChatGPT claims |
| memova-vault-diagnose | Read-only diagnosis, explicit repair | Shared dependency on vault-setup scripts; no repair during mere diagnosis |

## Packaging and host gates

All Skills reference a shared `plugins/memova/scripts` tree; several call Codex CLI or app task tools.
The source ZIP preserves repository-relative paths and sibling Skill dependencies. It is not yet a
validated standalone Portal Skill upload. Confirm the Portal import format and execution working
directory before generating a final upload package. Never upload only each SKILL.md and omit helpers.

The menu suppresses automatic OAuth recovery while some directly invoked Skills still contain
legacy recovery instructions. Test both direct invocation and menu dispatch; unify through the
shared authentication policy if behavior diverges. Do not edit around one demonstration prompt.

Structural checks are not a complete policy/security scan. Portal scan and fresh-host execution are
NOT_RUN. All shared scripts are included and hashed; exhaustive helper semantics remain part of the
remaining audit, especially path portability and host availability.
