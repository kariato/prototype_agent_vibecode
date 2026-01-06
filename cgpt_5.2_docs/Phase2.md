Locked in: **absolute path** goes into `project_state.json`. That removes ambiguity and simplifies every later guardrail (path validation, archive resolution, run logs).

We now advance **exactly one step** per the state machine.

---

# Phase 01 — Patch Proposal Summary (Gate B Prep)

**Phase:** 01 — Project Bootstrap
**State:** `S3 — Propose Patch`
**Type:** Structural filesystem + state initialization
**No code, no logic, no agent wiring**

This is the **only** set of changes that will be proposed for Phase 01.
If anything outside this list appears later, that is a spec violation.

---

## 1) Patch Scope (Strict)

### Allowed operations

* Create directories
* Create a new file
* Minimal update to an existing file (state file only, additive)

### Explicitly forbidden

* Modifying any source code files
* Modifying `.env`
* Rewriting or archiving any existing documents
* Creating any markdown docs other than a run log
* Adding tests (planned but not implemented here)

---

## 2) Filesystem Operations (Exact)

### A) Directory creation (idempotent)

The patch will **ensure existence** of the following directories under `workspace_root`:

```
/documents/
  /PHASES/
  /DECISIONS/
  /RUN_LOGS/
  /_archive/
/.agent_ide/
```

**Rules**

* If directory exists → no-op
* If path exists as a file → fail bootstrap, log error
* No directory outside this list may be created

---

### B) Project state file creation or update

**Path**

```
/.agent_ide/project_state.json
```

#### Case 1: File does not exist

Create it with the **minimal schema** below.

#### Case 2: File exists

* Parse and validate JSON
* Add missing required keys only
* Preserve unknown keys
* Update `updated_at`
* Do **not** delete or rename any fields

---

## 3) `project_state.json` — Initial Content (Conceptual Schema)

> This is structure, not implementation code.

```text
{
  schema_version: 1,
  created_at: <timestamp>,
  updated_at: <timestamp>,

  workspace: {
    root_path: "<absolute_path_to_workspace>",
    initialized: true
  },

  documents: {
    documents_dir: "documents",
    outline_path: "documents/PROJECT_OUTLINE.md"
  },

  phases: {
    current_phase: 1,
    phase_status: {
      "01": "docs_approved"
    }
  },

  approvals: [
    {
      phase_id: "01",
      gate: "A",
      timestamp: <timestamp>,
      note: "Phase 01 docs approved"
    }
  ]
}
```

### Notes

* `root_path` is **absolute**, per your decision
* `phase_status` explicitly records that Gate A has already passed
* This file contains **state**, not intent — intent lives in markdown docs
* Future phases may extend this schema, but Phase 01 must not anticipate them

---

## 4) Run Log Artifact

### New file created

```
/documents/RUN_LOGS/run_<timestamp>_phase01_bootstrap.md
```

### Required sections (fixed)

* **Run Metadata**

  * timestamp
  * phase id
  * workspace root (absolute path)
* **Preflight Checks**

  * directory exists
  * writable
* **Filesystem Changes**

  * directories created (list)
  * files created/updated (list)
* **State Initialization**

  * project_state.json created or updated
  * keys added (summary)
* **Errors**

  * empty if successful
* **Result**

  * SUCCESS or FAIL

**Rule**

* This file is append-only and never rewritten
* If bootstrap fails partway, this file must still exist if possible

---

## 5) Risk Assessment (Phase 01)

### Identified risks

* Incorrect absolute path resolution
* Permissions errors on directory creation
* Existing invalid `project_state.json`

### Mitigations

* Fail fast with explicit error messages
* Never delete or overwrite existing content
* Log all partial progress

**Overall risk:** LOW
**Rollback strategy:** Log-only, no destructive rollback

---

## 6) Phase Size Check (Compliance)

* Non-test files touched: **1**

  * `/.agent_ide/project_state.json`
* Directories created: allowed
* LOC added: minimal, within limits
* Single objective: ✔

This phase fully complies with **Small Phase** constraints.

---

## 7) Gate B — Pending Approval

Before applying this patch, confirm:

* [ ] Only listed directories will be created
* [ ] Only `project_state.json` will be created or minimally updated
* [ ] No documents will be rewritten or archived
* [ ] Absolute path is stored in state
* [ ] A run log will be created regardless of success or failure

---

### Gate B Status

⛔ **Not Approved**

---

## Next Valid Actions (choose one)

1. **Approve Phase 01 Patch**
   → patch is applied, directories/state/log created, Phase 01 moves to verification

2. **Reject with changes**
   → specify exactly what to alter (scope, fields, logging)

