# Technical Debt Ledger

This ledger records structural cost the project is consciously carrying.

Do not record every imperfection. Record debt that may affect future delivery,
safety, maintainability, validation, operation, or product coherence.

## States

```text
Carried   known and accepted for now
Paying    currently being reduced by active work
Paid      resolved or reduced enough to close
Dropped   no longer relevant or replaced by another item
```

## Debt Items

| ID | Title | Kind | Severity | Status | Source | Revisit Trigger |
|----|-------|------|----------|--------|--------|-----------------|
| D-001 | Lint debt on `main` blocks the whole CI/release chain | operations | high | Paid (2026-06-12) | PR #3 merge + web-UI edit (2025-07) | — |
| D-002 | No `[build-system]` in pyproject; `uv sync` doesn't install the package | operations | medium | Paid (2026-06-12) | initial packaging | — |
| D-003 | `audit_for_django.py` uses 3.12-only syntax; SyntaxError on import in py3.10/3.11; fallback `HttpHeaders(...)` not callable | architecture | high | Carried | adoption survey 2026-06-12 | Before any release claiming py3.10 support |
| D-004 | `Audit.events` is an unbounded in-memory list; no rotation/flush/handler; secrets unredacted by default | architecture | medium | Carried | adoption survey | When observability/audit story is planned |
| D-005 | `response.__class__` cast in `CustomResponseSession` skips `__init__`; implicit coupling between mixins (works only in `ProSession` order) | design | medium | Carried | adoption survey | Async-support spike (cast won't port to httpx) |
| D-006 | No thread-safety: token renewal race in `TokenStore`/`ExpireValue`, unsynchronized `Audit.events` | architecture | medium | Carried | adoption survey | First concurrency-sensitive consumer or async story |
| D-007 | `handle_401` retries with the possibly-revoked stored token (does not invalidate before retry) | design | medium | Carried | adoption survey | Auth/resilience story |
| D-008 | `Client.request` always calls `response.json()`; HEAD/204/empty bodies raise `JSONDecodeError` (`fix/handle-204-no-content` branch exists, no PR) | design | medium | Carried | adoption survey | Error-handling/response story |
| D-009 | `test_auth.py:71` patch never started — `test_auth_dont_recover_twice` passes by coincidence | test | low | Carried | adoption survey | Next time `auth.py` is touched |
| D-010 | Demo bugs: `dt.replace(tzinfo=...)` return discarded in `EduzzAuth.renew` (wrong TTL timezone); argparse positionals with `default=` don't work as fallback; demo has no tests | docs | low | Carried | adoption survey | Recipe-documentation story (demo is the recipe's exhibit) |
| D-011 | `InvalidJSONError(ve, request=self)` passes the Session as request (`sessions.py:150`); dead `recover_401` param (`auth.py:58`); `BaseSession.__init__` swallows unknown kwargs | design | low | Carried | adoption survey | Next time `sessions.py` or `auth.py` is touched |

## Template

```text
ID:
Title:
Kind: design | test | docs | architecture | operations | process
Severity: low | medium | high
Status: Carried | Paying | Paid | Dropped
Source:
Carrying reason:
Revisit trigger:
Closure condition:
Notes:
```
