# Phase 04 — PatchOps Protocol + Diff Viewer

**Phase ID:** 04
**Status:** Completed
**Last Updated:** 2026-01-06

---

## 1. Objective

Define a **file-level PatchOps protocol** and a **read-only diff review UI** that allows code changes to be proposed as auditable artifacts.

---

## 2. Scope

- Defined PatchOps v1 protocol in `app/proposals/patchops.py`.
- Implemented SHA-256 hashing for file validation.
- Implemented unified diff generation for patch review.
- Added a "Diff Viewer" tab to the Gradio UI.
- Integrated PatchOps proposals into the unified approval state machine.

---

## 3. Implementation Details

- **Protocol**: File-level operations (`create`, `update`, `delete`) with mandatory `pre_hash` and `post_hash` for safety.
- **Validation**: Enforces workspace boundaries, protected paths, and hash matching (blocking stale patches).
- **UI**: Read-only diff view showing lines added/removed.
- **Artifacts**: Immutable diff artifacts stored in `/documents/RUN_LOGS/`.

---

## 4. Acceptance Criteria (Verified)

- [x] PatchOps proposals are correctly validated.
- [x] Diff artifacts are generated correctly.
- [x] Diff viewer displays deletions and additions as expected.
- [x] ApprovalFlow governs PatchOps.
- [x] No filesystem code changes occur (execution deferred).

---

## 5. Changelog
* **2026-01-06** — Implementation completed and verified with unit tests.
