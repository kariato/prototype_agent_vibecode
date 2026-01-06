Great—then we lock two more architectural requirements into the spec:

* **All runtime options live in `.env`** (global/app-level and/or per-project overrides).
* **Each project has a persisted state/config file** that captures IDE + agent state and run history pointers (since there’s no git).

Below is the **Design Doc v1.0** (still no code; only high-level pseudo where helpful). This is written as the thing your agent IDE itself would generate into `/documents/`—but here it is as the canonical spec.

---

# Design Doc v1.0 — Document-First Lightweight Agent IDE

**Stack:** Gradio (UI) + Python (server) + OpenAI-compatible LLM provider + LangGraph (agent)
**Mode:** Option A (Strict Patch IDE), no git, approvals required
**Date:** 2026-01-06

## 1) Purpose

Provide a lightweight, local-first “agent IDE” that:

* plans changes in **documents first**
* executes changes through **reviewable patches**
* requires **explicit approval**
* generates **unit tests for every code phase**
* persists project state without relying on git

---

## 2) Core Principles (Non-negotiable)

1. **Document-first:** no code patch is generated before the outline/phase docs exist and are approved.
2. **Strict patching:** file changes are only applied via validated patch artifacts (diff hunks + hashes).
3. **Small phases:** each phase changes ≤3 non-test files, ≤200 LOC total (configurable).
4. **Approval gates:** at least:

   * Gate A: approve docs
   * Gate B: approve patch apply
5. **Local-only workspace:** agent is sandboxed to a chosen local folder.
6. **No git required:** traceability via `/documents/` + patch artifacts + state files.
7. **Config-driven:** app options live in `.env`; per-project state in a project config file.

**Critique:** These principles must be enforced by the state machine, not just “guidelines.” If any are optional, the agent will eventually violate them.

---

## 3) Terminology

* **Workspace:** The local folder selected by the user containing a software project.
* **Project:** A workspace with a valid `project_state` file and `/documents/`.
* **Phase:** A small, bounded unit of work described in a phase doc and executed as a patch.
* **Patch Artifact:** A saved diff file plus metadata (hashes, timestamps).
* **Run:** One complete agent attempt for a phase step (doc draft, patch proposal, repair, etc.).

---

## 4) Repository layout requirements

### Required directories

At workspace root:

* `/documents/`

  * `PROJECT_OUTLINE.md`
  * `/PHASES/`
  * `/DECISIONS/` (ADR)
  * `/RUN_LOGS/`
  * `/_archive/<timestamp>/...`

### Required project state file

* `/.agent_ide/project_state.json` (or `.yaml` if you prefer; pick one)

  * Contains current phase index, approvals, applied patch history, configuration pointers, etc.

**Rationale:** keeping state under a dedicated hidden-ish folder avoids polluting the project while still being versionable later if git is added.

---

## 5) Configuration model

### 5.1 `.env` (runtime options)

A single `.env` governs the application defaults (and optionally supports per-project overrides).

**Categories**

1. **Provider**

   * provider base URL
   * model name
   * api key ref
   * timeouts, retry policy
2. **Safety**

   * allowed root path(s)
   * maximum diff size
   * maximum files changed
   * allow/deny directories
   * command allowlist
3. **Workflow**

   * require doc approval (true)
   * require patch approval (true)
   * phase size limits
   * archive-on-rewrite (true)
4. **UI**

   * streaming on/off
   * max context files
   * display toggles

**Rule:** If an option affects behavior, it must be in `.env` (or explicitly declared immutable/hard-coded in the design doc).

**Critique:** If you scatter these across constants + UI toggles + hidden defaults, you’ll never be sure what behavior produced a patch.

### 5.2 Per-project state/config file (`project_state.json`)

This file persists:

* workspace identity (path, created time)
* document pointers and versions
* phase list + status
* approvals log (who/when; in single-user this is “user”)
* patch history (file path to diff artifacts, metadata)
* verification history (pasted outputs and outcome)
* current operating mode (strict, always approvals)
* language/framework detection outputs

**Rule:** The agent can read/update this state file only through the same gated process (documented + patch). The app itself may write it as part of state transitions, but those writes must be logged to `/documents/RUN_LOGS`.

**Critique:** If you let the app mutate project state “silently,” you lose auditability. The run log must reflect it.

---

## 6) Document-first workflow

### 6.1 Phase 0: Project Outline

Agent creates:

* `/documents/PROJECT_OUTLINE.md`
* `/documents/PHASES/phase_01_<slug>.md` ... `phase_NN_<slug>.md`

**Archive rule:** If any of these already exist, move old versions to:
`/documents/_archive/<YYYYMMDD_HHMMSS>/...`

### 6.2 Execution cycle per phase

Each phase follows this sequence:

**S1 Draft Phase Doc → Gate A Approve Docs → S2 Retrieve Context → S3 Propose Patch → Gate B Approve Patch → S4 Apply Patch → S5 User Verification → S6 Close Phase**

Unit tests are included in S3.

If verification fails:

* agent writes “Fix attempt #k” in the phase doc (archive previous)
* proposes a minimal repair patch
* re-enters Gate B

---

## 7) Phase size enforcement (small phases)

A valid phase must specify:

* ≤3 non-test files in “Files to change”
* ≤200 LOC expected change (informational, enforced after patch proposal)
* explicit acceptance criteria

If patch exceeds limits:

* agent must split the phase into:

  * Phase NN (reduced scope)
  * Phase NN+1 (carry-over)
* and update `PROJECT_OUTLINE.md` accordingly (archiving prior version)

---

## 8) Patch system specification (strict)

### 8.1 Patch metadata requirements

Each proposed patch includes:

* patch id
* timestamp
* phase id
* list of file operations
* pre-image hash per touched file
* risk flags (delete, new deps, large diff)

