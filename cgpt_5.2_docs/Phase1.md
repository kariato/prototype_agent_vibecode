Below is the **PROJECT_OUTLINE.md** exactly as it should be created in
`/documents/PROJECT_OUTLINE.md`.

This is **not marketing fluff**. It is a control document that constrains the agent and the workflow. Every later phase must trace back to this.

---

# Project Outline

**Project Name:** Document-First Lightweight Agent IDE
**Status:** Draft (v1)
**Last Updated:** 2026-01-06

---

## 1. Purpose

This project defines and implements a **local-first, document-driven, agent-assisted IDE** that enables structured software development through:

* mandatory documentation before code
* strictly reviewed and approved patches
* small, bounded implementation phases
* explicit unit test generation
* persistent state without relying on git

The system is designed to be **general-purpose**, **safe by default**, and **auditable**, prioritizing correctness and traceability over speed or automation.

---

## 2. Core Design Principles (Hard Constraints)

These principles are **non-negotiable** and must be enforced by the system state machine.

1. **Document-First Execution**

   * No code patch may be proposed until documentation exists and is approved.
   * All planning is captured in Markdown documents under `/documents`.

2. **Strict Patch Application**

   * All code changes occur via validated patch artifacts.
   * Direct file writes by the agent are forbidden outside `/documents`.

3. **Small Phases**

   * Each phase:

     * touches **≤ 3 non-test files**
     * introduces **≤ 200 LOC** of change
     * has **one primary objective**

4. **Explicit Approval Gates**

   * Documentation approval (Gate A)
   * Patch approval before apply (Gate B)

5. **Unit Tests Are Mandatory**

   * Every code-changing phase must include unit tests aligned to acceptance criteria.
   * Tests are executed by the user and results are captured.

6. **Local-Only Workspace**

   * The agent is sandboxed to a user-selected local folder.
   * No network access or external execution is required.

7. **Config-Driven Behavior**

   * Runtime options live in `.env`
   * Per-project state is persisted in a project config file

8. **No Git Dependency**

   * Traceability is achieved through:

     * archived documents
     * patch artifacts
     * run logs
     * persisted project state

---

## 3. Target Users

* Technical users building or modifying software locally
* Users who want:

  * controlled AI assistance
  * explainable, reviewable changes
  * structured iteration
  * auditability without heavyweight tooling

This system is **not** optimized for beginners, nor for unattended automation.

---

## 4. Non-Goals

The system explicitly does **not** aim to:

* Replace full IDEs (debuggers, profilers, refactor engines)
* Provide autonomous agents that modify code without approval
* Support multi-user collaboration (initially)
* Implement CI/CD pipelines
* Act as a git replacement (git may be added later but is not required)

---

## 5. Repository & Document Structure

Each project workspace must contain:

```
/documents/
  PROJECT_OUTLINE.md
  /PHASES/
  /DECISIONS/
  /RUN_LOGS/
  /_archive/<timestamp>/
.agent_ide/
  project_state.json
```

### Document Rules

* All documents are Markdown (`.md`)
* Rewrites require archival of previous versions
* Run logs are append-only

---

## 6. Workflow Overview

### Phase 0: Project Planning

* Create `PROJECT_OUTLINE.md`
* Define all implementation phases
* No code changes permitted

### Per-Phase Execution

Each phase follows:

1. Draft phase documentation
2. **Gate A:** User approves documentation
3. Retrieve relevant code context
4. Draft patch + unit tests
5. **Gate B:** User approves patch
6. Apply patch
7. User runs tests and pastes results
8. Phase is closed or enters repair loop

---

## 7. Phase Definition Requirements

Each phase must define:

* Objective
* Scope and non-goals
* Files to change (explicit paths)
* Acceptance criteria
* Unit test plan
* Manual test commands
* Risks and rollback
* Approval checklist

Phases that exceed size or complexity limits must be split.

---

## 8. Configuration Model

