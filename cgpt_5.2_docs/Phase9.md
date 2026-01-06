You’re right — the last response **violated the spec you built**.

### Direct critique (no softening)

* What you got was a **generic enterprise app SDLC**.
* It ignored **your actual system invariants**: DocOps, PatchOps, approvals, LangGraph pauses, atomic execution.
* It would **fail Anti Gravity review** because it doesn’t tell them *what to build*, *in what order*, or *what files/modules must exist*.
* It reintroduced abstraction instead of **operational design**.

We’re fixing that now.

Below is a **purpose-built SDLC design document** for **your Lightweight Agent IDE**, written so Anti Gravity can **implement it phase-by-phase** with no ambiguity.

No fluff. No product-speak. No generic CRUD app nonsense.

---

# Lightweight Agent IDE

## SDLC Design Specification

**Audience:** Anti Gravity Engineering
**Format:** Markdown
**Scope:** Full system build from empty repo to hardened runtime
**Constraints:**

* Gradio UI
* Python runtime
* LangGraph orchestration
* OpenAI-compatible LLM interface
* Local filesystem workspace
* Human-in-the-loop approvals
* Atomic patch execution

---

## SYSTEM GOAL (One Paragraph)

Build a **document-first, approval-gated, crash-safe agent IDE** that allows an LLM to *propose* document changes and code patches, but **never execute side effects** without explicit human approval, verifiable diffs, checkpointing, and deterministic recovery.

---

# SDLC PHASE BREAKDOWN (Authoritative)

---

## Phase 0 — Repository & Execution Baseline

### Goal

Establish a deterministic, inspectable runtime environment before any agent logic exists.

### Code to Produce

```
/app
  /ui
  /runtime
  /tools
  /state
  main.py
.env.example
```

### Responsibilities

* Load `.env`
* Resolve absolute workspace root
* Enforce allowed filesystem boundaries
* No agent execution yet

### Interfaces

* **Input:** absolute path to workspace
* **Output:** initialized directory structure

### Acceptance Criteria

* App starts without agent
* Workspace is validated
* No writes occur outside root

---

## Phase 1 — Workspace Bootstrap & State Model

### Goal

Make the workspace a **controlled system** with persistent state.

### Code to Produce

```
/state
  project_state.py
  state_schema.py
```

### Behaviors

* Create:

  ```
  documents/
    PHASES/
    DECISIONS/
    RUN_LOGS/
    _archive/
  .agent_ide/
    artifacts/
    project_state.json
  ```
* Store:

  * workspace root (absolute)
  * phase status
  * pending proposal pointers
  * last checkpoint id

### Interfaces

* `initialize_workspace(path) -> state`
* `load_state()`
* `update_state(partial)`

### Acceptance Criteria

* Idempotent initialization
* State survives restart
* No agent execution possible yet

---

## Phase 2 — Document System (DocOps)

### Goal

Make **documents the source of truth**.

### Code to Produce

```
/tools
  doc_writer.py
/runtime
  docops.py
```

### DocOps Actions

* `CreateDoc`
* `RewriteDoc` (archive old)
* `AppendDoc`
* `CreatePhaseDoc`

### Rules

* Rewrite → move old doc to `_archive/`
* All doc writes go through DocOps proposals
* No silent document mutation

### Interfaces

* Input: DocOps proposal JSON
* Output: document files + artifact

### Acceptance Criteria

* Docs cannot be written without approval
* Archive directory populated on rewrite
* Run logs reference doc artifacts

---

## Phase 3 — Unified Proposal & Approval System

### Goal

Single approval model for **everything**.

### Code to Produce

```
/runtime
  proposal.py
  approval_state_machine.py
```

### Proposal Types

* `DocOpsProposal`
* `PatchOpsProposal`

### Approval Gates

* **Gate A:** Documentation
* **Gate B:** Code / Patch execution

### States

