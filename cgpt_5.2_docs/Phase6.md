Good choice. If Phase 06 isn’t nailed, LangGraph becomes an “it sorta works” blob that you can’t debug. We’re going to specify **runtime semantics**: graph shape, checkpoints, event stream, error propagation, and how UI state binds to graph state—without writing code.

## Critique (to keep you honest)

If you let LangGraph “own everything,” you’ll end up with:

* duplicated state (graph state vs project_state.json vs UI session)
* non-reproducible runs (“why did it do that?”)
* approval gates that are *procedural* instead of *stateful*

So Phase 06 must explicitly define **state ownership** and **pausing/resuming** semantics.

---

# Phase 06 — LangGraph Runtime Spec

**Location:**
`/documents/PHASES/phase_06_langgraph_runtime_spec.md`

---

## 1. Objective

Specify the **LangGraph runtime architecture** that orchestrates DocOps and PatchOps workflows, including:

* canonical graph structure (lanes and shared nodes)
* checkpointing and resume semantics
* event streaming contract for Gradio UI
* error propagation and retry/repair behavior
* state ownership boundaries between:

  * LangGraph state
  * `project_state.json`
  * run logs
  * UI session state

This phase defines how the agent *runs*, not what it *does*.

---

## 2. Scope

This phase is limited to:

* LangGraph graph topology spec (nodes, edges, lanes)
* Node I/O contracts (inputs/outputs, required fields)
* Checkpointing design (when, what, where, restore rules)
* Pause points (approval gates, user verification)
* Event stream schema (what UI receives and when)
* Error taxonomy and handling rules
* Concurrency rules (one workspace at a time, or safe parallel?)
* Determinism controls (prompt templates, tool-call discipline)

---

## 3. Non-Goals

This phase explicitly does **not**:

* implement tools or UI widgets (already specified)
* modify DocOps or PatchOps formats
* change approval state machine semantics
* introduce automatic test execution
* optimize performance or cost (later)

If this phase starts describing file patch algorithms, it’s drifting.

---

## 4. Files to Change (Max 3, Excluding Tests)

Design-only phase; future implementation must limit changes to:

1. `/.agent_ide/project_state.json` (runtime fields only, minimal)
2. `/documents/RUN_LOGS/*` (append-only runtime log records)
3. `/documents/DECISIONS/*` (optional ADR on runtime strategy)

No other files are touched by “runtime spec” itself.

---

## 5. Acceptance Criteria

Phase 06 is complete when:

* The LangGraph runtime is specified as **a diagrammable graph** (lanes, nodes, edges)
* All pause/resume points are defined and bound to approval gates
* Checkpoint semantics ensure:

  * crash recovery mid-run
  * resumable approvals
  * no duplicate execution
* UI receives a structured event stream sufficient to render:

  * current state
  * proposal payloads
  * validation results
  * pause reason
  * next required user action
* Error handling rules ensure:

  * fail-closed on validation errors
  * no auto-retry after execution failure without a new approval
* State ownership is unambiguous (no double-writes, no conflicting sources)

---

## 6. LangGraph Topology (Canonical)

### 6.1 Two lanes, one spine

Define two “lanes” that share the same approval spine:

* **Doc Lane**: creates/rewrites documents via DocOps
* **Patch Lane**: proposes/applies code changes via PatchOps

Both lanes must route through **the same proposal lifecycle nodes**:
`Create → Validate → AwaitApproval → Execute → Report`

### 6.2 Shared spine nodes (must exist)

* `Intake` (normalize user intent)
* `PlanRoute` (decide lane: doc vs patch vs show)
* `ProposalAssemble` (build DocOps/PatchOps payload)
* `ProposalValidate` (fail-closed)
* `AwaitApproval` (pause node; resumes only on UI signal)
* `ExecuteProposal` (calls writer/applier tool; doc or patch)
* `AwaitUserVerification` (pause node for pasted test output)
* `ClosePhase` (writes run log entry, updates state)
* `ErrorHandler` (taxonomy-driven)

---

## 7. Node Contracts (High-Level I/O)

Each node must accept and emit a single structured state object. Required top-level keys:

