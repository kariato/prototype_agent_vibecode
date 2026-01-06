Locked: **DocOps bundles are allowed, max 3 actions per proposal** (Phase 02 constraint). Good trade: fast enough without turning review into a nightmare.

We now produce the **Phase 02 Build Packet** (your “Patch Proposal” equivalent, since we’re never writing code here). This is the implementation checklist that Antigravity (or you) can follow, and it’s also what the agent must treat as the contract for later phases.

---

# Phase 02 — Build Packet (No Code)

**Phase:** 02 — Documents UI + DocOps
**Bundle limit:** max 3 actions per DocOps proposal
**Scope guard:** only `/documents/**` doc operations + doc-only UI + doc-related state fields

## 1) Component boundaries (files/modules conceptually)

Even without code, we define *where responsibilities live* to prevent “God file” creep.

### A) UI Layer: Documents Workspace

**Responsibility:** render documents, accept commands, show proposals, enforce approvals, trigger writes.

**Sub-components**

1. **Workspace Header**

   * shows absolute `workspace_root`
   * shows “initialized / partial / new”
2. **Documents Navigator**

   * filter dropdown (Outline/Phases/ADRs/Run Logs/Archive/All)
   * filename search
   * selectable list of docs (relative path)
3. **Chat + Command Helpers**

   * chat transcript
   * command helper buttons that insert canonical commands
4. **Right-side Tabs**

   * Doc Preview (rendered + raw toggle)
   * Proposed DocOps (pretty JSON + validation)
   * Archive Viewer (versions + preview)
   * Run Logs viewer

**UI state machine**

* `Idle`
* `DocOps_Proposed`
* `DocOps_Approved`
* `DocOps_Writing`
* `DocOps_Written`
* `DocOps_Error`

**UI enforcement**

* “Write Docs” disabled unless `DocOps_Approved`
* Reject requires reason (stored to run log)
* Approval and write events create run log entries

---

### B) DocOps Protocol + Validator

**Responsibility:** parse `<DOCOPS>...</DOCOPS>`, validate schema, expand templates, reject unsafe operations.

**DocOps v1 required fields**

* `version: 1`
* `proposal_id`
* `summary`
* `actions[]` (1–3 entries only in Phase 02)

**Allowed actions (Phase 02)**

* `CreateDoc(path, content)`
* `RewriteDoc(path, content, archive=true)`
* `AppendLog(path, content)`
* `CreatePhaseDoc(phase_id, slug, content)` (expands to CreateDoc)
* `CreateADR(adr_id, slug, content)` (expands to CreateDoc)

**Validation rules (fail closed)**

* Exactly one DOCOPS block per proposal
* JSON must parse; no trailing junk
* Actions count: 1–3
* All action paths must start `documents/`
* No absolute paths, no `..`, no control chars
* Extensions: `.md` only
* `RewriteDoc.archive` must be `true`
* Scope: reject targets outside `documents/**`

**Expansion rules**

* `CreatePhaseDoc` → `documents/PHASES/phase_<phase_id>_<slug>.md`
* `CreateADR` → `documents/DECISIONS/ADR_<adr_id>_<slug>.md`

**Important security rule**

* The agent never supplies archive destination paths.
* The writer computes archive path: `documents/_archive/<timestamp>/<relative_doc_path>`

---

### C) Document Writer (DocOps executor with archival)

**Responsibility:** apply validated DocOps actions to the filesystem under `workspace_root`.

**Write algorithm (conceptual)**

1. Re-validate DocOps (defense in depth)
2. Expand template actions to concrete CreateDoc actions
3. For each action:

   * `CreateDoc`: fail if file exists? (decision below)
   * `RewriteDoc`: if file exists, archive old to timestamped folder, then overwrite
   * `AppendLog`: create file if missing, append content
4. Return a write report:

   * actions executed
   * archive files created
   * any errors

**Decision (must be explicit)**

* `CreateDoc` on existing file:

  * Option A: fail
  * Option B: treat as RewriteDoc with archive
    I recommend **Option A (fail)** to keep semantics explicit and prevent accidental overwrites.

