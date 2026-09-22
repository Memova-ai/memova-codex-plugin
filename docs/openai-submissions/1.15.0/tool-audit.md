# Tool audit — 43 observed tools

Source: production MCP 1.14.0 catalog plus backend release `361b1406`. TRACED means source routing/behavior reviewed, not full acceptance or official approval. No writes were invoked. Every tool has an output schema, but runtime schema conformance for every reviewer case remains untested.

| Tool | R / D / O hints | Assessment | Behavior / justification draft |
| --- | --- | --- | --- |
| get_personal_manual_generation_contract | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| get_current_personal_manual_generation_contract | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| get_personal_manual_preflight | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| get_personal_manual_status | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| upsert_personal_manual | false/false/false | BLOCKER | Creates a version and publishes or updates an anyone-with-link Personal Manual page. openWorldHint=false contradicts publication; review destructive semantics of replacement separately. |
| import_selected_codex_content | false/false/false | TRACED | Writes the exact approved sanitized selection to durable archive and canonical V5; does not authorize surrounding history or guarantee retrieval rollout. |
| delete_selected_codex_import | false/true/false | TRACED | Deletes one explicitly selected import after adjacent confirmation; destructive=true; idempotency bounds repeated requests. |
| search_notes | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| list_recent_meetings | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| get_note | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| get_transcript | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| list_automation_tasks | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| list_latest_note_automation_tasks | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| claim_task | false/false/false | TRACED | Acquires a bounded task lease and changes task state. |
| get_task_context | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| append_task_progress | false/false/false | TRACED | Appends a task event under the current claim token. |
| create_approval_request | false/false/false | TRACED | Persists an approval request and guarded task transition. |
| list_ready_approvals | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| release_task | false/false/false | TRACED | Releases the claimed task lease; does not grant broader execution authority. |
| complete_task | false/false/false | TRACED | Persists task completion and result under the claim token. |
| fail_task | false/false/false | TRACED | Persists task failure and diagnostic summary. |
| list_pending_knowledge_base_setups | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| get_knowledge_base_setup_context | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| append_knowledge_base_setup_progress | false/false/false | TRACED | Persists setup progress, not merely a read. |
| complete_knowledge_base_setup | false/false/false | TRACED | Completes setup/binding and may enqueue waiting project asset recovery; correctly marked write. |
| fail_knowledge_base_setup | false/false/false | TRACED | Persists setup failure state. |
| create_knowledge_entry_proposal | false/false/false | TRACED | Persists a pending proposal but does not apply canonical knowledge; correctly marked write. |
| get_knowledge_entry_proposal | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| apply_knowledge_entry_proposal | false/false/false | REVIEW | Commits a confirmed create/replace canonical entry under revision/hash guards. destructiveHint=false requires evidence that replacement is normally recoverable; do not assume confirmation removes destructive semantics. |
| reject_knowledge_entry_proposal | false/false/false | TRACED | Persists rejection of one confirmed proposal, not deletion of canonical content. |
| get_llm_wiki_sync_capabilities | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| import_agent_file | false/false/false | TRACED | Creates/updates one authorized final artifact; verify stable ID/hash, revision conflict behavior and normally recoverable replacement semantics. |
| import_codex_task_markdown | false/false/false | TRACED | Imports only the selected current-task Markdown with authorization fields; no task enumeration. |
| get_llm_wiki_sync_status | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| list_llm_wiki_pending_operations | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| retry_llm_wiki_operation | false/false/false | TRACED | Retries one existing selected failed operation and changes processing state; correctly marked write. |
| move_llm_wiki_agent_file | false/true/false | TRACED | Same-provider move or cross-provider copy plus explicitly confirmed source delete; destructive=true covers the deleting branch. |
| search_memova_resources | true/false/false | BLOCKER | Filtered discovery reads bounded resources, but an unfiltered request with domain scopes updates credential verification state and commits. readOnlyHint=true does not cover all branches. |
| get_memova_resource | true/false/false | READ_ROUTE_TRACED | Route reads bounded current-account data or computes contract/capability metadata. Full downstream side-effect audit and reviewer-account result-schema validation remain pending. |
| create_memova_resource_download | true/false/false | REVIEW | Signs a single exact-resource 300-second capability; create_grant has no database write. Rechecks scope/token/lifecycle on redemption. Validate privacy minimization of signed payload and exact host permission semantics; do not call this bulk/public publication. |
| get_memova_menu | true/false/false | TRACED | Builds a capability-filtered menu; does not read note content or authorize workflows. |
| search_sparks | true/false/false | TRACED | Reads bounded parent Sparks and separate generated Page metadata; parent pagination, owner/workspace and lifecycle filtering. |
| get_spark_conversation | true/false/false | TRACED | Reads ordered current messages with cursor/snapshot checks and owner/workspace scopes. Historical commands are data; no generation or modification. |

R = readOnlyHint; D = destructiveHint; O = openWorldHint. All 43 currently advertise O=false; that blanket default is invalid for the confirmed Personal Manual publication branch.

## Required general repairs (proposal only)

- Model annotations per actual tool behavior, including all optional modes and downstream state transitions. Add a focused catalog/side-effect invariant so new publishing tools cannot inherit a private-only default silently.
- For resource verification, choose explicitly between a truthful write annotation and separating the state-changing verification operation from search. Preserve the connection verification guarantee and do not silently remove it to satisfy a scan.
- Reconcile Knowledge retrieval visibility, Skills and listing through the shared capability contract. Do not bypass rollout/cohort or scope protections to make a demo succeed.
- Review replacement/retry/grant semantics and user-data fields before marking their annotations final. Preserve consent, ACLs, revision guards and source identity.

Official reference: https://developers.openai.com/plugins/deploy/app-review#review-and-approval-faqs . Fixes, deployment and Portal rescans have not been performed.
