# Project Briefing

Stable context for this project. Drafted by the Driver during Ariad adoption (2026-06-12); items marked *(confirm)* were inferred and need Navigator confirmation.

## Purpose

RequestsPro is a framework for building professional-grade API clients on top of `requests`, eliminating repetition and enforcing separation of concerns and single responsibility at every layer.

It serves two audiences:

1. **Developers** building API clients that need transparent auth, token persistence, 401 recovery, custom JSON handling, consistent error handling, and HTTP audit — without rewriting that plumbing per API.
2. **Coding agents.** The long-term goal is that this repository works as an executable recipe: point an agent at an API's documentation or OpenAPI spec plus this repo, and the agent generates a complete, well-tested client (sync or async) that follows the architecture by construction.

## Current State

- Version 1.0.0 published on PyPI as `requests-pro`. Sync-only, built on `requests`.
- Core modules in `src/requestspro/`: `client.py` (`Client`/`MainClient`), `sessions.py` (cooperative mixins `BaseSession`, `BaseUrlSession`, `CustomJsonSession`, `CustomResponseSession`, composed as `ProSession`; `ProResponse`), `auth.py` (`RecoverableAuth`: lazy token renewal + single 401 retry), `token.py` (`TokenStore`/`ExpireValue`), `audit.py` (adapter-decorator HTTP audit), `audit_for_django.py`, `utc.py`.
- 41 tests pass on `main`. CI was red on every push from 2025-07-31 to 2026-06-12 (lint debt on `main` failed `lint`, skipped `test`, and blocked `publish`); paid on 2026-06-12 (D-001), together with the missing `[build-system]` (D-002) — `uv sync` now installs the package and tests collect directly.
- Open work: issue #4 (audit breaks on streamed bodies; fix exists on branch `claude/issue-4-20250915-2231`, PR never opened), PR #5 (`json=None` encoded as `"null"` body on GET; needs rebase over the lint fix), branch `fix/handle-204-no-content` (no PR).
- Reference example: `demo/eduzz.py` — the minimal canonical client built on the framework. No tests, no webhooks, no service layer.

## Architecture Premises

- **Layering, from the wire up**: `ProResponse` subclass (translates the API's error envelope once) → `ProSession` subclass (protocol: base URL, JSON encoder/decoder, timeout, headers) → `RecoverableAuth` subclass (credentials, `renew()`, `authorize()`) → `TokenStore` (pluggable persistence: in-memory or any cache-like backend) → `MainClient.from_credentials()` (explicit composition) → `Client` subclients (one-line methods per endpoint).
- **The organizing thesis** (from the demo docstring): *"The Client and SubClients are simple because we handled all the API craziness before."* API quirks are resolved in the lowest applicable layer, exactly once.
- Configuration by class attributes; composition happens explicitly in the factory; mixins cooperate via `**kwargs` + `super()` chains (MRO order is load-bearing).
- `Audit` is an adapter decorator wrapping the real `HTTPAdapter` — the established pattern for future cross-cutting concerns (retry, rate limiting).
- Token-renewal requests deliberately bypass auth and audit (no credential logging, no auth loops). Covered by tests.
- **Integration boundary** (the Navigator's stated design philosophy): the API client package owns everything that speaks the vendor's protocol, including *verification* of incoming webhooks (signature/HMAC, replay window) — verification lives next to the client, not in the web framework layer. Webhook *handlers* stay thin and business-focused. A separate *service layer* is the only surface the product consumes: it converts client responses into domain objects and client exceptions into domain exceptions. The framework itself ships only the integration layer; the boundary is a documented convention.
- Planned: sync (`requests`) and async (`httpx`) flavors of the same architecture; httpx's API is close enough to make this natural. The sync API must not break when async lands. *(confirm packaging approach when work starts)*

## Product Premises

- Consumers must be able to trust the transparent machinery: auth renewal, 401 recovery, JSON handling, and audit work without per-call ceremony.
- Agent-legibility is a product feature: docs, demo, and tests should teach the recipe well enough that an agent replicates it for a new API without human coaching.
- Extension by subclassing documented hooks — consumers should never need to fork or monkey-patch the framework.

## Constraints

- `requires-python >= 3.10`. (`audit_for_django.py` currently violates this with 3.12-only `type` alias syntax — known bug, see debt ledger.)
- Runtime dependency is `requests` only; keep the sync flavor dependency-light.
- Public API stability: 1.0.0 is published; breaking changes need deliberate versioning decisions.
- Lint: ruff with `select = ["ALL"]` (minus ignores), line length 120, enforced through pre-commit (ruff 0.11.9 pinned in hooks).

## Operating Notes

- Tooling is `uv`-first. See `docs/process/development-guide.md` for commands and verification.
- CI: `push.yml` runs `lint` → `test` (test skipped if lint fails); `publish.yml` on release needs both. Pre-commit is the lint authority.
- GitHub: issues and PRs on `henriquebastos/requests-pro`; Claude Code Review and PR Assistant workflows are installed.

## Glossary

- **SubClient** — a `Client` subclass grouping one API resource's endpoints as one-line methods, sharing the `MainClient`'s session.
- **Recipe** — the documented, agent-followable process of deriving a new client from this architecture.
- **Integration layer / service layer / webhook handler** — see Architecture Premises; the three-layer boundary every full client should follow.