3. **Request revision**
   → e.g. “add extra state field”, “change run log structure”

No other action is allowed by the state machine.

Your move.

You’re trying to jump ahead **without creating the Phase doc**, which breaks the very system you’re building. If you let yourself do that once, you’ll do it again, and your “document-first IDE” becomes theatre.

So: we do this properly.

## Phase 02 Doc: Documents UI + DocOps Command Protocol

Create this at:

`/documents/PHASES/phase_02_documents_ui_and_docops.md`

---

# Phase 02 — Documents UI + DocOps Command Protocol

**Phase ID:** 02
**Status:** Draft
**Last Updated:** 2026-01-06

---

## 1. Objective

Define and implement the **document creation workflow** in the IDE, including:

* a Gradio UI focused on `/documents`
* a machine-parseable **DocOps** command protocol that packages “create/overwrite/archive document” into explicit agent actions
* strict guardrails so the agent can only write within `/documents` and must archive before rewrite

This phase establishes how the user and agent collaboratively generate the **project outline + phase docs + ADRs + run logs** under approvals.

---

## 2. Scope

This phase is limited to:

* UI panels and controls required to:

  * view `/documents`
  * request creation of `PROJECT_OUTLINE.md`
  * request creation of `PHASES/phase_XX_*.md`
  * approve/reject document outputs (Gate A)
  * show archive history for rewritten docs
* Definition of a **DocOps protocol** (structured actions) including:

  * CreateDoc
  * RewriteDoc (with archival)
  * AppendLog
  * CreatePhaseDoc (templated)
  * CreateADR (templated)
* Mapping DocOps → LangGraph “agent actions” (node/tool boundaries), without implementing broader PatchOps yet
* Rules for doc rewrite + archive (Option 2: rewrite current, archive old)

---

## 3. Non-Goals

This phase explicitly does **not**:

* Implement PatchOps or apply code changes
* Run tests or commands
* Implement full Approval Gate B (patch approval)
* Implement LangGraph repair loops
* Add repo-wide code search features (beyond what’s needed for doc creation)
* Modify anything outside `/documents` (except minimal state transitions already defined in Phase 01)

If PatchOps approval controls appear here, the phase must be split.

---

## 4. Files to Change (Max 3, Excluding Tests)

This phase is permitted to create/modify only:

1. `/documents/*` (create/rewrite/archive docs + add run logs)
2. `/.agent_ide/project_state.json` (update doc-related state only)
3. `/documents/RUN_LOGS/*` (append-only new log files)

No other project files may be modified.

---

## 5. Acceptance Criteria

This phase is complete when:

* The UI has a “Documents” workspace that can:

  * list docs under `/documents`
  * open and display selected doc content
* The user can trigger doc generation actions:

  * Create/Rewrite `PROJECT_OUTLINE.md`
  * Create a new Phase doc using the locked template
  * Create an ADR doc using an ADR template
* Any doc rewrite automatically archives the old version to:

  * `/documents/_archive/<timestamp>/<relative_path>`
* Agent outputs doc edits as **DocOps actions** in a structured, parseable format
* The UI shows a preview of proposed doc changes and requires **Gate A approval** before writing
* All doc writes and approvals create a run log entry in `/documents/RUN_LOGS/`

---

## 6. Unit Test Plan

Unit tests are required for:

* Archive path generation correctness
* Rewrite behavior (existing doc archived before new write)
* DocOps parsing and validation (schema correctness, path sandbox)
* UI approval gate enforcement (no write without approval)

Tests must be local-only and deterministic.

---

## 7. Manual Commands

Document (do not execute here):

* How to start IDE
* How to bootstrap a workspace
* How to generate/rewrite outline and phase docs
* How to inspect archive history

---

## 8. Risks and Rollback

### Risks

* Agent writes outside `/documents`
* Accidental overwrite without archive
* DocOps format drifts and becomes unparseable
* UI allows write without approval

### Rollback

* No destructive rollback
* All doc operations are reversible via archived copies
* Fail closed: if parsing/validation fails, do not write

---

## 9. Approval Checklist (Gate A)

* [ ] UI scope is strictly documents-related
* [ ] DocOps protocol is machine-parseable and validated
* [ ] Rewrite requires archive and is enforced
* [ ] No PatchOps, no tests execution, no repo code edits
* [ ] Acceptance criteria are objectively verifiable

---

## 10. Changelog

* **2026-01-06** — Initial draft created by Agent

---

## 11. Verification Results

*(Empty until implemented and verified.)*

---

### Gate A Status

⛔ **Not Approved**

---

If you approve Phase 02 docs, we move to designing (still no code):

