# Anti Gravity Task Packet 04 — DocOps Writer + Archive Rules

## Goal

Implement **DocOps** as the only permitted mechanism to create/modify files under the workspace `documents/` directory. DocOps must flow through the existing **proposal + approval FSM** (Gate A). Rewrites must archive old versions into `documents/_archive/`.

This step creates the first real “side effect tool,” but it must remain strictly contained.

---

## Depends On

* Task 00 (dotenv/settings)
* Task 01 (workspace + project_state)
* Task 02 (artifact store + run logs)
* Task 03 (proposal model + approval FSM + registry)

---

## Directory Layout (workspace)

Must already exist from bootstrap (Task 01):

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

---

## Files to Create / Modify (repo code)

Create:

```
app/tools/doc_writer.py
app/runtime/docops.py
app/runtime/docops_schema.py
```

Modify (only if needed):

```
app/runtime/validation.py
```

---

## DocOps Proposal Format (Contract)

DocOps proposals must have:

* `proposal_type = "docops"`
* `gate = "A"`
* `payload = { "actions": [ ... ] }`
* `actions.length <= Settings.MAX_ACTIONS_PER_BUNDLE` (default 3)

### Action types (must implement)

Each action is an object with:

* `action_type` (one of the below)
* `path` (workspace-relative path under `documents/`)
* `content` (string; required for create/rewrite/append)
* `mode` (optional; e.g., `"overwrite"` for create conflicts—default fail closed)

#### 1) `CreateDoc`

* Creates a new document at `documents/...`
* Must fail if file exists (unless explicitly allowed in `mode` and documented)

#### 2) `RewriteDoc`

* Replaces an existing doc
* Must move old file into `documents/_archive/` first
* Archive naming (contract):

  * `_archive/<original_relpath_with_slashes_replaced>__<ts>.md`
  * Example: `documents/PHASES/phase_06_langgraph_runtime_spec.md`
    becomes `_archive/documents__PHASES__phase_06_langgraph_runtime_spec.md__20260106T140501.md`

#### 3) `AppendDoc`

* Appends content to an existing doc
* Must fail if doc doesn’t exist (fail closed)

#### 4) `CreatePhaseDoc`

* Convenience action to create:

  * `documents/PHASES/phase_<NN>_<slug>.md`
* Still a create; must fail if already exists unless `mode` explicitly allows overwrite (default no)

---

## Validation Rules (Fail Closed)

DocOps validation must check:

### Path Safety

* All action paths must be:

  * relative
  * normalized
  * under `documents/` only
  * not contain `..`
  * not target `.agent_ide/` or repo root

### Bundle Size

* `len(actions) <= MAX_ACTIONS_PER_BUNDLE`

### Action Integrity

* `CreateDoc` requires `content`
* `RewriteDoc` requires `content` AND target must exist
* `AppendDoc` requires `content` AND target must exist
* `CreatePhaseDoc` requires `phase_number` and `slug` OR a prebuilt `path`

  * (Pick one format and lock it; recommended: prebuilt `path` to keep schema simpler.)

### Proposal Integrity

* Proposal must be in `approved` state before execution
* Execution must refuse anything not `approved`

---

## Tooling Behavior (Doc Writer)

Doc writer must:

* Write only inside workspace root
* Use atomic write for doc modifications:

  * write temp next to target
  * rename into place
* On rewrite:

  1. archive existing file
  2. write replacement
  3. log both operations

Doc writer must return an **ExecutionReport** dict:

* `proposal_id`
* `success: bool`
* `files_written: [rel_paths]`
* `files_archived: [archive_rel_paths]`
* `errors: [ {code, message, path} ]`

---

## Artifacts & Logs (mandatory)

### Proposal artifact

Already handled by Task 03; DocOps execution must reference it.

### Execution artifact

On every DocOps execute, write:

* `.agent_ide/artifacts/execution_<ts>_<proposal_id>.json`

### Run log entry

Append a human log to:

* `documents/RUN_LOGS/run_<ts>_docops_<proposal_id>.md`
  Include:
* summary
* list of doc paths affected
* archive path(s)
* pointer(s) to proposal artifact + execution artifact

---

## Code Modules — Responsibilities

### `app/runtime/docops_schema.py`

* Defines the DocOps action schema (Pydantic recommended)
* Provides parsing/validation helpers

### `app/runtime/docops.py`

* Assembles DocOps proposals (optional helper)
* Validates DocOps proposals using schema + rules
* Executes DocOps by calling `app/tools/doc_writer.py`
* Enforces approval gate:

  * execute only if proposal status == `approved`

Public functions:

```python
def validate_docops_payload(payload: dict, workspace_root: str) -> tuple[bool, list[str]]: ...
def execute_docops(workspace_root: str, proposal_id: str, session_id: str) -> dict: ...
```

### `app/tools/doc_writer.py`

* Implements actual document writes + archiving
* Implements atomic write for doc edits
* Produces ExecutionReport dict

Public functions:

```python
def apply_docops_actions(workspace_root: str, proposal_id: str, actions: list[dict]) -> dict: ...
```

---

## Required Public Interfaces (Must Exist)

### Runtime

```python
# app/runtime/docops.py
def validate_docops_payload(payload: dict, workspace_root: str) -> tuple[bool, list[str]]: ...
def execute_docops(workspace_root: str, proposal_id: str, session_id: str) -> dict: ...
```

### Tools

```python
# app/tools/doc_writer.py
def apply_docops_actions(workspace_root: str, proposal_id: str, actions: list[dict]) -> dict: ...
```

---

## Invariants (Non-Negotiable)

* DocOps writes only under `documents/`
* No execution without proposal approval (Gate A)
* Rewrite always archives first
* All writes are atomic
* All actions logged with pointers to artifacts
* DocOps execution never changes `.agent_ide/project_state.json` except:

  * clearing pending pointers if this was the pending proposal
  * adding execution report pointers if you track them (optional)

---

## Validation / Done Criteria

Anti Gravity must demonstrate:

1. **CreateDoc**: creates new file under `documents/`
2. **AppendDoc**: appends correctly
3. **RewriteDoc**: archives old version correctly and writes new version
4. **Gate enforcement**: execution refuses non-approved proposals
5. **Artifacts produced**: execution artifact exists
6. **Run log produced**: includes pointers and affected file list

---

## Forbidden Actions

* Do NOT implement PatchOps yet
* Do NOT implement LangGraph yet
* Do NOT implement Gradio UI yet
* Do NOT allow DocOps to write outside `documents/`
* Do NOT store proposal payloads under `documents/` (Option B artifact rule)

---

## Minimal “Manual Test Script” (for Anti Gravity to run)

1. Initialize workspace (Task 01)
2. Submit a DocOps proposal (Task 03 registry) with `CreateDoc` action for:

   * `documents/PROJECT_OUTLINE.md`
3. Transition proposal to `approved`
4. Execute `execute_docops()`
5. Confirm file created + execution artifact + run log
6. Submit `RewriteDoc` for same file
7. Approve + execute
8. Confirm `_archive/` has old version and new version is in place

---
