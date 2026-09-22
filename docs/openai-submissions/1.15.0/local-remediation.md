# Authorized local remediation — 2026-09-21

**Implemented and locally validated; not deployed, published, or submitted.** Owner authorized the
three identified fixes and at most 100 targeted cases. No production configuration or rollout changed.

## Source boundaries

- Backend worktree: `/Users/gxyfred/Github/Codex Projects/memova-plugin-submission-contracts`,
  branch `codex/plugin-submission-contract-fixes`, base `fb756f1e` (current main at worktree creation).
- Plugin worktree: `/Users/gxyfred/Github/Codex Projects/memova-plugin-openai-1.15`,
  branch `codex/openai-submission-1.15.0`, base `6830a8c0` (published 1.15.0).
- Changes remain local for review. Primary checkouts and other worktrees were not edited.
- Original catalogs, release receipts and `memova-1.15.0-source-candidate.zip` are immutable historical
  evidence. They do not contain these fixes. Assign a new patch version and regenerate the final
  reviewed package at release time; do not overwrite the 1.15.0 tag or label changed bytes as it.

## Root cause and common contract

1. **Stale retrieval route.** `search_knowledge` uses KnowledgeGraphService; the legacy
   `retrieve_knowledge_context` starts with KnowledgeRetrievalService and only optionally adds V5.
   Both remain gated by legacy graph access. `search_notes` already calls UnifiedSearchService with
   agent purpose and the MCP query surface, and admits V5 only through existing scope/read-rollout
   checks. The absence of the old tools was not evidence that all V5 search was unavailable. The
   incorrect Skill and shared menu route are now aligned with the existing unified entry point.
2. **Lost evidence semantics.** Unified V5 results carried source revision, citation, truncation and
   refusal metadata that `_search_hit_response` discarded. A bounded allowlist now preserves those
   fields for V5 evidence/gate rows, excluding query plans, diagnostics, run IDs and premise internals.
   Ordinary note results are not relabeled. The Skill treats unknown/missing gates conservatively,
   never treats excerpts as complete documents, and refuses unsafe replacement without exact revision
   and sufficient verified before-state.
3. **Implicit annotation default.** `_tool` previously forced every tool to openWorldHint=false.
   External interaction is now a required explicit constructor decision, and Personal Manual
   publication sets it true. Versioned catalogs retain the correction.
4. **Search branch state effect.** Unfiltered resource search records credential verification.
   readOnlyHint is now false for the tool and its description/Skill disclose this effect. The
   verification service, success/failure conditions, scopes and business-object read boundary remain.

This belongs to the existing V5 retrieval/Plugin integration contract (roadmap V5.0 authority and
V5.1 retrieval safety), not a new graph, Fact, grant or model rollout. No gate was enabled or weakened.
The general invariant is that routing, returned evidence and annotations describe actual behavior,
including optional branches. No prompt-specific exception or query-string workaround was added.

## Validation

**76 individual cases passed: 54 backend and 22 Plugin; zero failed or skipped.**

- Backend: 15 new regressions; existing menu, connection verification, selected catalog/discovery,
  scope and unified-search tests. Backend pytest time 6.14 seconds (not production latency).
- Plugin: 17 existing public-boundary checks plus 5 menu checks, including fixed-route behavior in
  English and Chinese. No repeated full suite or CI triggered.
- Holdout coverage: Chinese design query and research query alongside Atlas; conflicting/stale/empty
  gates; notes-only scope; graph disabled; OAuth and Agent Key verification; filtered/unfiltered
  searches; failed discovery; unknown/older metadata. Most runtime dependencies are synthetic mocks;
  this is not fresh production quality or reviewer acceptance evidence.
- Canonical `scripts/dev/validate targeted` also passed compile, full-tree Ruff and paid-callsite
  budget catalog checks. Plugin structural validation and byte-identical backend/bundled menus pass.
- Warnings: two dependency deprecations and pytest cleanup warnings concerning an existing temp
  garbage directory. No test failed; no other task's directory was manually removed or repaired.

Backend targets:

```text
tests/test_mcp_submission_contracts.py
tests/test_memova_menu.py
tests/test_mcp_connection_status.py
tests/test_mcp_protocol.py::test_mcp_tool_catalog_contains_beta_automation_tools
tests/test_mcp_protocol.py::test_public_mcp_catalog_preserves_versioned_plugin_contracts
tests/test_mcp_protocol.py::test_public_mcp_discovery_hides_rollout_disabled_tools
tests/test_mcp_protocol.py::test_authenticated_mcp_discovery_matches_rollout_and_oauth_scope
tests/test_mcp_protocol.py::test_tools_call_rejects_tool_hidden_by_runtime_discovery
tests/test_unified_search.py::test_mcp_search_requires_knowledge_scope_for_graph_provider
```

Machine evidence: local-remediation-validation.json and local-tool-changes.json. No paid model calls,
new provider costs or production latency measurements. No migration or persistent schema change.
The full backend suite was not run because the owner's explicit maximum is 100 cases.

## Remaining release and submission gates

- Review local diffs and create an appropriately versioned patch release through separately authorized
  GitHub/CI/deployment actions. Any CI selection must be counted before triggering; no implicit >100 run.
- After an authorized deployment, verify actual catalog annotations and unified V5 evidence on the
  dedicated synthetic reviewer account. Live 1.15.0 still exposes the pre-fix behavior today.
- Read-only graph gates stay off unless their independent owner-approved roadmap explicitly changes.
- Verify Portal-supported hosts, shared-script upload layout, identity, auth, scans and disclosure
  consistency. Reviewer data writes, real acceptance, video publication, final Submit and Publish
  remain outstanding and independently authorized.
- Replacement/retry/download-grant semantics and broader response minimization remain audit topics;
  these local fixes do not certify every tool or promise zero future review findings.

Rollback of this local candidate means discarding only these reviewed branch diffs. No production
rollback is needed because no deployment occurred. A future release must retain its normal prior
image/tag rollback pointers.
