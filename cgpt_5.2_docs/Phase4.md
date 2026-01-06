Good. **PatchOps = file-level only** is consistent with Option A and with everything you’ve locked so far. It keeps diffs reviewable, validation simpler, and approval meaningful. Operation-level edits can come later *if and only if* you hit a real limitation.

We now do the **only legal next move**.

---

# Phase 04 — PatchOps Protocol + Diff Viewer

**Location:**
`/documents/PHASES/phase_04_patchops_protocol_and_diff_viewer.md`

---

## 1. Objective

Define a **file-level PatchOps protocol** and a **read-only diff review UI** that allows the agent to propose code changes as explicit, auditable artifacts **without executing them**.

This phase makes code changes **reviewable objects** governed by the unified approval state machine defined in Phase 03.

---

## 2. Scope

This phase is limited to:

* Defining **PatchOps v1** (file-level only)
* Defining patch proposal structure and validation rules
* Defining diff artifact format and storage
* Defining the Diff Viewer UI (read-only)
* Integrating PatchOps proposals into the **unified approval state machine**
* Recording PatchOps proposals and approvals in project state and run logs

**No patch application occurs in this phase.**

---

## 3. Non-Goals

This phase explicitly does **not**:

* Apply patches to the filesystem
* Execute tests or commands
* Introduce repair loops
* Add new approval gates
* Modify DocOps
* Modify source files

If a file changes on disk as a result of Phase 04, that is a spec violation.

---

## 4. PatchOps Philosophy (File-Level, v1)

PatchOps v1 treats **each file as the atomic unit of change**.

* No partial writes
* No in-place text operations
* No “surgical” edits
* Every change is represented as:

  > *old file → new file*

This ensures:

* deterministic validation
* simple hashing
* clean diffs
* understandable approvals

---

## 5. PatchOps v1 Protocol (Abstract Schema)

### 5.1 Envelope

Agent must emit exactly one PatchOps block per proposal:

```text
<PATCHOPS>
{
  "version": 1,
  "proposal_id": "<uuid-or-timestamp>",
  "phase_id": "NN",
  "summary": "<short description>",
  "files": [ ... ]
}
</PATCHOPS>
```

---

### 5.2 File Entry (File-Level Only)

Each entry in `files[]` represents one file change.

```text
{
  "path": "<relative_path>",
  "operation": "create | update | delete",
  "pre_hash": "<hash or null>",
  "post_hash": "<hash or null>",
  "content": "<full file content if create/update>"
}
```

#### Rules

* `path` must be relative to workspace root
* No absolute paths
* No `..`
* `create`

  * `pre_hash` must be `null`
  * `post_hash` required
  * `content` required
* `update`

  * `pre_hash` required
  * `post_hash` required
  * `content` required
* `delete`

  * `pre_hash` required
  * `post_hash` must be `null`
  * `content` must be omitted

---

## 6. Validation Rules (Fail Closed)

PatchOps proposal is rejected if:

* Version != 1
* More than **3 non-test files** are included
* Any path escapes workspace root
* Any path targets:

  * `/documents/**`
  * `/.agent_ide/**`
  * `.env`
* Any `update` pre_hash does not match current file hash
* Total content size exceeds configured limit
* Required fields are missing

---

## 7. Diff Artifact Generation

### 7.1 Diff Format

For every PatchOps proposal, the system generates:

* A **unified diff** per file (old vs new)
* A summary:

  * files changed
  * LOC added/removed
  * risk flags

### 7.2 Storage

Diff artifacts are written to:

```
/documents/RUN_LOGS/patch_<timestamp>_phaseNN.diff
```

Diff files are:

* immutable
* append-only artifacts
* never rewritten

---

## 8. Diff Viewer UI (Read-Only)

### UI Elements

* File list (changed files)
* Per-file unified diff
* Metadata panel:

  * proposal_id
  * phase_id
  * risk flags
  * validation status

### Enforcement

* No editing
* No apply button in this phase
* Approval controls are visible but **execution is disabled**

---

## 9. Approval Integration (Unified State Machine)

PatchOps proposals use the same approval lifecycle:

* `Proposal_Created`
* `Proposal_Validated`
* `Awaiting_Approval`
* `Approved`
* `Rejected`

### Gate Usage

* **Gate B** applies to PatchOps proposals
* Approval requires explicit user action
* Rejection requires a reason

No automatic transition to execution.

---

## 10. Persistence Rules

### Project State

On PatchOps proposal creation:

* record:

  * proposal_id
  * phase_id
  * target files
  * validation result
  * current status

On approval/rejection:

* append approval record
* update proposal status

### Run Logs

Every PatchOps proposal creates a run log entry including:

* proposal summary
* validation outcome
* approval decision

---

## 11. Risks and Mitigations

### Risks

* Large file rewrites cause noisy diffs
* Agent proposes too-broad changes
* Hash mismatches due to stale reads

### Mitigations

* Small phase limits enforced
* Hash validation blocks stale updates
* User review via diff viewer before approval

---

## 12. Acceptance Criteria

Phase 04 is complete when:

* PatchOps proposals are emitted as structured objects
* Proposals are validated and rejected on error
* Diff artifacts are generated and stored
* Diff viewer displays proposals correctly
* Unified approval flow governs PatchOps
* No filesystem code changes occur

---

## 13. Changelog

* **2026-01-06** — Initial draft created by Agent

---

## 14. Verification Results

*(Empty until implemented and user verification.)*

---

### Gate A Status

⛔ **Not Approved**

---

## Why this phase matters (no fluff)

This is the point where:

* “AI edits code” stops being scary
* approvals become informed decisions
* Option A actually exists in reality

Everything after this (Phase 05: Apply Patch + Tests) is *procedural*, not conceptual.

---

### Next legal action

If this matches your intent:

👉 **Say:** *“Approve Phase 04 Docs”*

After that, Phase 05 will finally **close the loop**:

* apply PatchOps
* run user-driven tests
* repair failures using the same machinery

At that point, the system is end-to-end complete.
