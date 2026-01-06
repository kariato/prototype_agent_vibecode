## Critique (keep the discipline)

“Next” could mean 05, 06, or both. But your dependency chain says 05 (PatchOps+Diff) must exist before 06 (Atomic FS). So I’m giving you **Task Packet 05** now. It creates PatchOps proposals, validates them, and generates diffs—**no apply** yet.

---

# Anti Gravity Task Packet 05 — PatchOps Spec + Diff Generation (No Apply)

## Goal

Implement **PatchOps** as a proposal type that represents file-level code changes as inspectable diffs. This step must:

* validate PatchOps payloads (fail closed)
* generate unified diffs for UI review
* store diff artifacts in `documents/RUN_LOGS/`
* store proposal payloads in `.agent_ide/artifacts/` (Option B)

**Important:** No file writes to code yet. Execution (apply) comes in Step 07 and depends on Atomic FS (Step 06).

---

## Depends On

* Task 00 (dotenv/settings)
* Task 01 (workspace + state)
* Task 02 (artifacts + run logs + safe paths)
* Task 03 (proposal + approval FSM + registry)
* Task 04 is not required, but compatible

---

## Files to Create / Modify

Create:

```
app/runtime/patchops_schema.py
app/runtime/patchops.py
app/tools/diffgen.py
app/state/diff_artifacts.py
```

Modify (only if needed):

```
app/runtime/validation.py
app/state/paths.py
```

---

## PatchOps Proposal Format (Contract)

A PatchOps proposal must have:

* `proposal_type = "patchops"`
* `gate = "B"`
* `payload = { "operations": [ ... ], "summary": "...", "constraints": {...} }`

### Operation object (file-level only)

Each `operation` includes:

Required:

* `op`: `"create" | "update" | "delete"`
* `path`: workspace-relative path (MUST NOT be under `documents/` or `.agent_ide/`)
* `content`: string (required for create/update; forbidden for delete)
* `pre_hash`: string | null

  * required for update/delete
  * null for create
* `post_hash`: string | null

  * required for create/update
  * null for delete

Optional:

* `is_test_file`: bool (computed or supplied)

  * used to apply “max non-test files” constraint

### Constraints (must enforce)

* Max actions per bundle applies at agent-level, but PatchOps has its own:
* **Max 3 non-test files per proposal**

  * Tests excluded (anything under `tests/` OR filename matches `test_*.py` OR `*_test.py`)
* No binary files (reject if content looks binary or path suggests it, configurable)
* No symlink targets (reject when applying later; for now, validate path only)

---

## Validation Rules (Fail Closed)

### Path safety

For every operation:

* path is relative
* normalized, no `..`
* must be inside workspace root
* must NOT be under:

  * `documents/`
  * `.agent_ide/`
* must NOT match denylist prefixes from settings

### Operation integrity

* `create`:

  * requires `content`
  * `pre_hash` must be null
  * `post_hash` must be present (hash of content)
* `update`:

  * requires `content`
  * `pre_hash` must be present (computed from current file at validation time)
  * `post_hash` must be present (hash of content)
  * file must exist at validation time
* `delete`:

  * `content` must be absent
  * `pre_hash` must be present (computed from current file at validation time)
  * `post_hash` must be null
  * file must exist at validation time

### Proposal integrity

* Must be stored as proposal artifact via registry (Task 03)
* Must be in `awaiting_approval` state for UI review after validation

### Non-test file cap

* Count operations where `is_test_file == False`
* Must be ≤ 3 or validation fails

---

## Diff Generation (Unified)

Diffs must be generated for UI review:

* For create: diff from empty file → new content
* For update: diff from current content → new content
* For delete: diff from current content → empty (or deletion marker)

### Diff format

* Unified diff (`---`, `+++`, `@@`) per file
* Deterministic ordering by path

---

## Diff Artifact Storage

Diff must be written to:

* `documents/RUN_LOGS/patch_<ts>_<proposal_id>.diff`

Also record a run log entry:

* `documents/RUN_LOGS/run_<ts>_patchops_<proposal_id>.md`
  with:
* proposal summary
* list of paths
* “non-test file count”
* pointer to proposal artifact + diff artifact

---

## Code Modules — Responsibilities

### `app/runtime/patchops_schema.py`

* Pydantic models for PatchOps payload + operations
* Helper `is_test_file(path) -> bool`

### `app/runtime/patchops.py`

Responsibilities:

* Validate PatchOps payload against workspace filesystem
* Compute `pre_hash` for update/delete from current file contents
* Compute/verify `post_hash` matches provided content (or compute if you choose that contract—pick one and freeze; recommended: compute internally and treat provided hash as optional)
* Generate diffs via `diffgen`
* Write diff artifacts + run logs
* Return validation messages for UI

Public functions:

```python
def validate_patchops_payload(workspace_root: str, payload: dict) -> tuple[bool, list[str], dict]: ...
def generate_patchops_diff(workspace_root: str, proposal_id: str) -> str: ...
```

### `app/tools/diffgen.py`

* Pure function utilities for unified diff generation

Public function:

```python
def unified_diff(old_text: str, new_text: str, from_path: str, to_path: str) -> str: ...
```

### `app/state/diff_artifacts.py`

* Write diff file under `documents/RUN_LOGS/`
* Return relative path

Public function:

```python
def write_diff(workspace_root: str, proposal_id: str, diff_text: str) -> str: ...
```

---

## Required Public Interfaces (Must Exist)

```python
# app/runtime/patchops.py
def validate_patchops_payload(workspace_root: str, payload: dict) -> tuple[bool, list[str], dict]: ...
def generate_patchops_diff(workspace_root: str, proposal_id: str) -> str: ...

# app/tools/diffgen.py
def unified_diff(old_text: str, new_text: str, from_path: str, to_path: str) -> str: ...

# app/state/diff_artifacts.py
def write_diff(workspace_root: str, proposal_id: str, diff_text: str) -> str: ...
```

Notes:

* `validate_patchops_payload` returns:

  * `ok`
  * `messages`
  * `normalized_payload` (with computed hashes and is_test flags)

---

## Invariants (Non-Negotiable)

* No file writes to code/tests yet
* Validation fails closed on any ambiguity
* Diffs are deterministic and stored in RUN_LOGS
* Proposal payload stays in `.agent_ide/artifacts/` (Option B)
* PatchOps cannot touch `documents/` or `.agent_ide/`

---

## Validation / Done Criteria

Anti Gravity must demonstrate:

1. PatchOps `create` proposal generates a diff and logs it
2. PatchOps `update` proposal computes pre_hash and diff matches expected
3. PatchOps `delete` proposal generates deletion diff
4. Non-test cap enforced (reject 4 non-test files)
5. Attempts to patch `documents/*` rejected
6. Diff artifacts written under `documents/RUN_LOGS/`
7. Proposal payload stored as artifact via registry

---

## Forbidden Actions

* Do NOT implement apply/execute of PatchOps yet
* Do NOT add LangGraph
* Do NOT add UI
* Do NOT allow PatchOps to modify workspace files in this step

---

## Minimal Manual Test Script

1. Init workspace
2. Create a dummy file `adder.py` manually (outside system is okay for now)
3. Submit PatchOps update to change it
4. Validate -> diff generated -> stored
5. Submit PatchOps touching `documents/PROJECT_OUTLINE.md` -> validation must fail
6. Submit PatchOps with 4 non-test paths -> validation must fail

---

If you want the real “next” after this, it is **Task Packet 06 — Atomic FS Core** (the hard part).