### Global Runtime Configuration

* Stored in `.env`
* Controls:

  * provider settings
  * safety limits
  * workflow enforcement
  * UI behavior

### Per-Project State

* Stored in `.agent_ide/project_state.json`
* Tracks:

  * phase progress
  * approvals
  * applied patches
  * verification outcomes
  * detected languages/frameworks

---

## 9. Safety Model

The system enforces:

* strict filesystem sandboxing
* denylisted paths (e.g., secrets, `.env`)
* patch size and file count limits
* explicit deletion confirmation
* full logging of all state transitions

---

## 10. Definition of Done (Project-Level)

This project is considered complete when:

1. A user can select a local folder and initialize a project.
2. Documentation is created and enforced before any code change.
3. Approval gates prevent unauthorized patch application.
4. Patches are generated, reviewed, applied, and logged.
5. Unit tests are created for every code phase.
6. Verification results are captured and traceable.
7. All actions are auditable via `/documents`.

---

## 11. Planned Implementation Phases (Initial)

1. **Phase 01 – Project Bootstrap**

   * Workspace selection
   * Document system initialization
   * Project state file creation

2. **Phase 02 – Document & Archive System**

   * Document writing rules
   * Rewrite + archive mechanism

3. **Phase 03 – Approval State Machine**

   * Gate A / Gate B enforcement
   * UI state transitions

4. **Phase 04 – Patch Artifact Pipeline**

   * Patch proposal, validation, apply
   * Diff viewer

5. **Phase 05 – Unit Test Contract**

   * Test generation expectations
   * Verification workflow

6. **Phase 06 – LangGraph Agent Wiring**

   * Node graph
   * Tool gating
   * Repair loops

---

## 12. Change Management

* Any modification to this outline:

  * requires archival of the previous version
  * must be explicitly logged
  * may require re-approval of dependent phases

---

## 13. Open Questions (Tracked)

* Whether per-project `.env` overrides are allowed
* Whether project state should remain JSON or migrate to YAML
* Whether limited command execution should be allowed in later versions

These are intentionally deferred and must be resolved via documented decisions (ADR).

---

If you want, the **next correct move** (by your own rules) is:

**Phase 01: Project Bootstrap**
→ create `/documents/PHASES/phase_01_project_bootstrap.md`

Say *“Create Phase 01 doc”* and I’ll generate it exactly to the locked template, ready for Gate A approval.

✔ **Phase 01 Docs Approved — Gate A passed**

We now transition the state machine exactly as specified.

---

## State Transition

**From:**
`S1 — Draft Phase Doc`

**To:**
`S2 — Retrieve Context (Phase 01)`

What this *means* in practice (and what it explicitly does **not** mean):

* ✅ The phase definition is now frozen as the controlling contract
* ✅ We are allowed to reason about *implementation planning*
* ❌ We are **not** allowed to apply patches yet
* ❌ We are **not** allowed to touch files outside the declared scope
* ❌ We are **not** allowed to change the phase doc without archiving

---

## What Happens Next (by design)

The **only valid next artifact** is a **Phase 01 Implementation Plan**, which will:

* Translate the accepted phase doc into:

  * concrete initialization steps
  * filesystem invariants
  * state file structure (high-level schema, not code)
* Identify:

  * bootstrap entry point (conceptual)
  * failure modes
  * idempotency guarantees
* Define:

  * what “rerunning bootstrap” must do vs must not do
* Prepare the ground for a **patch proposal** *without yet producing one*

This plan is *not* a patch.
It is the bridge between documentation and PatchOps.

---

## Critical Design Check (before I generate it)

I need to resolve **one ambiguity** that directly affects the bootstrap plan:

### Question (design-critical, not procedural)

When bootstrapping an **existing workspace** that already has a `/documents/` directory:

Which rule should apply?

**Option A — Conservative (recommended)**