1. **Gradio Documents UI spec (exact widgets + states)**
2. **DocOps protocol schema + examples**
3. **LangGraph node/action mapping for doc creation**

---

# Now: the design content you asked for (preview, not yet “approved implementation”)

You asked specifically: **“Gradio UI and prompt commands to package these items into agent actions for creating documents.”** Here are the designs we’ll finalize immediately after you approve Phase 02.

---

## A) Gradio UI Design for Documents (Document-only workspace)

### Panels / Tabs

**Left**

* Workspace root (readonly display)
* Documents tree (only `/documents`)
* Filter: Outline / Phases / ADRs / Run logs / Archive

**Center**

* Chat (user prompts + agent outputs)
* Message types: `DOC_REQUEST`, `DOCOPS_PROPOSAL`, `DOC_APPROVAL`, `DOC_WRITE_RESULT`

**Right Tabs**

1. **Doc Preview**

   * rendered markdown
   * raw markdown toggle
2. **Proposed DocOps**

   * structured actions viewer
   * validation results (pass/fail + why)
3. **Archive Viewer**

   * pick doc → show archived versions list by timestamp
4. **Run Log**

   * latest run log rendered

### Required Buttons (doc-only)

* **Create / Rewrite Project Outline**
* **Create Next Phase Doc**
* **Create ADR**
* **Approve Docs (Gate A)**
* **Reject Docs**
* **Write Docs** (only enabled after approval)
* **Revert from Archive** (optional; safe because it’s just a RewriteDoc with archive)

### UI State model (doc-only)

* `Idle`
* `DocOps Proposed`
* `DocOps Approved`
* `Writing`
* `Written / Error`

**Critique:** if “Write Docs” is enabled anytime other than `DocOps Approved`, you’ve violated your own safety model.

---

## B) DocOps Protocol (structured agent actions)

You need a format that is:

* trivial to parse
* stable over time
* explicit about intent
* safe by default

### Option 1 (recommended): JSON “DOCOPS” block

Agent must output **exactly one** block:

```text
<DOCOPS>
{
  "version": 1,
  "actions": [
    { "type": "RewriteDoc", "path": "documents/PROJECT_OUTLINE.md", "content": "...", "archive": true },
    { "type": "CreateDoc", "path": "documents/PHASES/phase_02_documents_ui_and_docops.md", "content": "..." },
    { "type": "AppendLog", "path": "documents/RUN_LOGS/run_YYYYMMDD_HHMMSS_phase02.md", "content": "..." }
  ]
}
</DOCOPS>
```

### Allowed actions (Phase 02)

* `CreateDoc(path, content)`
* `RewriteDoc(path, content, archive=true)` (archive must be true for existing docs)
* `AppendLog(path, content)`
* `CreatePhaseDoc(phase_id, slug, content)` → expands into CreateDoc
* `CreateADR(adr_id, slug, content)` → expands into CreateDoc

### Validation rules (must fail closed)

* All `path` must begin with `documents/`
* No absolute paths
* No `..`
* If `RewriteDoc` targets an existing file, `archive` must be true
* Archive target path is computed by the app, not the agent (prevents tricks)

**Critique:** Do not let the model propose archive paths. The model will eventually mess it up or be exploited. The app computes the archive destination.

---

## C) Prompt Commands (how the user asks / how the agent responds)

### User “prompt commands” in chat (human friendly, deterministic)

* `@docs:outline create`
* `@docs:outline rewrite`
* `@docs:phase create 03 approval-state-machine`
* `@docs:adr create 0001 docops-protocol`
* `@docs:show phase 02`

These are **UI shortcuts** that the app translates into structured agent inputs.

### Agent response contract

Agent must respond with:

1. a short explanation (plain text)
2. exactly one `<DOCOPS>...</DOCOPS>` block

No other side-channel formats.

---

## D) Mapping DocOps to LangGraph agent actions

### Node split (doc-only)

* `DocIntake` → interpret user command into doc intent
* `DocDraft` → generate markdown content
* `DocOpsEmit` → emit structured actions block
* `AwaitDocApproval` → UI gate
* `DocWrite` (tool call) → executes actions (create/rewrite/archive/appendlog)
* `DocWriteReport` → confirmation + log entry

### Tools (doc-only)

* `documents_list()`
* `documents_read(path)`
* `documents_write(actions)`  ← only called after approval
* `documents_archive_on_rewrite(path)` ← internal behavior of write tool
* `runlog_append(path, content)` ← could be part of write tool

---

## What I need from you right now

Say: **“Approve Phase 02 Docs”** (Gate A).
Then I’ll produce the **Phase 02 Implementation Plan** (still no code) that locks:

