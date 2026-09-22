# Coordinated 1.15.1 release — execution scope for owner approval

Prepared 2026-09-22. No remote action below has been executed.

## Exact candidate and target

- Plugin: `Memova-ai/memova-codex-plugin`, branch `codex/openai-submission-1.15.0` (historical branch name), source commit `9e699f0`; manifest **1.15.1**, based on released `6830a8c0` / `v1.15.0`. Subsequent preparation-doc commits must preserve this exact plugin tree.
- Backend: `Memova-ai/memova`, branch `codex/plugin-submission-contract-fixes`, commit `27771c1fd6637ac92b5390cf50a4bc9e60fc1539`, base `fb756f1e94d680bfc37249eb64caa1ac7b2605fb`.
- Current successful production baseline: workflow [35585935542](https://github.com/Memova-ai/memova/actions/runs/35585935542), both-region release at `fb756f1e` on 2026-09-21. Recheck live state before release.
- Backend advertises latest Plugin 1.15.1; minimum remains 1.8.2. Public MCP contract stays 1.14.0. No migration, scope grant, feature-gate change or reviewer/customer data mutation is included.

## Verified preparation

Prior fix validation: 54 backend +22 Plugin cases passed. This step added seven CI selection/scope rejection cases and two compatibility checks, all now passing. The first selector test used the wrong dataclass attribute (`mode` instead of `profile`); corrected, repinned and all seven rerun successfully. Compile/Ruff/paid-callsite checks pass. Plugin manifest validation and shared-menu parity pass.

Actual HEAD-to-origin/main backend selector produces the exact nine-file targeted plan in `backend-ci-plan.json`; collection resolves **63 cases**. Prior 54-case evidence is retained; only the nine added/affected cases were executed again as needed. CI will run all 63 against the committed release. Extra files, deletes, renames, unknown bytes or missing coverage do not receive this mapping.

Source ZIP: 46 files, 10 Skills, every byte verified against plugin source commit. It is source evidence, not proof of Portal compatibility or production acceptance.

## Remote actions requested

1. Recheck both remote bases, candidate trees and active CI/deploys. If scope changed or another task is releasing, defer our conflicting action and reassess; never interrupt its run.
2. Push the two reviewed branches and create release PRs using the prepared descriptions. These actions change GitHub and trigger CI.
3. Require successful exact-head CI, review the diffs, then merge each PR only while its reviewed base/scope still matches. Do not force merge, bypass gates or cancel existing workflows.
4. Publish the Plugin GitHub release **v1.15.1** at its verified merge SHA using `release-notes.md`; never move or overwrite v1.15.0. Verify tag, manifest and release afterward.
5. Deploy the reviewed backend merge SHA to **production JPE + US**, using the existing `deploy-prod.yml` with `target_region=both`, `release_mode=normal`, `validation_profile=ci_evidence`, `run_migrations=true`, and default conservative component selection. No new schema changes are present; keep the normal schema preflight. Do not override drain/parity/health checks. A conservative fallback may update additional runtime components; do not manually force their scope narrower.
6. Verify read-only health, compatibility, initialize and tools/list against the deployed release. Do not call unfiltered resource search as a read-only probe; it records verification. Reviewer data setup, acceptance writes and recording require their separate concrete plan.

Representative commands (run from the respective candidate worktrees after approval):

```sh
git push -u origin codex/openai-submission-1.15.0
gh pr create --base main --head codex/openai-submission-1.15.0 --title 'fix(plugin): release 1.15.1 submission contract corrections' --body-file docs/openai-submissions/1.15.1/plugin-pr.md

git push -u origin codex/plugin-submission-contract-fixes
gh pr create --base main --head codex/plugin-submission-contract-fixes --title 'fix(mcp): preserve bounded knowledge evidence and accurate tool annotations' --body-file '/Users/gxyfred/Github/Codex Projects/memova-plugin-openai-1.15/docs/openai-submissions/1.15.1/backend-pr.md'
```

After verified checks, use each returned PR number with `gh pr merge --merge --match-head-commit <verified-head>`. Publish `gh release create v1.15.1 --target <verified-plugin-merge-sha> --title 'Memova 1.15.1' --notes-file docs/openai-submissions/1.15.1/release-notes.md`. Dispatch backend `gh workflow run deploy-prod.yml --ref <verified-backend-merge-sha> -f target_region=both -f release_mode=normal -f validation_profile=ci_evidence -f run_migrations=true`. Resolve placeholders from successful receipts, never guess them.

## Explicit CI scope and cost

The existing Plugin workflow performs **90 Linux +43 Windows =133 cases per run**, including setup fixtures. Its `codex/**` push, PR and main events can produce three runs: **399 case executions**. This exceeds the owner's 100-case default and requires explicit exception approval before the first push. Preserve its coverage; no test-cap change is proposed. Three rounds are expected to take approximately 10–30 minutes of wall time depending on runner queues, with GitHub Actions runner usage; there are no paid model calls in these suites.

Backend CI selects **63 cases per run**; PR + main is at most126 executions (main may reuse exact evidence when the existing gate allows). The production workflow uses successful exact-SHA CI evidence instead of dispatching a full test suite. Stop if collection/scope changes or a different oversized plan is selected. No unbounded retry authorization is requested.

## Effect and rollback

Publishing makes 1.15.1 available through the repository marketplace; production deployment corrects live MCP annotations/evidence and advertises that version. Neither action publishes the Plugin in OpenAI's official directory.

On release failure, stop rollout and preserve diagnostics. Retain production `fb756f1e` and its immutable image receipts for the standard both-region rollback; never reset shared Git history or mutate old tags. The Plugin fallback is the previous `v1.15.0` source/release; any corrective public version should be a new patch. Do not treat deletion of a GitHub release as removal from already updated clients.

Official Portal edits, final Submit, official Publish, reviewer fixture writes, customer data changes and enabling Knowledge rollouts are outside this requested release approval.