* Treat existing `/documents/` as authoritative
* Only create missing subdirectories
* Never rewrite or archive docs during bootstrap

**Option B — Strict Reset**

* Archive entire existing `/documents/` directory
* Recreate fresh structure and outline

Your earlier constraints *imply* Option A, but they do not state it explicitly — and bootstrap behavior must be deterministic.

---

### Why this matters (critique)

If this is not fixed **now**, you will later get:

* accidental doc rewrites during “initialization”
* archive spam
* or worse: silent divergence between project state and documents

Bootstrap must be **idempotent and non-destructive** by definition.

---

## Pending State

We are paused at:

**`S2 — Retrieve Context (Phase 01)`**

No files will be touched until you answer:

> **Option A or Option B for existing `/documents/` during bootstrap?**

Once you answer, I will produce:

### 📄 Phase 01 — Implementation Plan (High-Level, No Code)

* structured steps
* invariants
* state schema outline
* failure/rollback logic
* ready to proceed to **Patch Proposal (Gate B)**

Your move.
Good. Option A makes bootstrap **idempotent** and non-destructive, which is exactly what you need in a no-git world.

## Phase 01 Implementation Plan (High-Level, No Code)

**Artifact:** `Phase 01 — Implementation Plan` (this is planning, not a patch)
**State:** `S2 Retrieve Context → S3 Propose Patch (next)` only after this plan is accepted

---

### 1) Inputs and invariants

**Inputs**

* `workspace_root` (user-selected local folder)
* Global `.env` (app runtime config)
* Existing workspace contents (may be empty or already a project)

**Hard invariants**

* All paths must resolve under `workspace_root` (no `..`, symlinks escaping root)
* Bootstrap must not modify any file outside the Phase 01 scope:

  * `/documents/**` (directory creation only, no doc rewrite)
  * `/.agent_ide/project_state.json` (create if missing; update only minimal bootstrap fields)
  * `/documents/RUN_LOGS/**` (append-only new log file)
* If `/documents/` exists: **do not rewrite** anything; only create missing subdirs.

**Config invariants**

* App reads `.env` for:

  * allowlisted base directories (optional)
  * denylisted paths
  * limits (phase caps exist but not enforced here beyond “don’t touch other files”)
  * logging verbosity
  * provider settings are allowed to exist but must not be required for bootstrap success

---

### 2) Bootstrap decision tree

**Step 1: Validate workspace_root**

* Confirm directory exists
* Confirm writable (create/delete temp file within root OR equivalent safe check)
* Confirm root is allowed (if `.env` specifies allowed roots)
* Reject if root contains forbidden markers (optional; e.g., OS root)

**Step 2: Detect whether workspace is already “initialized”**

* Condition: `/.agent_ide/project_state.json` exists and is valid JSON
* Condition: `/documents/` exists
* This yields 4 states:

  1. Neither exists → brand new
  2. documents exists, state missing → partial init
  3. state exists, documents missing → partial init
  4. both exist → initialized

**Step 3: Apply Option A behavior**

* If documents exist:

  * create only missing subdirectories
  * do **not** archive or rewrite any markdown docs
* If state exists:

  * validate minimal schema
  * migrate only if required for bootstrap completeness (see state schema below)
  * never delete unknown fields

---

### 3) Required filesystem operations (concrete but still non-code)

For a given `workspace_root`, ensure these directories exist:

* `/documents/`
* `/documents/PHASES/`
* `/documents/DECISIONS/`
* `/documents/RUN_LOGS/`
* `/documents/_archive/`
* `/.agent_ide/`

**Rules**

* Directory creation is safe and idempotent
* If any path exists as a file where a directory is expected → bootstrap fails with a clear error and logs it

---

### 4) `project_state.json` minimal schema (Phase 01 scope)

This phase initializes only the minimal fields needed to support later phases without forcing premature design decisions.

**Top-level keys (minimum)**

