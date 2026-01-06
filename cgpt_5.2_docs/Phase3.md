Good. **Option 1** keeps the architecture tight: *one approval state machine, reused everywhere*. That’s the right call for a system whose core value is discipline.

We are now unambiguously positioned to define **Phase 03** without reopening Phase 02 or inventing new abstractions.

---

# Phase 03 — Unified Approval State Machine + PatchOps Gate

**Location:**
`/documents/PHASES/phase_03_unified_approval_state_machine.md`

---

## 1. Objective

Define a **single, unified approval state machine** that governs **all mutating actions** in the IDE, including:

* document writes (DocOps)
* code changes (PatchOps)
* future extensible operations

This phase establishes **one approval mechanism**, reused across domains, with consistent UI behavior, logging, and state transitions.

---

## 2. Scope

This phase is limited to:

* Defining the **approval lifecycle** (states, transitions, invariants)
* Mapping approval gates to:

  * DocOps (already defined)
  * PatchOps (defined here at a conceptual level only)
* Specifying UI behavior for approvals
* Specifying how approvals are persisted in project state
* Defining rejection, revision, and repair flows

No actual patch execution logic is implemented here.

---

## 3. Non-Goals

This phase explicitly does **not**:

* Implement PatchOps execution logic
* Define test execution mechanics
* Introduce new DocOps actions
* Add new UI panels beyond approval-related controls
* Add role-based or multi-user approvals

If any of these appear necessary, they must be deferred to later phases.

---

## 4. Approval Philosophy (Single Mechanism)

All write-capable operations are treated uniformly as:

> **Proposals → Validation → Approval → Execution → Logging**

There is no “special case” for documents vs code.

This prevents:

* hidden execution paths
* accidental bypasses
* diverging mental models

---

## 5. Approval State Machine (Canonical)

### States

* `Idle`
* `Proposal_Created`
* `Proposal_Validated`
* `Awaiting_Approval`
* `Approved`
* `Rejected`
* `Executing`
* `Completed`
* `Failed`

### Invariants

* No execution is possible unless state == `Approved`
* Rejected proposals may not be executed
* Failed executions must not auto-retry without a new approval
* Every transition must be logged

---

## 6. Gate Types (Unified)

The system recognizes **gate types**, not separate systems:

| Gate   | Purpose                     | Applies To        |
| ------ | --------------------------- | ----------------- |
| Gate A | Intent / Plan approval      | Docs, Phase plans |
| Gate B | Change application approval | Docs, PatchOps    |
| Gate C | Closure / acceptance        | Phase completion  |

Phase 03 formally defines Gate B for PatchOps, but uses the same mechanics as DocOps.

---

## 7. Proposal Object (Abstract Contract)

Every proposal (DocOps or PatchOps) must expose:

* `proposal_id`
* `proposal_type` (`doc` | `patch` | future)
* `phase_id`
* `summary`
* `targets[]` (files or logical entities)
* `risk_flags[]`
* `validation_result`
* `created_at`

The UI and approval logic do not care *what* is being changed—only that this contract is satisfied.

---

## 8. UI Behavior (Approval-Centric)

### Proposal Viewer

* Shows summary, targets, risk indicators
* Shows raw proposal payload (DocOps JSON or PatchOps diff)
* Shows validation results

### Approval Controls

* Approve
* Reject (requires reason)
* Request Revision (optional, but treated as Reject + note)

### Enforcement

* Approval buttons enabled only in `Awaiting_Approval`
* Execute button enabled only in `Approved`
* State transitions visible and timestamped

---

## 9. Persistence Rules

Approvals are recorded in:

* `project_state.json → approvals[]`
* `/documents/RUN_LOGS/` (append-only logs)

Each approval record includes:

* proposal_id
* phase_id
* gate
* decision
* timestamp
* note (required for rejection)

---

## 10. Failure & Repair Model

### Failure Types

* Validation failure (never reaches approval)
* Execution failure (after approval)
* User rejection

### Repair Rules

