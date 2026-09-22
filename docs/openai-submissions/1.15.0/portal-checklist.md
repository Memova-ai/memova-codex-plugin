# Portal state and entry checklist

2026-09-21: https://platform.openai.com/plugins redirects the in-app browser to login. No new draft,
form save, scan, upload, review cancellation, submission or publication occurred. The owner confirmed
the old 1.6.1 review was cancelled. Do not cancel it again or infer that a public version is absent.

After login, inspect existing Memova entry first. Use its new-version/edit workflow as appropriate;
do not create a duplicate plugin or change the MCP origin without a justified decision.

| Section | Prepared input | Must inspect before entry |
| --- | --- | --- |
| Organization | Website identifies MEMOVA LLC | Matching verified identity, organization/project, Apps Management Write |
| Existing version | Owner says 1.6.1 review terminated | Draft/review/published state, retained fields, new-version flow |
| Info | submission-copy.md + source icons | Actual limits, asset format, supported surfaces |
| MCP | https://api.memova.ai/mcp | Universal URL, domain challenge, OAuth config, demo sign-in |
| Tools | tool-audit.json | Corrected live annotations, catalog scope, scan result |
| Skills | source inventories and ZIP | Exact upload layout, shared helpers, all scans; source ZIP not yet upload-approved |
| Prompts | Three proposed prompts | Current limit and host support |
| Testing | review-tests.md | Actual fields/limits, executed results and reproducible reviewer data |
| Global | Undecided | Owner's intended regions and real service availability |
| Demo | No recording yet | Final accepted public URL, anonymous access |
| Submit | Draft release notes | Accurate attestations, complete persisted-value audit, adjacent owner confirmation |

## Public pages observed through browser

- https://memova.ai/ — homepage loaded anonymously.
- https://memova.ai/support/ — support page loaded, hello@memova.ai, plugin/MCP support guidance.
- https://memova.ai/privacy — policy loaded, last updated August 25, 2026; MEMOVA LLC; user-directed
  sharing and agent permissions disclosed. Manual publication/derived metadata wording needs review.
- https://memova.ai/terms/ — terms loaded, last updated August 25, 2026; MEMOVA LLC.

Raw HTTP probes received 403 on those pages, while the browser succeeded. Validate OpenAI's scan
access when available; do not claim the website is globally inaccessible or weaken site protection.

## Permission boundaries for next steps

Preparation approval covers local documents, source packaging and read-only inspection. The supplied
global AGENTS instructions require explicit approval before moving an identified issue into a fix
or making shared/online changes. The canonical release process also says: “stop immediately before
the final submission action and obtain adjacent owner confirmation.”

Proposed next local work: isolated branch changes to the shared behavior-to-annotation contract and
capability routing/copy, with targeted regression plus diverse holdout under 100 cases. No production
configuration/deployment or Portal save is bundled into that approval. Any source change invalidates
the exact 1.15.0 package as final upload material; prepare a new patch release and preserve old tags.

For eventual fixture writes, first resolve exact account/objects/endpoints and bounded operations
from reviewer-fixture.md. For eventual Portal upload/save, show final files/field values and target
existing Memova draft. Formal submission and later Publish remain separately confirmed actions.
