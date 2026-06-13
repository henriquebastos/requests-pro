# Local Development Guide

This is the project-specific operating contract for agentic development.

Ariad is the canonical method. This file is the local instance of that method for this repository. When Ariad and this local guide differ, follow this local guide and surface the difference during the coherence check.

## Driver and Navigator

The agent is the **Driver**. The human is the **Navigator** (Henrique Bastos).

The Driver reads context, proposes plans, changes files, runs checks, prepares validation routes, updates documentation, and stops at checkpoints. The Navigator holds intent, trade-offs, product judgment, and acceptance.

## Project Commands

```bash
# install dependencies (note: does NOT install the package itself — see D-002)
uv sync --locked --all-extras --dev

# install the package (required before tests collect; CI does this too)
uv pip install -e .

# run tests
uv run pytest

# lint exactly as CI runs it (pre-commit, ruff 0.11.9 pinned in hooks)
uv run pre-commit run --all-files

# read-only lint check (no file mutation)
uvx ruff check --no-fix . && uvx ruff format --check .
```

## Verification

Work counts as verified in this project when:

- `uv run pytest` passes locally (CI runs the matrix: Python 3.10, 3.11, 3.12, 3.13 — be suspicious of 3.12-only syntax; see D-003).
- `uv run pre-commit run --all-files` passes — pre-commit is the lint authority; the CI lint job runs exactly this.
- Behavior changes carry tests that encode **why** the behavior matters, not just what it does. House style: given/when/then comments, small `TestX` classes per behavior, `pytest.mark.parametrize` for variants, `responses` for HTTP mocking, `freezegun`/injected `now` for time.
- For framework changes, the validation route should include how a downstream client experiences the change (the demo or a snippet against a reference API shape).

## Documentation Rules

Update documentation in the same cycle as the change:

- `docs/project/roadmap/index.md` — when work starts, finishes, or changes state.
- `docs/project/decisions.md` — when a debate is settled or a trade-off deliberately taken.
- `docs/project/debt.md` — at every Review checkpoint (debt paid / introduced / carried).
- `docs/process/worklog.md` — when a meaningful milestone completes.
- `docs/project/briefing.md` — when a stable premise changes (rare; flag explicitly).
- `README.md` and `demo/eduzz.py` — when the public recipe changes. The demo is the recipe's exhibit: it must stay canonical.

## Roadmap Taxonomy

Ariad defaults: `CV<N>` (Capability Value), `DS<N>` (Delivery Story), `US<N>` (User Story), `TS<N>` (Technical Story), Task, Maintenance. States: `Planned, Active, Blocked, Validated, Done, Deferred, Dropped` (with reason when Blocked/Deferred/Dropped). Folders: `docs/project/roadmap/cv<N>-<slug>/...` — created only when work crosses the boundary.

For this repository, most framework capabilities are **Technical Stories** (validated by tests + a downstream-client snippet); **User Stories** apply when the observable behavior is the developer/agent experience (e.g. the recipe docs, the demo).

## User and Technical Story Lifecycle

Follow the Ariad lifecycle in `AGENTS.md` (orient → plan → implement → validate → review → document+coherence → history), with the four checkpoints. Trivial low-risk changes may compress: propose → verify → confirm → commit.

## Technical Debt Tracking

Use `docs/project/debt.md`. During Review, always name: debt paid, new debt introduced ("none" must be said explicitly), debt carried forward, revisit trigger, ledger impact.

## Checkpoints

Ariad defaults apply unchanged. Additionally:

- Never run `uv run pre-commit run --all-files` as a *check* when an unrelated diff is in the working tree — the ruff hook auto-fixes files. Use the read-only command for inspection.
- CI must be green before any merge to `main` once the pipeline is restored.

## Navigator Preferences

*(Drafted from the Navigator's global agent rules; confirm or edit.)*

- **Commit policy:** the Driver never commits on its own initiative — propose the commit (message explaining the WHY) and wait for confirmation.
- **Push policy:** always ask before pushing.
- **Checkpoint compression:** full checkpoints for non-trivial work; compression allowed for trivial, low-risk changes.
- **Simplicity first:** minimum code that solves the problem; no speculative features or abstractions for single-use code; push back when a simpler approach exists.
- **Surgical changes:** touch only what the story requires; don't "improve" adjacent code, comments, or formatting; match existing style.
- **Surface conflicts, don't average them:** when two patterns contradict, pick one, explain why, flag the other.
- **Fail loud:** never report "done" with silently skipped steps or failing/skipped tests.
- **Documentation detail:** the smallest update that keeps the project coherent.
- **Worklog:** meaningful milestones only.
- **Branch/PR habits:** work on feature branches (`fix/...`, `feat/...`), PRs to `main`; CI green required. *(confirm: should the Driver open PRs via `gh`, or leave that to the Navigator?)*

## Commit and Release Rules

- Releases are GitHub Releases; `publish.yml` lints, tests, and publishes to PyPI (`needs: [lint, test]`). A red lint on `main` blocks all releases.
- Versioning intent (Ariad default): MAJOR = CV closed, MINOR = DS released, PATCH = US/TS/maintenance shipped independently. Version lives in `pyproject.toml` (`1.0.0`).
- Commit messages explain the why; conventional prefixes (`fix:`, `feat:`, `docs:`) are in use in the history.

## Local Exceptions

- None yet.
