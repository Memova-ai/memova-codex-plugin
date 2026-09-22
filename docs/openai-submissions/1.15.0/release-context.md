# Release context

## Frozen evidence

| Surface | Verified value | Interpretation |
| --- | --- | --- |
| Plugin | 1.15.0 at `6830a8c0bc06ce87bcd34b3b08e214c5f1763311` | GitHub release and remote main aligned at preparation start |
| Backend release | `361b14063402180650608e7b1cc6bec3e172b748` | Successful production workflow 35577393193 |
| Live MCP | `https://api.memova.ai/mcp`, server contract 1.14.0 | Fresh initialize, 2026-09-21 |
| Public discovery | 43 tools | Anonymous and existing Agent Key catalogs have the same tool names |
| Skills | 10 | Derived from tracked 1.15.0 files |
| Primary plugin checkout | 1.11.0 at `3fd1e15` | Preserved; not a packaging source |
| Submission worktree | branch `codex/openai-submission-1.15.0` | Base pinned to exact 1.15.0 source |
| Prior 1.6.1 review | Manually terminated by owner | User-confirmed 2026-09-21; current Portal details pending login |
| Official published baseline | Unknown | Do not infer from GitHub releases or cancelled review |
| Collector/company-knowledge plugin | Separate products | Not included in this public Memova package |

Plugin and MCP contract versions are independently meaningful; 1.15.0 / 1.14.0 is intentional.

## Delta from the withdrawn 1.6.1 submission

New Skill families: Personal Manual, authorized Agent archive, browser-free connection, and resource
access. Existing menu, explicit import, knowledge, workflow, and legacy vault Skills changed.
Resource access now distinguishes parent Sparks, complete current conversations, and generated
Pages. Complete reads preserve commands, pagination and snapshot consistency. Personal Manual uses
a live v6 contract and at most 20 authorized evidence items; no raw history upload. Agent archive
is explicit-only by default and Codex/Mac beta. Selected imports remain preview-and-confirm.
Knowledge Entry proposals replace the prior legacy proposal workflow. The old knowledge retrieval
claims require reconciliation with today's filtered production catalog.

This is a multi-version submission update, not merely a Spark patch. No historical approval is
claimed for unchanged features. CI can be reused as engineering evidence but not reviewer acceptance.

## Scope and invariant

The public listing, actual account-visible catalog, tool annotations, host capabilities, Skill
instructions and demonstrated behavior must describe the same release. Audit each branch by its
actual reads/writes/publication and required scopes; do not weaken consent or hide errors to pass.
Complete-history Collector, company-public knowledge submission, general SQL/Blob access, bulk
account export, automatic history collection, and unfinished iOS archive convergence are outside scope.

## Official guidance checked

- https://developers.openai.com/plugins/deploy/submission
- https://developers.openai.com/plugins/deploy/app-review

Current documentation calls for at least five positive and three negative cases. Listing and imported
Skill updates require a new version/review/publication. Published MCP tool definitions support
continuous automated review. Actual Portal limits and selected host availability remain to be read.
