# Worklog

Operational progress for the project.

Update this file when a meaningful milestone is completed. The worklog is not a full history of every edit. It is the project memory that helps future sessions understand what changed, why it matters, and how it was verified.

## Done

### 2026-06-12 — Delivery pipeline restored (D-001 + D-002 paid)

What changed: The pinned pre-commit hooks (ruff 0.11.9) auto-fixed the 25 lint violations on `main` (quote style and import order in `src/requestspro/sessions.py` and `tests/test_session_timeout.py`, plus one reformat). `pyproject.toml` now declares `[build-system]` (`setuptools.build_meta`, `setuptools>=77` for PEP 639 license metadata), and `uv.lock` was regenerated (project entry `virtual` → `editable`; lock format revision 2 → 3 — written by uv 0.11.19, same as CI's latest).

Why it matters: Every CI run had failed since 2025-07-31 — `lint` red, `test` skipped, `publish` unreachable. With the lint debt paid and the package installable by `uv sync` alone, the pipeline is whole again: PRs get real test runs and releases can publish.

How it was verified: Fresh venv (`/bin/rm -rf .venv && uv sync --locked --all-extras --dev`) → `pytest` 41 passed with no manual editable install; `uv build` produced a correct wheel and sdist (all modules + LICENSE in dist-info); `uv run pre-commit run --all-files` fully green. Final confirmation route: green "Lint and Test" run on `main` after push.

Follow-ups: rebase + land PR #5 (trivial quote conflict in `sessions.py` expected), open the PR for the issue-4 branch. Conscious exclusion: dev-group ruff stays at 0.11.8 vs hook 0.11.9 (inert today; noted in es-001 Carry Forward).

### 2026-06-12 — Ariad adopted; full project survey; CI root cause identified

What changed: Installed the local Ariad instance (`AGENTS.md`, `docs/project/*`, `docs/process/*`, `docs/product/*`), initialized from a deep survey of the framework core and the Eduzz demo plus the Navigator's stated design vision. Seeded the debt ledger (D-001..D-011), the roadmap (CV1–CV6 + maintenance queue), and five standing decisions.

Why it matters: The project advances in long-gapped bursts; this memory surface lets any agent session recover full context. The survey also found the single blocker of the delivery pipeline: `main` has carried 25 auto-fixable ruff violations since 2025-07-31, failing `lint`, skipping `test`, and blocking `publish` — no PR or release can land until it's paid (D-001). Secondary finding: missing `[build-system]` means `uv sync` alone doesn't make tests collectable (D-002).

How it was verified: `uv pip install -e . && uv run pytest` → 41 passed on `main`. Lint failure reproduced read-only with the pinned ruff (25 errors, 2 files, all auto-fixable). CI history cross-checked via `gh run list` (green until 2025-07-30, red after). Issue #4, PR #5, and all remote branches inspected via `gh`.

Follow-ups: first delivery session proposed = pay D-001 (+D-002) as Maintenance; then rebase/land PR #5, open the PR for the issue-4 branch, land or fold `fix/handle-204-no-content`. Conscious exclusion: no code was changed in this session — docs only.

## Next

Confirm the first green "Lint and Test" run on `main`, then pull the next Maintenance items: rebase + land PR #5, open the PR for `claude/issue-4-20250915-2231`, land or fold `fix/handle-204-no-content`, delete obsolete branches.
