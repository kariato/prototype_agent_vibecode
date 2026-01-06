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