* exact UI widgets + states
* exact DocOps schema (final)
* exact LangGraph node I/O contracts
* exact validation rules and failure behavior

✔ **Phase 02 Docs Approved — Gate A passed**

You’re now in the only state where it’s legal to define the **Documents UI** and the **DocOps command protocol** as an implementation plan (still no code, but fully concrete).

---

# Phase 02 — Implementation Plan (High-Level, No Code)

**Phase:** 02 — Documents UI + DocOps
**State:** `S2 Retrieve Context → S3 Propose Patch (next)`
**Goal:** Lock UI behavior + DocOps schema + validation + LangGraph action mapping

---

## 1) Phase 02 Deliverables (must exist at end of phase)

### UI Deliverables

* A **Documents Workspace** UI that supports:

  1. browsing `/documents` (including archive and run logs)
  2. previewing markdown
  3. generating doc changes (outline/phase/ADR)
  4. approving/rejecting doc proposals (Gate A behavior)
  5. writing docs only after approval

### Protocol Deliverables

* A stable, parseable **DocOps v1** schema
* A validator spec (“fail closed”) with explicit error messages
* A deterministic mapping: **DocOps → Document Writer tool actions**

### Agent Orchestration Deliverables

* A doc-only LangGraph lane:

  * doc drafting
  * docops emission
  * waiting for approval
  * doc write tool invocation
  * write report + run log entry

### Persistence Deliverables

* `project_state.json` updated with doc-related state:

  * current doc proposal id (if any)
  * last written doc timestamp
  * current phase “02” status changes
* Run logs created for doc writes and approvals

---

## 2) Gradio UI Spec (exact widgets + states)

### 2.1 Layout

**Left Column: Documents Navigator**

* Workspace display (read-only absolute path)
* Documents filter selector:

  * Outline
  * Phases
  * ADRs
  * Run Logs
  * Archive
  * All
* Documents file list (relative paths from `/documents`)
* Search box (filters by filename substring)

**Center Column: Chat + Commands**

* Chat transcript
* Command helper row: buttons that insert canonical commands into chat:

  * `@docs:outline create`
  * `@docs:outline rewrite`
  * `@docs:phase create <NN> <slug>`
  * `@docs:adr create <NNNN> <slug>`
  * `@docs:show <path>`
* Input box
* “Send” button

**Right Column: Tabs**

1. **Doc Preview**

   * Markdown render
   * Toggle: “Raw”
2. **Proposed DocOps**

   * Structured actions viewer (pretty JSON)
   * Validation results panel (pass/fail + messages)
3. **Archive Viewer**

   * If doc selected: list archived versions (timestamped paths)
   * Preview archived content
4. **Run Logs**

   * List runs (newest first)
   * Preview

### 2.2 UI State Machine (doc-only)

Define UI states; buttons enabled only where legal.

* `Idle`

  * No proposal pending
  * Buttons enabled: “Send”, command helpers
* `DocOps_Proposed`

  * A DocOps proposal exists but not approved
  * Buttons enabled: ✅ Approve Docs, ❌ Reject Docs
  * Buttons disabled: Write
* `DocOps_Approved`

  * Proposal approved but not written
  * Buttons enabled: ✍️ Write Docs
* `DocOps_Writing`

  * Write in progress
  * All buttons disabled except “Cancel” (optional)
* `DocOps_Written`

  * Write succeeded; show report
  * Buttons enabled: normal command helpers
* `DocOps_Error`

  * Write failed or validation failed
  * Buttons enabled: “Return to Proposed” or “Discard Proposal”

**Non-negotiable enforcement:** `Write Docs` is enabled *only* in `DocOps_Approved`.

---

## 3) DocOps v1 Protocol (final spec)

### 3.1 Envelope

Agent must emit **exactly one** block per doc proposal:

```text
<DOCOPS>
{
  "version": 1,
  "proposal_id": "<uuid-or-timestamp>",
  "summary": "<1-2 sentences>",
  "actions": [ ... ]
}
</DOCOPS>
```

### 3.2 Allowed actions

All paths are **relative** and must begin with `documents/`.

* `CreateDoc`

  * fields: `type`, `path`, `content`
* `RewriteDoc`

  * fields: `type`, `path`, `content`, `archive` (must be `true`)
* `AppendLog`

  * fields: `type`, `path`, `content`
* `CreatePhaseDoc`

  * fields: `type`, `phase_id`, `slug`, `content`
  * expansion rule: becomes `CreateDoc` at `documents/PHASES/phase_<phase_id>_<slug>.md`