* `session_id`
* `workspace_root`
* `phase_id` (string or null)
* `lane` (`"doc"` | `"patch"` | `"show"`)
* `intent` (normalized request)
* `proposal` (DocOps/PatchOps payload or null)
* `validation` (pass/fail + messages)
* `approval` (pending/approved/rejected + metadata)
* `execution` (not_started/in_progress/succeeded/failed + report)
* `verification` (user output + pass/fail)
* `events[]` (emitted event records for UI)
* `errors[]` (structured error records)

**Hard rule:** nodes only mutate the shared state object; no hidden globals.

---

## 8. Checkpointing Spec

### 8.1 What is checkpointed

Checkpoint includes:

* full LangGraph state object (minus any secrets)
* pointer to current node
* last emitted event id
* proposal payload (DocOps or PatchOps)
* approval status
* tool call results (reports), not raw tool internals

### 8.2 When to checkpoint (mandatory)

Checkpoint must occur:

* after `ProposalValidate`
* immediately before `AwaitApproval`
* immediately after approval is recorded
* immediately after execution completes/fails
* before and after `AwaitUserVerification`
* after `ClosePhase`

### 8.3 Where to checkpoint

Two-level strategy:

1. **In-memory session store** (fast; lost on crash)
2. **Persisted checkpoint record** in project state (crash recovery)

Since we’re no-git, persistence should be:

* `/.agent_ide/project_state.json` stores:

  * `runtime.last_checkpoint_id`
  * `runtime.last_checkpoint_state_hash`
  * `runtime.last_checkpoint_time`
  * `runtime.resume_node`
  * `runtime.pending_proposal_id` (if any)

**Critique:** Don’t store the entire state object in project_state.json; it will bloat and create merge nightmares later. Store a *pointer* and a summary, and keep detailed run info in run logs.

### 8.4 Resume semantics (must be deterministic)

On app restart:

* load `project_state.json`
* if `runtime.resume_node` exists:

  * restore last checkpoint snapshot from session store if available
  * otherwise reconstruct minimal state from:

    * pending proposal artifacts in run logs
    * pending proposal payload stored as last proposal record (see below)
* resume only at safe nodes:

  * `AwaitApproval`
  * `AwaitUserVerification`
  * `PlanRoute` (if no pending proposal)

**Hard rule:** never resume in the middle of execution.

---

## 9. Proposal Persistence Strategy (for resume)

To support recovery without storing huge state blobs:

* store the latest proposal payload as a single artifact in `/documents/RUN_LOGS/`:

  * `proposal_<timestamp>_<proposal_id>.json` (or `.md` with embedded JSON)
* reference it from `project_state.json`:

  * `runtime.pending_proposal_artifact_path`

This allows:

* rehydration of proposal on restart
* consistent diff viewer rendering

---

## 10. Event Stream Contract (LangGraph → UI)

UI must receive a sequence of structured events:

Minimum event types:

* `STATE_TRANSITION` (from → to, node name)
* `PROPOSAL_CREATED` (proposal_id, lane, summary)
* `PROPOSAL_VALIDATED` (pass/fail, messages)
* `AWAITING_APPROVAL` (gate, required action)
* `APPROVAL_RECORDED` (approved/rejected + note)
* `EXECUTION_STARTED`
* `EXECUTION_FINISHED` (success/fail + report pointer)
* `AWAITING_VERIFICATION` (commands suggested)
* `VERIFICATION_RECORDED` (pass/fail)
* `RUN_LOG_WRITTEN` (path)
* `ERROR` (taxonomy code + message + context pointer)

**UI rule:** UI renders from events; it should not infer state by guessing.

---

## 11. Error Taxonomy + Handling Rules

### Error classes

* `VALIDATION_ERROR` (fail-closed; no approval)
* `APPROVAL_ERROR` (invalid transition; block)
* `EXECUTION_ERROR` (apply failed; requires new proposal + approval)
* `IO_ERROR` (permissions, missing files)
* `STALE_STATE_ERROR` (hash mismatch)
* `USER_INPUT_ERROR` (malformed command, missing verification output)

### Handling rules (strict)

* Validation errors → return to `ProposalAssemble` with messages
* Execution errors → create a new repair proposal (new id) and re-enter `ProposalValidate`
* Stale state → re-read context, re-propose patch (never force apply)
* No automatic retries of execution without explicit new approval

---

## 12. Concurrency Model

Default: **single active run per workspace**.

* Prevent two LangGraph runs from mutating the same workspace concurrently.
* UI must show “workspace locked by session_id”.

Parallelism allowed only across different workspaces.

