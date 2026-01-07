# Phase 03 — Unified Approval State Machine + PatchOps Gate

**Phase ID:** 03
**Status:** Completed
**Last Updated:** 2026-01-06

---

## 1. Objective

Define and implement a **single, unified approval state machine** that governs all mutating actions in the IDE, including document writes (DocOps) and code changes (PatchOps).

---

## 2. Scope

- Defined the approval lifecycle: `Idle`, `Proposal_Created`, `Proposal_Validated`, `Awaiting_Approval`, `Approved`, `Rejected`, `Executing`, `Completed`, `Failed`.
- Unified proposal contract implemented in `app/proposals/models.py`.
- PatchOps skeleton defined in `app/proposals/patchops.py`.
- Gradio UI updated with a unified "Approval Center".
- Approval persistence implemented in `project_state.json`.

---

## 3. Implementation Details

- **Protocol**: Pydantic models for `UnifiedProposal` and `ApprovalRecord`.
- **State Management**: `StateManager` updated to handle unified proposal transitions and approval logging.
- **UI**: Added conditional logic to enable "Approve", "Reject", and "Execute" buttons based on proposal state.

---

## 4. Acceptance Criteria (Verified)

- [x] Docs and PatchOps use the same approval states.
- [x] UI approval controls are consistent.
- [x] No write action without approval.
- [x] Rejections and failures are logged.

---

## 5. Changelog
* **2026-01-06** — Implementation completed and verified with unit tests.