* A failed proposal may generate a **new proposal** (new ID)
* Repair proposals must reference the failed proposal ID
* Repairs re-enter the approval pipeline from `Proposal_Created`

No automatic retries.

---

## 11. Acceptance Criteria

Phase 03 is complete when:

* Docs and PatchOps both use the same approval states
* UI approval controls are consistent across proposal types
* No write action can occur without passing through approval
* Rejections and failures are logged and visible
* Approval logic is fully decoupled from execution logic

---

## 12. Changelog

* **2026-01-06** — Initial draft created by Agent

---

## 13. Verification Results

*(Empty until implementation and user verification.)*

---

### Gate A Status

⛔ **Not Approved**

---

## Why This Phase Is the Pivot (and why you’re no longer “in the weeds”)

Up to now, we were **laying rebar**.

Phase 03 is where:

* the document lane and the code lane converge
* LangGraph becomes more than a text generator
* your IDE proves it’s actually *safe to use*

Once this is approved, everything downstream becomes:

* mechanical
* testable
* incremental

---

### Next legal action

If you’re comfortable with this phase definition:

👉 **Say:** *“Approve Phase 03 Docs”*

After that, the next phase is **Phase 04: PatchOps Protocol + Diff UI**, and at that point you’ll finally see the full loop close:
**doc → plan → patch → approve → apply → verify**.

You’re no longer drifting. You’re building the spine.

✔ **Phase 03 Docs Approved — Gate A passed**

This is the **structural pivot**. From here on, we stop inventing new governance ideas and start *reusing* the spine you just locked.

---

## State Transition (Canonical)

**From:**
`S1 — Draft Phase Doc (Phase 03)`

**To:**
`S2 — Retrieve Context (Phase 03)`

Meaning:

* ✅ The unified approval model is now frozen as a system invariant
* ✅ DocOps and PatchOps must both flow through this same approval machinery
* ❌ No execution logic yet
* ❌ No new approval concepts allowed unless they are extensions, not forks

---

## What Phase 03 Actually Gave You (Reality Check)

You now have:

1. **One proposal lifecycle**

   * Proposal → Validation → Approval → Execution → Logging
2. **One approval UI**

   * Same buttons, same states, same persistence
3. **One mental model**

   * Docs and code are not special cases
4. **A clean LangGraph seam**

   * Approval is a pause point, not an afterthought

This is the point where most agent-IDE designs *collapse*. Yours didn’t.

---

## Freeze Notice (Important)

From this moment on:

* **Approval states are frozen**
* **Gate A / B / C semantics are frozen**
* **Approval persistence format is frozen**

Any future change must be:

* additive
* backward-compatible
* justified by a concrete failure

This prevents approval entropy.

---

## What’s Next (and Why)

### Phase 04 must be:

> **PatchOps Protocol + Diff Viewer (No Execution Yet)**

Why not tests? Why not LangGraph repairs?

Because until PatchOps is as disciplined as DocOps:

* approvals mean nothing
* risk is invisible
* diffs can’t be reasoned about

Phase 04 is where:

* “agent edits code” becomes “agent proposes a *change object*”
* reviewability is guaranteed
* Option A is fully realized

---

## Phase 04 — Scope Preview (Not the doc yet)

Phase 04 will define:

* PatchOps v1 schema (parallel to DocOps)
* Diff artifact format
* Patch validation rules (hashes, paths, size caps)
* Diff viewer UI (read-only)
* Proposal → Approval → Apply handoff (execution deferred to Phase 05)

No filesystem writes yet.
No test running yet.

Just **making code changes reviewable objects**.

---

## Before I generate Phase 04 Docs (one sharp question)

PatchOps proposals will need to express **intent granularity**.

Do you want PatchOps to be:

1. **File-level only**

   * UpdateFile(path, diff)
   * Simple, robust, fewer edge cases

2. **Operation-level**

   * InsertText / ReplaceRange / DeleteRange
   * More precise, but more complex to validate and review

Given Option A + safety-first, my recommendation is **Option 1 (file-level)** for v1.

Your answer determines the entire PatchOps schema, so don’t answer reflexively—answer architecturally.