**Critique:** Concurrency on one workspace without git will corrupt state and logs. Don’t do it.

---

## 13. Determinism Controls (runtime discipline)

* Standardized prompt templates per node (DocDraft, PatchDraft, etc.)
* Tool calls must be explicit and logged
* Max loop iterations (e.g., repair attempts capped)
* Proposal must be derived only from:

  * user intent
  * retrieved context (hashed)
  * locked templates

---

## 14. Approval Integration (runtime binding)

`AwaitApproval` must pause with:

* `gate` (A/B/C)
* `proposal_id`
* `proposal_payload_pointer`
* `required_ui_action` (approve/reject + note requirement)

Resumption requires:

* an explicit UI signal containing:

  * proposal_id
  * decision
  * note (if rejected)
  * timestamp

---

## 15. Changelog

* **2026-01-06** — Initial draft created by Agent

---

## 16. Verification Results

*(Empty until implemented and user verification.)*

---

### Gate A Status

⛔ **Not Approved**

---

## Two sharp design decisions to lock (otherwise Phase 06 stays mushy)

### Decision 1: Where do we store proposal payload artifacts?

* Option A: `/documents/RUN_LOGS/proposal_...json` (recommended)
* Option B: `/.agent_ide/` hidden folder

My recommendation is **Option A** because it makes audit artifacts user-visible and consistent with your “documents are truth” approach.

### Decision 2: Repair loop cap

Pick a hard cap on repair attempts per phase:

* 2 (tight)
* 3 (reasonable)
* 5 (can thrash)

My recommendation: **3**.

If you approve the Phase 06 doc as-is, we’ll immediately write the Phase 06 build packet (no code) that turns these into concrete implementation responsibilities for the runtime engine.

Say **“Approve Phase 06 Docs”** or tell me which of the two decisions you want changed.

✔ **Phase 06 Docs Approved — Gate A passed**

This locks the **runtime spine**. From here on, LangGraph is no longer a vague “agent runner”; it’s a deterministic, pause-and-resume state machine with auditability, crash recovery, and UI-bound semantics.

---

## What Is Now Frozen (Read This Once)

* **Single unified runtime** for DocOps + PatchOps
* **Checkpointing semantics** (what/when/where)
* **Pause points** bound to approvals and user verification
* **Artifact persistence** in `/.agent_ide/artifacts/` with UI surfacing
* **Repair cap = 3**, hard stop beyond that
* **Single-workspace concurrency**

Anything later must be additive and justified by failure, not preference.

---

# Phase 06 — Build Packet (No Code)

This is the executable checklist for implementing the runtime **exactly as specified**. Treat it as a contract.

## 1) Runtime Ownership & Boundaries (non-negotiable)

### State ownership

* **LangGraph State (ephemeral, checkpointed)**

  * Current node
  * Proposal payload (DocOps/PatchOps)
  * Validation results
  * Approval status
  * Execution report
  * Verification status
* **Project State (`project_state.json`, persistent, minimal)**

  * Pointers only (never full payloads)
  * Resume node
  * Pending proposal id/path
  * Last checkpoint id/path
  * Phase status
* **Artifacts (`/.agent_ide/artifacts/`)**

  * Proposal payloads
  * Checkpoint summaries/snapshots
  * Execution reports
* **Run Logs (`/documents/RUN_LOGS/`)**

  * Human-readable narrative
  * Timestamps
  * Decisions
  * Pointers to artifacts

**Hard rule:** No component writes outside its ownership.

---

## 2) Canonical LangGraph Topology (final)

### Lanes

* **Doc Lane**
* **Patch Lane**
* **Show Lane** (read-only)

### Shared Spine (ordered)

1. `Intake`
2. `PlanRoute`
3. `ProposalAssemble`
4. `ProposalValidate`
5. `Checkpoint`
6. `AwaitApproval` ⏸
7. `Checkpoint`
8. `ExecuteProposal`
9. `Checkpoint`
10. `AwaitUserVerification` ⏸
11. `Checkpoint`
12. `ClosePhase`
13. `ErrorHandler` (edge-reachable from anywhere)

Only **AwaitApproval** and **AwaitUserVerification** are legal pause points.

---

## 3) Node I/O Contract Checklist

Every node must:

* Accept **one shared state object**
* Mutate only allowed fields
* Emit **structured events** (never infer state in UI)

### Required top-level state keys