Saved to:

* `/documents/RUN_LOGS/patch_<timestamp>_phaseNN.diff`
* plus a small metadata record in the run log markdown

### 8.2 Allowed operations (v1)

* Create file
* Update file
* Delete file (requires extra confirmation checkbox in UI)

### 8.3 Validation rules

Before apply:

* all updated files must match expected pre-hash
* all hunks apply cleanly
* all paths must be within workspace root
* denylist directories must not be touched

---

## 9) Verification model (user-run)

### 9.1 Test creation requirement

Every code phase must include unit tests aligned to acceptance criteria.

### 9.2 Test execution

User runs tests manually (v1). The app provides:

* suggested commands (detected framework)
* “Copy command” buttons
* textbox for user to paste output

Agent uses pasted output to decide:

* PASS: close phase
* FAIL: propose fix patch

### 9.3 Lint (nice-to-have)

If lint config exists, agent suggests lint commands and may add lint config in a dedicated small phase (to avoid mixing lint setup with feature work).

**Critique:** Bundling “add lint tooling” into every phase will explode your diffs and wreck the “small phase” discipline.

---

## 10) UI design (Gradio)

### 10.1 Panels

**Left**

* Workspace selector
* Repo tree + search
* “Documents” quick list

**Center**

* Chat (user + agent)
* Messages tagged by type: DOC / PLAN / PATCH / VERIFY

**Right Tabs**

1. Documents viewer (focus on `/documents`)
2. Phase doc viewer (current phase)
3. Proposed Patch diff viewer
4. Run Logs
5. Trace (tool call summary)

### 10.2 Approval gates in UI

A persistent “Phase Control Bar” shows:

* current state (S1–S6)
* current phase
* next required approval
* buttons enabled only when appropriate

Gate A view shows:

* phase doc markdown
* checklist with explicit items (objective, file list, acceptance criteria, tests)

Gate B view shows:

* patch summary (files changed, LOC, risk)
* full diff viewer
* Approve & Apply / Reject / Request Revision

---

## 11) Agent architecture (LangGraph)

### 11.1 Graph nodes

* `Intake`
* `OrientWorkspace`
* `DraftOutlineDocs`
* `AwaitDocApproval` (Gate A)
* `RetrievePhaseContext`
* `DraftPhasePatch`
* `AwaitPatchApproval` (Gate B)
* `ApplyPatch`
* `AwaitUserVerification`
* `ClosePhase`
* loop: `Repair` path on failure

### 11.2 State (conceptual)

* `workspace_root`
* `project_state_path`
* `current_phase`
* `constraints` (from `.env` + UI)
* `doc_paths`
* `phase_plan`
* `proposed_patch`
* `approval_records`
* `verification_outputs`

### 11.3 Tool access policy

Agent cannot directly write files except via:

* “write doc file” tool (restricted to `/documents`)
* “propose patch” tool (no apply)
* “apply patch” tool (only after approval)

---

## 12) State persistence + run logging

### 12.1 Run log format

Each significant step appends a markdown log entry to:

* `/documents/RUN_LOGS/run_<timestamp>_phaseNN.md`

Includes:

* step name
* inputs (summaries)
* outputs (links to docs/patch files)
* approvals (who/when)
* verification output pasted by user (or excerpt)

### 12.2 Project state updates

When the state machine transitions (e.g., Gate A approved), the app:

* updates `project_state.json`
* writes a run log entry referencing what changed

---

## 13) Security & safety

* Strict path sandboxing
* Denylist protection (e.g., `.env`, secrets)
* Patch secret scanning before apply
* Command execution disabled in v1 (user-run verification)
* Diff size caps + file count caps

---

## 14) MVP acceptance criteria (for the IDE product)

The IDE is “v1 complete” if:

1. User selects a local folder and the app scans it.
2. `/documents` is created and populated with outline + phase docs (archiving any existing).
3. UI blocks patch generation until Gate A doc approval.
4. Agent produces patches as diff artifacts and UI blocks apply until Gate B approval.
5. Patch apply changes files and logs everything to `/documents/RUN_LOGS`.
6. Agent generates unit tests for at least Python and JS projects.
7. User can paste test output; agent can propose a repair patch and re-enter Gate B.

---

## 15) High-level pseudo flows (no code)

### 15.1 Phase execution (conceptual)

```
on UserRequest:
  Intake → OrientWorkspace
  if no outline or request implies new work:
    DraftOutlineDocs → GateA
  for each phase:
    DraftPhaseDoc → GateA
    RetrieveContext
    DraftPatch → GateB
    ApplyPatch
    ask User to run tests; collect output
    if tests pass: ClosePhase
    else: Repair loop (doc update + patch)
```

### 15.2 Document rewrite + archive

```
before writing doc_path:
  if doc_path exists:
    move doc_path → /documents/_archive/<timestamp>/<relative_doc_path>
  write new content → doc_path
```

---

## Two remaining sharp edges (decide now)

1. **Per-project `.env` override**: do you want `/workspace/.env` to override app `.env`?

   * Option: allow but forbid storing API keys in project repo (to avoid accidental sharing later).
2. **Project state file format**: JSON vs YAML.

   * JSON is stricter and tool-friendly; YAML is more human-editable but more error-prone.

If you don’t answer, default is:

* **No per-project `.env` overrides** (safer)
* **JSON** for `project_state.json`

We can now convert this into the initial contents of:

* `PROJECT_OUTLINE.md` (for the IDE project itself)
* `phase_01_bootstrap.md` (UI skeleton + state machine wiring)
* `phase_02_documents.md` (document system + archive)
* `phase_03_patchops.md` (patch artifact pipeline + apply gating)
* `phase_04_tests.md` (test generation contract + verification UI)

…and keep the phases small per your rule.