```
Draft → Validated → AwaitingApproval → Approved → Executed | Rejected
```

### Interfaces

* `submit_proposal(payload)`
* `approve(proposal_id)`
* `reject(proposal_id)`

### Acceptance Criteria

* UI blocks execution without approval
* Proposal history is persistent
* Rejected proposals cannot execute

---

## Phase 4 — PatchOps (Diff-First Code Changes)

### Goal

Turn code changes into **inspectable objects**.

### Code to Produce

```
/tools
  patch_planner.py
/runtime
  patchops.py
```

### PatchOps Model

* File-level only
* Unified diffs
* Pre-hash and post-hash
* Max 3 non-test files per proposal

### Interfaces

* Input: PatchOps proposal
* Output: diff preview + artifact

### Acceptance Criteria

* Diff viewer renders exact changes
* No writes during proposal phase
* Validation fails closed

---

## Phase 5 — Execution Engine (Apply + Verify Loop)

### Goal

Controlled execution with **human verification**.

### Code to Produce

```
/tools
  patch_applier.py
/runtime
  execution_engine.py
```

### Behaviors

* Apply approved PatchOps
* Pause for user-run tests
* Accept pasted output
* Generate repair proposal on failure
* Repair cap = 3

### Interfaces

* `execute(proposal_id)`
* `record_verification(pass|fail, output)`

### Acceptance Criteria

* Execution pauses correctly
* FAIL → repair proposal
* PASS → phase closure

---

## Phase 6 — LangGraph Runtime Orchestration

### Goal

Make the agent **pausable, resumable, debuggable**.

### Code to Produce

```
/runtime
  graph.py
  nodes/
    intake.py
    plan_route.py
    assemble.py
    validate.py
    checkpoint.py
    await_approval.py
    execute.py
    await_verification.py
    close_phase.py
    error_handler.py
```

### Invariants

* No node performs side effects directly
* All side effects go through tools
* Checkpoints written before every pause

### Interfaces

* Event stream → UI
* Resume from checkpoint

### Acceptance Criteria

* Restart resumes correctly
* State + graph stay in sync
* Error paths are visible

---

## Phase 7 — End-to-End Walkthrough (Proof Phase)

### Goal

Prove the system works **for real**.

### Deliverable

* Python + pytest Hello World walkthrough

### Must Demonstrate

* Doc creation
* Patch proposal
* Approval gating
* Failing test
* Repair loop
* Successful closure

### Acceptance Criteria

* Walkthrough reproducible
* Artifacts auditable
* No manual file edits required

---

## Phase 8 — Execution Hardening (Atomicity)

### Goal

Ensure **approved ≠ corrupted**.

### Code to Produce

```
/tools
  atomic_fs.py
```

### Guarantees

* Temp files (same dir)
* Backup + rollback
* Proposal-level atomicity
* Recovery on crash

### Acceptance Criteria

* Kill during apply → recoverable
* Windows locks handled safely
* No partial writes

---

## Phase 9 — Gradio UI Integration

### Goal

Expose the system without breaking invariants.

### UI Panels

* Documents Workspace
* Diff Viewer
* Runtime Console
* Verification Panel

### UI Rules

* UI never writes files
* UI only signals intent / approval / verification
* UI surfaces artifacts, not summaries

### Acceptance Criteria

* All state visible
* All pauses explicit
* No hidden execution

---

## FINAL SYSTEM GUARANTEES (For Review Board)

* No unapproved writes
* No silent failures
* No unrecoverable corruption
* Full audit trail
* Human authority preserved

---

## WHAT THIS DOCUMENT IS

* A **build contract**
* A **review artifact**
* A **non-negotiable execution plan**

## WHAT IT IS NOT

* A chatbot spec
* A generic IDE
* A prompt playground

---

If you want, next we can:

* convert each phase into **Anti Gravity task packets**
* or freeze this and generate **implementation order + dependency graph**

This time, we stayed **on target**.
