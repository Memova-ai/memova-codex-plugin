# Memova 1.15.0 — OpenAI submission preparation

Prepared 2026-09-21. **Preparation in progress; not ready to submit.**

The owner subsequently approved local repairs. See [local remediation](local-remediation.md) for
the corrected candidate; the live catalogs and original ZIP below remain frozen 1.15.0 evidence.

The owner confirmed that the 1.6.1 review was manually terminated during continued development.
It is a historical submitted baseline, not a pending review or an approved baseline.

| Material | Current state |
| --- | --- |
| [Release context](release-context.md) | Candidate and production contract identified |
| [Release evidence](release-evidence.md) | Recent CI/deployment reused; 17 local boundary tests passed |
| [Tool audit](tool-audit.md) / [machine inventory](tool-audit.json) | 43 live tools; blocking discrepancies and further semantic checks recorded |
| [Skill inventory](skill-inventory.md) / [file inventory](skill-inventory.json) | 10 Skills inventoried; source package validated |
| [Listing draft](submission-copy.md) | English copy drafted; public capability claims require reconciliation |
| [Review tests](review-tests.md) | 9 positive / 5 negative scenarios designed; reviewer execution not run |
| [Reviewer fixture](reviewer-fixture.md) | Exact synthetic content and bounded write plan drafted; not seeded |
| [Demo script](demo-script.md) / [QA](demo-qa.md) | Script prepared; no recording made |
| [Portal checklist](portal-checklist.md) | Browser requires login; no Portal mutations |

## Findings in deployed 1.15.0 (local fixes tracked separately)

1. Knowledge search is advertised but `search_knowledge` and `retrieve_knowledge_context` are absent
   from both anonymous and current authenticated production discovery. The direct Knowledge Skill
   cannot currently follow its prescribed path. Investigate rollout and choose a truthful public
   capability scope; do not silently enable production gates or substitute another search contract.
2. `upsert_personal_manual` publishes an anyone-with-link page but advertises `openWorldHint=false`.
   Correct the behavior-derived annotation before rescan/submission.
3. `search_memova_resources` advertises `readOnlyHint=true` but its unfiltered branch persists a
   connection-verification result. Resolve this shared side-effect/annotation contract before scan.
4. Codex-local scripts, OS credential access, and task tools in Skills are not evidence of equivalent
   ChatGPT support. Verify the supported hosts and Portal packaging before claiming universal use.
5. Reviewer credentials, account scopes, fixture readiness, Portal identity/domain state, real
   acceptance, and video remain unverified.

The initial preparation changed no implementation. The subsequent authorized local repairs are
recorded separately. No backend configuration, production business data, Portal draft, published
version, or other session's work was changed. The ZIP is exact source evidence, not a claim that
the Portal will accept that package layout. See package-receipt.json.

## Next action

Continue Portal inspection after login. Local capability/annotation repair approval has been granted; production deployment remains a
separate approval. Run reviewer acceptance
only after an exact synthetic-account write plan is approved. Submit only after all blockers close.

## Successor candidate — 2026-09-22

The corrected release is now prepared as [1.15.1](../1.15.1/README.md). This directory retains original 1.15.0 observations and repair history; its ZIP does not include the fixes.
