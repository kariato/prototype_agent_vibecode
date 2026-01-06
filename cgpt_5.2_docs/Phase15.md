## Critique (because this is where projects die)

If Atomic FS is even slightly hand-wavy, you will eventually corrupt a workspace and lose trust in the whole system. Also: your “proposal-level all-or-nothing” guarantee **forces** backup+rollback. So this packet is explicit about staging, commit, rollback, recovery, and Windows locks.

---

# Anti Gravity Task Packet 06 — Atomic FS Core (Proposal-Level All-or-Nothing)

## Goal

Implement the **Atomic Filesystem Transaction Engine** used by PatchOps apply to guarantee:

* **Per-file atomic writes** using temp + rename
* **Proposal-level all-or-nothing** via backup + rollback
* **Crash recovery** via on-start scan and incomplete transaction detection
* **Cross-platform behavior**, including Windows file lock handling

This step produces tooling only. It does **not** wire into LangGraph or UI yet.

---

## Depends On

* Task 00 (dotenv/settings)
* Task 01 (workspace + project_state; atomic JSON saves already)
* Task 02 (artifact store + run logs + safe paths)
* Task 05 (PatchOps schema/validation exists; no apply yet)

---

## Files to Create / Modify

Create:

```
app/tools/atomic_fs.py
app/tools/fsync_util.py
app/tools/recovery_scan.py
app/runtime/execution_reports.py
```

Modify (only if needed):

```
app/state/paths.py
app/state/artifacts.py
```

---

## Terminology (Frozen)

* **Temp file:** `.<name>.tmp.<proposal_id>.<nonce>` in same dir as target
* **Backup file:** `.<name>.bak.<proposal_id>` in same dir as target
* **Delete-staging file:** `.<name>.del.<proposal_id>` in same dir as target
* **Transaction artifact:** `.agent_ide/artifacts/execution_<ts>_<proposal_id>.json`

---

## Inputs / Outputs (Interfaces)

Atomic FS applies a **validated PatchOps payload**.

### Input: PatchOps payload (normalized)

* operations list with:

  * `op`, `path`, `content` (if create/update)
  * `pre_hash`, `post_hash`
  * `is_test_file`

### Output: ExecutionReport (dict)

Must include:

* `proposal_id`
* `transaction_id`
* `stage` final: `committed | rolled_back | failed_rollback | failed_preflight`
* `success: bool` (true only if committed)
* `files[]`: per-file details (see below)
* `pending_cleanup[]`
* `recovery_required: bool`
* `errors[]`

---

## Transaction Model (Must Implement)

### Stages (recorded in execution artifact)

* `staging`
* `committing`
* `rolling_back`
* `committed`
* `rolled_back`
* `failed_rollback`
* `failed_preflight`

### Commit definition

Transaction is **committed** only when:

* all operations applied
* all post-hash checks match expected
* stage updated to `committed`

Cleanup is separate.

---

## Required Preflight (Fail Closed, No Changes)

Before any mutation:

1. Validate all paths:

   * relative, normalized, no `..`
   * inside workspace root
   * not under `documents/` or `.agent_ide/`
   * not denylisted
2. For `update` and `delete`:

   * file exists
   * compute current hash == `pre_hash`
3. For `create`:

   * target does not exist (unless you explicitly allow “create-overwrite”; default NO)
4. Confirm parent directories exist (create parents allowed here; safe)
5. Create execution artifact in stage `staging`

If any preflight fails:

* write execution artifact with `failed_preflight`
* return without touching targets

---

## Core Algorithm (Authoritative)

### Phase A — STAGING (no target mutations)

For each op in sorted order by `path`:

* create/update:

  1. create temp path in same dir
  2. write full content
  3. flush + fsync temp file
  4. record temp path in report

* delete:

  * no temp creation

**No renames of existing targets occur in staging.**

Update execution artifact stage remains `staging`, but per-file records can be updated.

---

### Phase B — COMMITTING (mutations begin)

Set stage to `committing` in execution artifact.

#### Order rules (frozen)

1. Apply all `create` and `update` (sorted by path)
2. Stage all `delete` (sorted by path)
3. Only after full success: perform cleanup deletions

#### Commit for UPDATE (backup mandatory)

For each update:

1. rename target -> backup (`.<name>.bak.<proposal_id>`)
2. fsync directory (POSIX)
3. rename temp -> target (atomic)
4. fsync directory (POSIX)
5. compute hash(target) == `post_hash`
6. record: backup path, post_hash_observed, status=committed_for_file

On any failure: jump to rollback immediately.

#### Commit for CREATE

For each create:

1. rename temp -> target
2. fsync directory (POSIX)
3. compute hash(target) == `post_hash`
4. record status

On failure: rollback.

#### Commit for DELETE (stage first)

For each delete:

1. rename target -> delete-staging (`.<name>.del.<proposal_id>`)
2. fsync directory (POSIX)
3. record status=delete_staged

On failure: rollback.

---

### Phase C — CLEANUP (after commit success only)

After all create/update/delete-staging succeed and post-hashes verified:

1. Permanently delete all `.<name>.del.<proposal_id>`
2. Delete all backups `.<name>.bak.<proposal_id>`
3. Delete any remaining temps

If cleanup fails:

* transaction remains `committed`
* `recovery_required=true`
* `pending_cleanup[]` populated

Update stage to `committed` regardless of cleanup completeness.

---

## Rollback (Mandatory for All-or-Nothing)

### Trigger

Any failure during committing triggers rollback.

### Phase D — ROLLING BACK

Set stage to `rolling_back`.

Rollback actions must restore pre-transaction state:

For each op already mutated (track mutated list):

* update:

  * if target exists, rename to `.<name>.failednew.<proposal_id>` (optional)
  * restore backup -> target
  * fsync dir
* create:

  * remove created target (or rename to `.<name>.created.<proposal_id>` for forensics)
* delete (staged):

  * restore delete-staging -> original target

After rollback, verify for updates/deletes:

* current hash(target) == `pre_hash`

If all restored:

* stage = `rolled_back`, success=false

If any restore fails or hash mismatch:

* stage = `failed_rollback`
* recovery_required=true

Rollback must preserve temps/backups if recovery required.

---

## Recovery Scan (Startup / Pre-Apply)

Implement a scan utility that finds leftovers:

* `*.tmp.<proposal_id>*`
* `*.bak.<proposal_id>`
* `*.del.<proposal_id>`
* execution artifacts with stage in:

  * `committing`, `rolling_back`, `failed_rollback`

### Output: RecoveryReport

* list of proposal_ids with issues
* per proposal_id:

  * detected temp/backup/del files
  * execution artifact reference (if present)
  * recommended action: `rollback | cleanup | inspect`

**Hard rule:** never silently delete leftovers.

---

## Windows Requirements (Explicit)

Windows may fail rename/replace due to locks.

Minimum required behavior:

* detect lock errors and classify as `IO_ERROR_LOCKED`
* stop committing immediately
* rollback any prior changes
* mark `recovery_required=true` if rollback incomplete
* never continue to next file after lock failure

Also ensure:

* safe filename generation for temp/backup/del (avoid reserved names)
* path normalization respects Windows separators

---

## Logging / Artifacts Requirements

Every apply transaction must write:

* execution artifact: `.agent_ide/artifacts/execution_<ts>_<proposal_id>.json`

Per-file record fields in execution artifact:

* `path`
* `op`
* `temp_path` (if any)
* `backup_path` (if any)
* `del_path` (if any)
* `pre_hash_expected`, `pre_hash_observed`
* `post_hash_expected`, `post_hash_observed`
* `status`: `staged | committed | delete_staged | rolled_back | failed`
* `error` (if any)

Also append a run log entry:

* `documents/RUN_LOGS/run_<ts>_atomic_apply_<proposal_id>.md`
  with:
* final stage
* success/failure summary
* pointers to execution artifact

---

## Public Interfaces (Must Exist)

```python
# app/tools/atomic_fs.py
def apply_patchops_transaction(
    workspace_root: str,
    proposal_id: str,
    patchops_payload: dict,
    *,
    session_id: str
) -> dict: ...

# app/tools/recovery_scan.py
def scan_recovery(workspace_root: str) -> dict: ...
```

Optional but recommended:

```python
# app/tools/atomic_fs.py
def rollback_transaction(workspace_root: str, proposal_id: str) -> dict: ...
def cleanup_transaction(workspace_root: str, proposal_id: str) -> dict: ...
```

---

## Invariants (Non-Negotiable)

* temps/backups in same dir as target
* no partial writes (temp + rename)
* proposal-level atomicity (backup + rollback)
* fail closed on preflight mismatch (STALE_STATE)
* no silent cleanup of forensic artifacts
* deterministic ordering

---

## Validation / Done Criteria (must demonstrate)

Anti Gravity must demonstrate with small sample files:

1. **Happy path**

* update+create+delete committed, no backups left

2. **Kill simulation (manual)**

* stop after backups created, confirm recovery scan detects backups

3. **Hash mismatch**

* modify a target file between validate and apply → preflight fails, no changes

4. **Rollback**

* induce failure mid-commit (e.g., permission error on second file) → first file restored, no partial state

5. **Cleanup pending**

* simulate inability to delete backup → stage committed but recovery_required true

---

## Forbidden Actions

* Do NOT wire this into LangGraph yet
* Do NOT build UI yet
* Do NOT “simplify” by skipping backups
* Do NOT store execution artifacts under `documents/`
* Do NOT allow patching `documents/` or `.agent_ide/`

---

## Minimal Manual Test Script (Anti Gravity)

1. Create workspace, create files:

   * `adder.py`, `tests/test_adder.py`
2. Build a patchops_payload (normalized) updating `adder.py`
3. Call `apply_patchops_transaction()`
4. Confirm execution artifact exists and file updated
5. Induce stale state: edit `adder.py`, re-run transaction with old pre_hash → must fail_preflight
6. Induce rollback: make a second op target read-only to force failure → ensure rollback restores first file
7. Run `scan_recovery()` and confirm no leftovers in happy path; leftovers detected after simulated failures

---