* `schema_version` (integer)
* `created_at` (timestamp)
* `updated_at` (timestamp)
* `workspace`:

  * `root_path` (string)
  * `initialized` (boolean)
* `documents`:

  * `documents_dir` = `"documents"`
  * `outline_path` = `"documents/PROJECT_OUTLINE.md"` (pointer only; do not create in this phase)
* `phases`:

  * `current_phase` = `1` (integer) OR `null` if you prefer “not started”
  * `phase_status` map: `{ "01": "docs_approved" | "not_started" | ... }` (keep minimal)
* `approvals`:

  * list of approval records with:

    * `phase_id`
    * `gate` ("A" or "B")
    * `timestamp`
    * `note` (optional)

**Important constraints**

* If `project_state.json` already exists:

  * preserve unknown keys
  * only add missing required keys
  * only update `updated_at` and `workspace.initialized` as appropriate

**Critique:** Don’t try to finalize the entire state model here. That’s how bootstrap phases bloat. Minimal viable state is the right move.

---

### 5) Run logging plan (Phase 01)

Bootstrap must create a run log file:

* `/documents/RUN_LOGS/run_<timestamp>_phase01_bootstrap.md`

Log sections (fixed headings)

* **Run Metadata** (timestamp, workspace path, phase id)
* **Preflight Checks** (pass/fail results)
* **Filesystem Changes** (created dirs/files)
* **State File Changes** (created/updated + summary)
* **Errors** (if any)
* **Result** (SUCCESS/FAIL)

**Rule**

* Even if bootstrap fails early, it should attempt to write a run log **if `/documents/RUN_LOGS/` exists or can be created safely**. If it can’t, it must present the error in UI.

---

### 6) Idempotency requirements

Running bootstrap multiple times must:

* not rewrite or archive any existing docs
* not remove any directories
* not reset or wipe project_state fields
* only:

  * create missing directories
  * add missing minimal keys to project_state
  * append a new run log entry/file

**Edge cases**

* If directory exists but is read-only → fail with explicit instruction
* If symlink inside workspace points outside and is targeted → must refuse

---

### 7) UI behavior (Phase 01 only)

Minimum UI elements required to support bootstrap:

* Folder picker / path input
* “Initialize / Bootstrap” button
* Read-only status panel:

  * initialized vs partial vs new
  * paths found / created
* Run log viewer (just open the latest run log)

**No other UI is permitted in this phase** (keeps scope tight).

---

### 8) Failure modes + rollback behavior

**Failure modes**

* Workspace not writable
* Expected directory path exists as a file
* `project_state.json` exists but invalid JSON
* `.env` configuration inconsistent (e.g., allowed_roots excludes this path)
* Permission errors

**Rollback**

* This phase does not delete anything automatically (safer)
* If partial creation occurred:

  * log what was created
  * user can manually delete created directories/files if desired
* The key is to avoid destructive rollback that could remove user data.

**Critique:** Automatic rollback is where you accidentally delete user work. Log-only rollback is the correct v1 stance.

---

## Output of this plan

Once we proceed, Phase 01 patch proposal will include **only**:

1. directory creation operations under `/documents` and `/.agent_ide`
2. creation or minimal update of `/.agent_ide/project_state.json`
3. creation of a run log under `/documents/RUN_LOGS`

No other changes.

---

## Next state transition

If you accept this plan, we move to:

**`S3 — Propose Patch (Phase 01)`**
…and I will produce a **Patch Proposal Summary** (not code) that enumerates the exact filesystem operations and the exact initial JSON structure to be written—ready for Gate B approval.

### Probe (design-critical)

Do you want `project_state.json` to store absolute `root_path`, or store it as `"."` and let the app bind it at runtime?

* **Absolute path**: simpler, but less portable if you move the folder.
* **Relative (“.”)**: more portable, but you must always know the binding root.

If you don’t answer, I’ll default to **absolute path** because this is a local-only tool and it reduces ambiguity.