* `CreateADR`

  * fields: `type`, `adr_id`, `slug`, `content`
  * expansion rule: becomes `CreateDoc` at `documents/DECISIONS/ADR_<adr_id>_<slug>.md`

### 3.3 Validation (fail closed)

Reject proposal if any condition fails:

**Schema**

* `version` == 1
* `proposal_id` exists
* `actions` non-empty array
* each action has required fields

**Path rules**

* `path` must start with `documents/`
* no absolute paths
* no `..`
* no null bytes or control characters
* only `.md` extension allowed for CreateDoc/RewriteDoc (except run logs which are `.md` too)

**Rewrite rules**

* If action is `RewriteDoc`, then `archive` must be `true`
* The agent must not supply archive destination paths (app computes)

**Scope rules (Phase 02)**

* Actions may only target:

  * `documents/**`
  * `documents/RUN_LOGS/**`
* No `.agent_ide` writes in this phase through DocOps (state updates are done by app on approval/write)

**Size limits**

* Max actions per proposal: configurable (default 5)
* Max content size per doc: configurable (default e.g. 200 KB)

### 3.4 Write semantics

On “Write Docs”:

1. Expand `CreatePhaseDoc`/`CreateADR` into concrete `CreateDoc` actions.
2. For each `RewriteDoc`, if target exists:

   * archive the old version to `documents/_archive/<timestamp>/<relative_path>`
3. Write new contents.
4. Append a run log entry describing:

   * proposal id
   * actions executed
   * archived paths created
5. Update project state fields related to docs proposals (see section 6).

---

## 4) Agent response contract (prompt discipline)

### Required response structure

Every doc proposal response must include:

1. A short natural-language preface (max ~6 lines) describing what it’s doing
2. One and only one `<DOCOPS>...</DOCOPS>` block

### Forbidden

* Multiple DOCOPS blocks
* Unstructured “here’s the markdown” without DocOps
* Archive path suggestions
* Writing outside documents/

**Critique:** This constraint is what makes the system mechanizable. If you relax it, you’ve built another chatbot.

---

## 5) LangGraph mapping (doc lane only)

### Nodes

* `DocIntake`

  * input: user chat + optional UI command
  * output: `doc_intent` (outline / phase / adr / show)
* `DocDraft`

  * reads existing docs if present
  * produces markdown content + summary
* `DocOpsEmit`

  * produces structured DocOps block
* `AwaitDocApproval`

  * pauses; UI sets approved/rejected
* `DocWriteTool`

  * invoked only if approved
* `DocWriteReport`

  * outputs results; updates logs and state

### Tools (conceptual)

* `documents_list(filter)`
* `documents_read(path)`
* `documents_validate_docops(docops_json)` (validator)
* `documents_apply_docops(docops_json)` (writer with archival)

---

## 6) Project state updates (doc-related only)

Upon proposal creation:

* store:

  * `documents.pending_proposal_id`
  * `documents.pending_actions_count`
  * `documents.pending_targets[]` (paths)
  * `documents.pending_created_at`

Upon approval:

* append approval record:

  * phase “02”, gate “A”, timestamp, note “DocOps proposal approved”
* set `documents.pending_status = "approved"`

Upon write success:

* clear pending proposal fields
* set:

  * `documents.last_write_at`
  * `documents.last_write_proposal_id`
* set phase status for “02” minimally (e.g., `"in_progress"` until verification)

All such changes must be echoed in `/documents/RUN_LOGS/...`.

---

## 7) Verification plan for Phase 02 (user-run)

You verify by:

* generating an outline rewrite (DocOps proposal)
* rejecting once (ensure no write)
* approving and writing (ensure archive on rewrite)
* browsing archive viewer to confirm old version exists
* checking run log contains executed actions

---

## Next Step (legal per state machine)

Move to **`S3 — Propose Patch (Phase 02)`** with a patch that includes only:

* UI scaffolding for documents panels (conceptual in spec; later code)
* DocOps validator + writer tooling (conceptual in spec; later code)
* state update hooks and run logs behavior
* nothing else

But since you said **no code ever**, the “Patch Proposal” in our spec process becomes a **“Build Packet”**: a precise checklist of components to implement, with file boundaries and responsibilities, without actual code.

### Probing question (design-critical)

Do you want DocOps proposals to be **single-document only** (one Create/Rewrite per proposal), or allow **multi-action bundles** (outline + new phase doc + run log together)?

* Single-document: simpler approvals, less risk, slower workflow
* Bundles: faster, but more risk and more complex review

If you don’t answer, I’ll default to **bundles up to 3 actions** because your workflow explicitly wants “package these items into agent actions” and you’ll want outline+phase to travel together sometimes.
