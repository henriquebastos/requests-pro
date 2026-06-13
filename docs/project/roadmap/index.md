# Roadmap

The roadmap describes meaningful progress, not every task. Taxonomy, codes, folders, and states follow Ariad defaults (see `docs/process/development-guide.md`).

## Current Focus

**Restore the delivery pipeline, then grow the framework.** CI was red on every push since 2025-07-31 because `main` carried auto-fixable lint debt; `lint` failed → `test` was skipped → `publish` could never run. Paid on 2026-06-12. Next: land the pending fixes (PR #5, issue #4 branch, 204 branch), then grow the framework toward the Navigator's vision — the same architecture in sync and async flavors, with the missing cross-cutting capabilities, legible enough that an agent can derive a new client from an API spec.

## Active Work

| Item | Status | Notes |
|------|--------|-------|
| (none) | — | Next pull: rebase + land PR #5 |

## Planned Work

| Item | Status | Notes |
|------|--------|-------|
| Maintenance: rebase + land PR #5 (`json=None` GET body) | Planned | Trivial quote-style conflict with the lint fix in `sessions.py` expected |
| Maintenance: open + land PR from `claude/issue-4-20250915-2231` (audit stream placeholder) | Planned | Fix and tests already written; decision recorded in `decisions.md` |
| Maintenance: land or fold `fix/handle-204-no-content` (D-008) | Planned | May merge into a future error-handling story instead |
| Maintenance: delete obsolete branches (`claude/issue-2-*`, `add-claude-github-actions-*`) | Planned | Housekeeping |
| CV1 — Error semantics: API error taxonomy, `raise_for_status` hooks (incl. "HTTP 200 with error body"), transient/permanent classification, response-envelope hook | Planned | Framework ships no error hooks today; the demo hand-rolls `EduzzAPIError` + `ERROR_STATUSES` |
| CV2 — Testing toolkit (`requestspro.testing`): `ProResponse` builders, recording fake session/adapter, given/when/then conventions | Planned | Test setup currently means manual `Response._content`/`headers`/`status_code` plumbing |
| CV3 — Webhook verification toolkit: parametrizable HMAC verifier base (base string, headers, tolerance window, `compare_digest`, exception taxonomy, verify+parse atomicity) | Planned | The same skeleton fits any provider that HMAC-signs its webhooks; institutionalizes "verification lives in the integration package" |
| CV4 — Resilience: client-side rate limiting with pluggable strategies, transient retry with backoff, 429/`Retry-After` awareness | Planned | Adapter-decorator seam proven by `Audit`; open discussion in `decisions.md` |
| CV5 — Async flavor: same architecture over httpx | Planned | Coupling seams listed in `decisions.md`; needs the open sync/async architecture decision first |
| CV6 — The Recipe: agent-facing documentation that derives a new client (sync or async) from an OpenAPI spec or API docs | Planned | Branch `claude/write-requests-pro-guide-uCZq0` has a 577-line `docs/HOWTO.md` draft as raw material; demo bugs (D-010) should be fixed as part of it |

## Done

| Item | Notes |
|------|-------|
| 2026-06-12 — Maintenance: GitHub Actions pinned to Node 24 (checkout v6, setup-python v6, setup-uv v7) + publish.yml `python-version-file` fix | PR #6; CI green. setup-uv held at v7 to keep pin-by-major (see `decisions.md`) |
| 2026-06-12 — Maintenance: lint debt paid (D-001) + `[build-system]` declared (D-002) | First Ariad delivery session; CI/release pipeline restored (green run on `main`) |
| 2026-06-12 — Ariad adopted; deep survey of framework core + demo; CI root cause identified | See `docs/process/worklog.md` |
| 2025-07 — Session-level timeout support (PR #3) | Last merged feature; its merge introduced part of the lint debt |

## Radar

Problems visible but not planned; each names the problem and its evidence/trigger.

- **Pagination** — no helpers (iterators, cursors, link headers). Trigger: first client needing listing.
- **Idempotency keys** — standard in payment APIs (`Idempotency-Key` header); framework offers nothing. Trigger: CV1/CV4 design.
- **Static auth + default headers** — framework only offers the "heavy" `RecoverableAuth` (renewable) or manual header-setting; a `StaticTokenAuth` + `DEFAULT_HEADERS` would close the gap for long-lived API keys/bot tokens. Trigger: CV1 or recipe work.
- **Form-encoded request bodies** — `Client.request` assumes JSON; OAuth token endpoints and some APIs need `application/x-www-form-urlencoded`. Trigger: CV1 design.
- **Audit hardening** — bounded/streamable event storage, logging handlers, secret redaction by default, `http://` schema coverage (D-004). Trigger: first long-running production consumer.
- **Access to the raw Response** — `Client.request` returns only parsed JSON; status/headers are unreachable for callers (needed for pagination, rate-limit headers). Trigger: first consumer needing headers.
- **Cache-injectable factory convention** — `from_credentials` composition often hardcodes a cache backend, blocking non-Django use; a documented convention for injecting in-memory vs. shared cache would help the recipe. Trigger: recipe work (CV6).
- **setup-uv v8 / SHA-pinned actions** — v8 dropped major/minor tags (immutable releases), so adopting it means full-tag or SHA pinning and losing automatic patch updates; deferred to keep pin-by-major. Trigger: adopting Dependabot or a supply-chain hardening policy.
