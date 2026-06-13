# Decisions

Incremental decisions made as the project evolves. Entries dated before 2026-06-12 were reconstructed by the Driver from code, tests, and issue history during Ariad adoption — marked *(reconstructed; confirm)* where the rationale was inferred.

## Completed Decisions

### Adopt Ariad as the development method

**Date:** 2026-06-12
**Status:** Decided

Decision: This repository uses Ariad (Driver/Navigator, Exploration/Delivery, checkpoint lifecycle). The local instance lives in `AGENTS.md` and `docs/`; the canonical method is not vendored.

Rationale: The project advances in bursts with long gaps; the Navigator wants any agent pointed at the repo to recover full context and follow the same process. Ariad's memory surface (briefing, decisions, roadmap, debt, worklog) is that mechanism.

Consequences: Agents read `AGENTS.md` and the docs listed there before meaningful work; non-trivial work goes through plan/validation/review/history checkpoints; documentation updates in the same cycle as code.

### Pin GitHub Actions to Node 24; setup-uv on v7 not v8

**Date:** 2026-06-12
**Status:** Decided

Decision: The workflows pin `actions/checkout@v6`, `actions/setup-python@v6`, and `astral-sh/setup-uv@v7` — the newest releases running on the Node 24 runtime that GitHub Actions defaults to from 2026-06-16 (Node 20 removed 2026-09-16). setup-uv stays on v7 rather than the latest v8.

Rationale: v8 stopped publishing major/minor tags, so `@v8` no longer resolves; adopting it would force full-tag (or SHA) pinning and forfeit the automatic patch updates that pin-by-major provides. v7 runs on Node 24 and keeps the repo's pin-by-major convention. A breaking-change scan found nothing in checkout v6, setup-python v6, or setup-uv v6/v7 that affects this repo's usage.

Consequences: Revisit setup-uv v8 (and SHA-pinning generally) if the repo adopts Dependabot or a supply-chain hardening policy. Tracked on the roadmap radar.

### Audit replaces streamed bodies with a placeholder

**Date:** 2025-09-15
**Status:** Decided (landed 2026-06-13)

Decision: When a request or response body is a stream (file-like/generator, or `stream=True`), the audit records a placeholder instead of materializing the body (issue #4; option 1 of the five discussed, chosen by the owner, TDD approach).

Rationale: Reading the body inside the adapter either crashes (`AttributeError`/`UnicodeDecodeError` on file-like and binary bodies) or defeats streaming by loading everything into memory. Audit must never break or distort the request it observes.

Consequences: Streamed bodies are not auditable by design; a richer strategy (sampling, metadata-only, content-type aware) stays on the radar. Detection: response streaming keys off the `stream` kwarg the audit adapter receives from `Session.send`; request streaming off a file-like or non-bytes-iterable body.

### Webhook verification belongs to the integration package

**Date:** 2026-06-12 (Navigator's stated design philosophy)
**Status:** Decided

Decision: Verifying that an incoming webhook genuinely comes from the vendor (signature/HMAC, timestamp window, replay defense) is integration-layer knowledge and lives next to the API client, not in the web framework layer. Verification and payload parsing are one atomic operation: you cannot obtain the payload without passing verification.

Rationale: The same package that knows how to talk to the vendor knows how to recognize the vendor talking back. Views/controllers stay thin: extract headers + raw body, delegate, map exceptions to 403.

Consequences: A future `requestspro` webhook-verification toolkit must keep vendor idiosyncrasies in subclasses, never in the base. HMAC-signed webhooks are a common, publicly documented pattern across many providers, so the base can be generic.

### Service layer is the product-facing boundary

**Date:** 2026-06-12 (Navigator's stated design philosophy)
**Status:** Decided

Decision: Products never consume the API client directly. A service layer converts client responses into domain objects and client exceptions into domain exceptions; webhook handlers consume the service, not the client.

Rationale: The client speaks the vendor's language; the product speaks the domain's. Keeping translation in one layer makes both sides independently testable and replaceable.

Consequences: The framework documents this boundary as part of the recipe even though it ships no service-layer code.

### Token-renewal traffic bypasses auth and audit

**Date:** ~2024 *(reconstructed from code and tests; confirm)*
**Status:** Decided

Decision: `RecoverableAuth.renew()` uses a fresh `SESSION_CLASS()` session; renewal requests are not authenticated with the expiring token and are not recorded by `Audit` (test: `test_client_should_not_log_auth_requests`).

Rationale: Avoids logging credentials and avoids auth recursion/loops.

Consequences: Auth traffic is invisible to the audit trail on purpose; do not "fix" this when building observability features.

## Open Discussions

### Sync + async: how do the two flavors coexist?

**Status:** Open
**Raised:** 2026-06-12

The framework must offer the same architecture over `requests` (sync) and `httpx` (async) — httpx's API is close enough to make this natural. The coupling seams: adapter→transport for `Audit`, `AuthBase`+hooks→`auth_flow` generator for `RecoverableAuth`, `prepare_request`→`build_request` for the session mixins, the `response.__class__` cast, and the eager `.json()` in `Client.request`. Undecided: one package with `requestspro.sync`/`requestspro.aio`? A shared policy core with two thin bindings? Does the sync flavor migrate to httpx-sync, or stay on requests? What would make this decidable: a spike porting the Eduzz demo to httpx async behind a shared abstract core.

### Rate limiting and retry strategy interface

**Status:** Open
**Raised:** 2026-06-12

The framework needs client-side rate limiting (with pluggable strategies — token bucket, fixed window, `Retry-After`/429 awareness) and transient-failure retry with backoff. Importing/adapting an existing strategy library is acceptable if it supports the RequestsPro composition model. The adapter-decorator pattern proven by `Audit` is the natural seam. Undecided: own implementation vs. wrapping `urllib3.Retry` vs. third-party strategy lib; how strategies compose with the future async flavor.

### `from_credentials` contract vs. named factories

**Status:** Open
**Raised:** 2026-06-12

`MainClient.from_credentials` is a nominal `NotImplementedError` contract, but a static-token API has no credentials to exchange and naturally wants a `from_token`-style factory instead. Either relax the contract (factories are conventionally named: `from_token`, `from_client_credentials`, ...) or enforce it. Affects the recipe documentation.

### Packaging hygiene

**Status:** Open
**Raised:** 2026-06-12

`__init__.py` exports nothing (no stable public API surface), and `ruff target-version = "py312"` disagrees with `requires-python >= 3.10`. `[build-system]` was added 2026-06-12 (D-002). Decide the public API of `requestspro.__init__` and the real minimum Python; revisit the build backend choice if hatchling/uv_build becomes preferable.