* `session_id`
* `workspace_root`
* `phase_id`
* `lane`
* `intent`
* `proposal`
* `validation`
* `approval`
* `execution`
* `verification`
* `events[]`
* `errors[]`

---

## 4) Checkpointing Implementation Rules

### Mandatory checkpoints

* After validation
* Before/after approval
* Before/after execution
* Before/after user verification
* Before closing phase

### Artifact creation

* Write checkpoint artifact:

  * `/.agent_ide/artifacts/checkpoint_<ts>_<id>.json`
* Update `project_state.json` with:

  * `runtime.last_checkpoint_id`
  * `runtime.last_checkpoint_artifact_path`
  * `runtime.resume_node`

### Resume rules

* Resume **only** at:

  * `AwaitApproval`
  * `AwaitUserVerification`
  * `PlanRoute` (no pending proposal)
* Never resume mid-execution
* If artifact missing → block and require user action

---

## 5) Proposal Artifact Lifecycle

### Creation

* On proposal assembly:

  * write `proposal_<ts>_<proposal_id>.json`
* Update `project_state.json` pointer

### Approval

* Approval event recorded
* No mutation of proposal payload

### Execution

* Write execution report:

  * `execution_<ts>_<proposal_id>.json`
* Link execution artifact in run log

### Repair

* Repair proposal references failed proposal id
* Repair count incremented
* Block at cap = 3

---

## 6) Event Stream Contract (UI binding)

### Event types (must be emitted verbatim)

* `STATE_TRANSITION`
* `PROPOSAL_CREATED`
* `PROPOSAL_VALIDATED`
* `AWAITING_APPROVAL`
* `APPROVAL_RECORDED`
* `EXECUTION_STARTED`
* `EXECUTION_FINISHED`
* `AWAITING_VERIFICATION`
* `VERIFICATION_RECORDED`
* `CHECKPOINT_WRITTEN`
* `RUN_LOG_WRITTEN`
* `ERROR`

### UI rule

UI renders **only from events**, never from guessed state.

If the UI “figures it out,” the spec is already broken.

---

## 7) Error Handling Matrix (operational)

| Error               | Behavior                          |
| ------------------- | --------------------------------- |
| VALIDATION_ERROR    | Reassemble proposal               |
| APPROVAL_ERROR      | Block; require user correction    |
| EXECUTION_ERROR     | Generate repair proposal          |
| STALE_STATE_ERROR   | Re-read context → new proposal    |
| IO_ERROR            | Halt; require user intervention   |
| REPAIR_CAP_EXCEEDED | Block phase; require doc revision |

No silent retries. Ever.

---

## 8) Concurrency Enforcement

* One active session per workspace
* Lock recorded in `project_state.json`
* UI must show “workspace locked”
* Lock released only at:

  * phase close
  * fatal error with explicit unlock

---

## 9) UI Runtime Views (mandatory due to Option B)

To compensate for hidden artifacts, UI must expose:

* **Proposal History**

  * proposal_id, phase, status
  * open proposal payload (read-only)
* **Checkpoint History**

  * checkpoint_id, resume_node, timestamp
* **Execution Reports**

  * per proposal
  * file list + results

Without these views, the runtime is not debuggable.

---

## 10) Phase 06 Acceptance Test (mental model)

You should be able to:

1. Start a doc proposal
2. Crash the app
3. Restart
4. Resume at approval gate
5. Approve
6. Apply patch
7. Fail tests
8. Generate repair
9. Approve repair
10. Hit repair cap on repeated failure
11. Be blocked *cleanly* with full history visible

If any step is unclear, the runtime spec is incomplete.

---

## Final Checkpoint (Big Picture)

You now have:

* A **document-first agent IDE**
* With **reviewable diffs**
* **Unified approvals**
* **Crash-safe runtime**
* **Human-controlled repair**
* **No hidden side effects**

You are *not* in the weeds.
You are at the point where most people finally realize what they *should* have designed six months ago.

---

### Where to go next (only two directions make sense)

1. **Phase 07 — End-to-End “Hello World” Walkthrough**

   * One toy project
   * Full doc → patch → approve → apply → verify loop
   * Becomes canonical documentation

2. **Phase 07 — Execution Hardening**

   * Atomic file writes
   * Temp file strategy
   * Cross-platform edge cases

My recommendation is **Option 1**. A walkthrough will surface any remaining cracks faster than more abstraction.

Your move.