If you disagree, say so; otherwise the spec locks Option A.

---

### D) Project State Updates (doc-related only)

**Responsibility:** record pending proposal, approvals, and last write.

**Fields updated**

* `documents.pending_proposal_id`
* `documents.pending_created_at`
* `documents.pending_targets[]`
* `documents.pending_actions_count`
* `documents.pending_status`: `"proposed" | "approved" | "rejected" | "written" | "error"`
* `documents.last_write_at`
* `documents.last_write_proposal_id`

**Approval records**

* append to `approvals[]`:

  * `phase_id: "02"`
  * `gate: "A"`
  * `timestamp`
  * `note: <reason>`

**Rule**

* State updates must be echoed in run logs.

---

### E) Run Logging (Phase 02)

**Responsibility:** append auditable trail for doc proposals, approvals, writes.

Create run logs as new files (not rewrites):

* `documents/RUN_LOGS/run_<timestamp>_phase02_docs.md`

Log entries must include:

* Proposal ID
* Action summary
* Validation pass/fail + messages
* Approval decision + reason if rejected
* Write report + list of archives created

---

## 2) Agent prompt command protocol (user → agent intent)

These are UI-level convenience commands (not “magic strings” the agent invents).

### Canonical user commands

* `@docs:outline create`
* `@docs:outline rewrite`
* `@docs:phase create <NN> <slug>`
* `@docs:adr create <NNNN> <slug>`
* `@docs:show <documents/relative_path>`

### Interpretation rules

* Commands are parsed by the app first and translated into a structured intent payload for the agent (so the model doesn’t have to parse strings reliably).
* If a command is malformed, the UI rejects it before the agent runs.

---

## 3) LangGraph doc-lane action mapping (tight contract)

### Node contracts (inputs/outputs)

* `DocIntake`

  * input: structured intent + current doc index (paths + hashes)
  * output: `{ target_docs[], operation_type, constraints }`

* `DocDraft`

  * input: intake + existing doc contents (if any)
  * output: `{ draft_markdown_by_target, summary }`

* `DocOpsEmit`

  * input: drafts
  * output: `<DOCOPS>...</DOCOPS>`

* `AwaitDocApproval`

  * input: proposal
  * output: approved/rejected + note

* `DocWriteTool`

  * input: validated docops JSON
  * output: write report (archives, files written)

* `DocWriteReport`

  * input: write report
  * output: human summary + next suggested command

**Hard rule:** The only filesystem writes in Phase 02 happen inside `DocWriteTool`.

---

## 4) UI acceptance tests (manual verification steps)

This is what you (user) will do to verify Phase 02 is correct.

1. Select workspace with existing `documents/PROJECT_OUTLINE.md`
2. Run `@docs:outline rewrite`
3. Confirm UI enters `DocOps_Proposed`
4. Reject once; verify no write occurred, state shows rejected, run log exists
5. Run again; approve; click Write Docs
6. Verify:

   * old outline moved into `_archive/<timestamp>/documents/PROJECT_OUTLINE.md`
   * new outline exists in place
   * run log lists both
7. Create a phase doc:

   * `@docs:phase create 03 approval-state-machine`
   * ensure max actions ≤3 (outline rewrite + phase create + log is okay)
8. Confirm DocOps viewer shows exactly one block and ≤3 actions.

---

## 5) Two spec decisions to lock now (or they’ll bite you)

### Decision 1: `CreateDoc` on existing file

I recommend: **FAIL** (force agent to use RewriteDoc explicitly).

### Decision 2: Bundle composition

When multiple actions exist in a bundle, recommended order:

1. RewriteDoc (archives old first)
2. CreateDoc (new)
3. AppendLog (record)

This makes failures easier to reason about.

---

## Gate B equivalent (since we’re not applying code patches)

If you accept this Build Packet as the “Phase 02 patch,” the next step is:

* **Phase 03 doc** (Approval State Machine UI + transitions), because Phase 02 has defined the doc approval gate mechanics and tool boundaries.

### Design-critical confirmation

Do you accept **Decision 1**: `CreateDoc` fails if the target already exists (instead of silently archiving and overwriting)?

If you don’t respond, I will lock it as **FAIL** because explicitness is the entire point of Option A.

Short answer: **yes, a little — but in a *controlled*, recoverable way**. Longer answer: we’re *supposed* to be this deep **once**, and then never again.

Let me checkpoint this cleanly and critically, without backpedaling.

---

## 🔎 Checkpoint Assessment — Are We in the Weeds?

### What’s actually happening

You’re not lost in implementation weeds. You’re doing **systems hardening**. There’s a difference.

You’ve been nailing down:

* invariants
* state transitions
* failure modes
* safety contracts between UI ⇄ agent ⇄ filesystem

That’s the part everyone skips—and then regrets.

### Where the risk *does* appear

You’re at risk of:

* **over-freezing** Phase 02 (Docs) before Phase 03 (Approvals / PatchOps) gets air
* conflating *mechanism correctness* with *product momentum*

The danger is not “too much detail.”
The danger is **continuing to add new constraints without promoting them up a layer**.

---

## 🧠 Reality Check: What You’ve Already Locked (This Is Good)

Let’s inventory what is *already settled* so we don’t keep re-litigating it.

### Hard constraints (locked)

* Document-first, no exceptions
* Option A strict patching
* Small phases
* Absolute workspace path
* `.env` for runtime config
* per-project state file
* archive-on-rewrite
* DocOps protocol
* Bundles ≤ 3 actions
* CreateDoc fails if exists
* UI gates writes

This is **enough to build the product**. Anything more here *is* diminishing returns.

---

## 🧭 Where You’re Right to Pause

Phase 02 has reached the point of **spec sufficiency**.

Continuing to refine it now would likely:

* create speculative complexity
* steal oxygen from PatchOps + Approval state (Phase 03)
* delay end-to-end flow validation

Your instinct to checkpoint is correct.

---

## 📌 The Correct Mental Model Going Forward

Think in **layers**, not phases:

### Layer 1 — Safety & Control (DONE)

* Docs before code
* Approvals
* Patch isolation
* Archival
* Audit trail

✅ This layer is now solid.

### Layer 2 — Flow Completion (NEXT)

* Can a user go:

  * outline → phase doc → patch → approve → apply → test → repair?
* This is **Phase 03 + Phase 04**, not more Phase 02.

### Layer 3 — Ergonomics (LATER)

* Fewer clicks
* Smarter defaults
* Batch operations
* Visual polish

You are at the boundary between Layer 1 and Layer 2.

---

## 🛑 What We Should *Not* Do Next

* Add more DocOps variants
* Add more UI toggles
* Add more config flags
* Spec archive edge cases

All of that can wait until there’s a full loop.

---

## ✅ What the Checkpoint Means Practically

We **freeze Phase 02** as:

* “Docs UI + DocOps protocol are sufficiently specified.”

No more changes unless:

* Phase 03 *forces* a revision (that’s valid)
* or an invariant is violated (unlikely now)

---

## 🔜 What the Next Move Should Be (and why)

The **next phase must be Phase 03**:

> **Approval State Machine + PatchOps Gate UI**

Why?

* That’s where:

  * your discipline either pays off or collapses
  * the system proves it’s not just a document generator
* It’s also where LangGraph orchestration becomes meaningful.

If Phase 03 works cleanly, everything else is just plumbing.

---

## Before proceeding, one grounding question (not process, not meta)

Do you want Phase 03 to:

1. **Generalize approval gates** (Docs + PatchOps use same mechanism), or
2. **Introduce PatchOps as a parallel lane** with its own approval semantics?

Option 1 keeps the system elegant.
Option 2 gives flexibility but increases mental overhead.

My recommendation is **Option 1** unless you’re anticipating radically different approval behaviors later.

Your answer determines whether Phase 03 is clean or gnarly.
