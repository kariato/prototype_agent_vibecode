## Critique (so this doesn’t blow up)

If I dump all 0–10 in one blob, Anti Gravity will skim, miss invariants, and you’ll get cross-layer bleed. The handoff must be **stepwise packets** with: dependencies, exact files, interfaces, invariants, done criteria, forbidden actions. That’s what I’m giving you.

You asked “starting with step 0” — I’ll generate **Step 0 through Step 3** now (foundation). That’s the correct tranche to hand off first because everything else depends on it. You can paste these into Anti Gravity as-is.

---

# Anti Gravity Task Packet 00 — Repo Skeleton + Dotenv Loader

## Goal

Create the repo layout and a deterministic configuration loader from `.env` / environment variables. No workspace writes. No LangGraph. No Gradio UI.

## Depends On

* None

## Directory Layout (create)

```
app/
  main.py
  config/
    __init__.py
    env.py
    settings.py
  state/
    __init__.py
  runtime/
    __init__.py
  tools/
    __init__.py
  ui/
    __init__.py
documents/
  (empty placeholder for repo-level docs only, NOT workspace docs)
.env.example
README.md
```

## Files to Create / Contents Requirements

### `app/config/env.py`

* Load dotenv if present (local dev)
* Read environment variables
* Never crash on missing optional vars; must error on missing required vars
* Must not print secrets

### `app/config/settings.py`

Define a typed `Settings` object (Pydantic or dataclass) containing:

Required:

* `WORKSPACE_ROOT_DEFAULT` (string, optional; used only if user doesn’t select)
* `ALLOWED_WORKSPACE_ROOTS` (comma-separated list, optional; if set, enforce selection under these)
* `ARTIFACTS_DIRNAME` default: `.agent_ide/artifacts`
* `PROJECT_STATE_PATH` default: `.agent_ide/project_state.json`
* `DOCUMENTS_DIRNAME` default: `documents`
* `RUN_LOGS_DIRNAME` default: `documents/RUN_LOGS`
* `PHASES_DIRNAME` default: `documents/PHASES`
* `DECISIONS_DIRNAME` default: `documents/DECISIONS`
* `ARCHIVE_DIRNAME` default: `documents/_archive`
* `MAX_ACTIONS_PER_BUNDLE` default: 3
* `MAX_REPAIR_ATTEMPTS` default: 3
* `DENYLIST_PATH_PREFIXES` (list; defaults include `.git/`, `.agent_ide/` except artifacts/state, system dirs)

LLM-related placeholders (no usage yet):

* `LLM_PROVIDER`
* `OPENAI_BASE_URL`
* `OPENAI_API_KEY`
* `OPENAI_MODEL`

### `app/main.py`

* Minimal entrypoint that:

  * loads settings
  * prints a non-secret “config loaded” message
  * does not run UI yet

### `.env.example`

* Include all fields above with comments

### `README.md`

* “How to run” + “What this repo is (design constraints)”
* Explicitly state: no side effects outside tools; approvals required for mutations

## Public Interfaces (must exist)

```python
# app/config/settings.py
def load_settings() -> Settings: ...
```

## Invariants

* No filesystem writes to any workspace
* No network calls
* No UI
* No agent logic

## Validation / Done Criteria

* `python -m app.main` runs without error
* Missing required env var yields a clear error message
* No secrets printed

## Forbidden Actions

* Do NOT create Gradio UI
* Do NOT implement LangGraph
* Do NOT implement workspace initialization logic

---

# Anti Gravity Task Packet 01 — Workspace Bootstrap + Persistent State

## Goal

Implement workspace initialization and persistent state storage at:

* `/.agent_ide/project_state.json`
* and create the workspace doc directories.

## Depends On

* Task 00

## Directory Layout (workspace root, created on init)

Inside selected workspace root:

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

## Files to Create / Modify

Create modules:

```
app/state/
  state_schema.py
  project_state.py
  workspace.py
  locking.py
```

### `app/state/state_schema.py`

Define Pydantic (preferred) models:

**ProjectState**

* `workspace_root: str` (absolute path)
* `initialized_at: str` (ISO timestamp)
* `phase_status: dict[str, str]` (e.g., `"01": "completed"`)
* `runtime: RuntimeState`

**RuntimeState**

* `workspace_lock: WorkspaceLock | None`
* `pending_proposal_id: str | None`
* `pending_proposal_artifact_path: str | None`
* `last_checkpoint_id: str | None`
* `last_checkpoint_artifact_path: str | None`
* `resume_node: str | None`
* `repair_attempts_by_phase: dict[str, int]`

**WorkspaceLock**

* `locked_by_session_id: str`
* `locked_at: str`

### `app/state/locking.py`

* Implement a simple lock mechanism using project_state fields (no OS-level locking required yet, but safe design)
* Must prevent concurrent sessions from same workspace (fail closed)

### `app/state/workspace.py`

Responsibilities:

* Validate input path is absolute
* If `ALLOWED_WORKSPACE_ROOTS` set, enforce workspace under one of them
* Create directory structure (idempotent)
* Create `.agent_ide/artifacts` (idempotent)

### `app/state/project_state.py`

Responsibilities:

* Create default state if missing
* Load existing state
* Update state with patch (atomic write of JSON to avoid corruption)
* Must never store secrets in project_state

## Public Interfaces (must exist)

```python
# app/state/workspace.py
def init_workspace(workspace_root: str, session_id: str) -> "ProjectState": ...

# app/state/project_state.py
def load_state(workspace_root: str) -> "ProjectState": ...
def save_state(state: "ProjectState") -> None: ...
def update_state(workspace_root: str, patch: dict) -> "ProjectState": ...

# app/state/locking.py
def acquire_lock(workspace_root: str, session_id: str) -> None: ...
def release_lock(workspace_root: str, session_id: str) -> None: ...
```

## Invariants

* Workspace root must be absolute
* Writes must stay under workspace root
* Initialization must be idempotent
* State save must be atomic (write temp, rename)

## Validation / Done Criteria

* Initialize a new workspace → creates expected directories and state
* Re-initialize same workspace → no errors, state persists
* Lock acquisition blocks second session

## Forbidden Actions

* Do NOT implement DocOps or PatchOps yet
* Do NOT implement UI

---

# Anti Gravity Task Packet 02 — Artifact Store (Option B) + Run Logs

## Goal

Implement artifact persistence in:

* `/.agent_ide/artifacts/`
  and append-only narrative logs in:
* `/documents/RUN_LOGS/`

## Depends On

* Task 01

## Files to Create

```
app/state/
  artifacts.py
  run_logs.py
  paths.py
```

### `app/state/paths.py`

* Centralize derived paths from `workspace_root` + settings
* Must prevent path traversal (normalize + ensure under root)

### `app/state/artifacts.py`

Artifact naming conventions (must follow):

* `proposal_<ts>_<proposal_id>.json`
* `checkpoint_<ts>_<checkpoint_id>.json`
* `execution_<ts>_<proposal_id>.json`

Responsibilities:

* write artifact JSON (atomic)
* list artifacts by kind
* read artifact by path/ref
* return relative paths for storage in state

### `app/state/run_logs.py`

Responsibilities:

* append Markdown logs with timestamp
* create stable filename:

  * `run_<ts>_<label>.md`
* logs must reference artifact paths (relative)

## Public Interfaces (must exist)

```python
# app/state/artifacts.py
def write_artifact(workspace_root: str, kind: str, payload: dict, *, id: str) -> str: ...
def read_artifact(workspace_root: str, rel_path: str) -> dict: ...
def list_artifacts(workspace_root: str, kind: str | None = None) -> list[str]: ...

# app/state/run_logs.py
def append_run_log(workspace_root: str, title: str, body_md: str, *, related_artifacts: list[str] = []) -> str: ...
```

## Invariants

* Artifacts are machine truth, stored only under `.agent_ide/artifacts`
* Run logs are human narrative under `documents/RUN_LOGS`
* No artifact stored under documents (to avoid user confusion)
* All writes are atomic

## Validation / Done Criteria

* Create/read/list artifacts works
* Append run log works and includes artifact pointers
* All paths remain under workspace root

## Forbidden Actions

* Do NOT create proposal/approval logic yet

---

# Anti Gravity Task Packet 03 — Proposal Model + Unified Approval FSM

## Goal

Implement the unified proposal lifecycle and registry. This is the control plane that everything else plugs into.

## Depends On

* Tasks 01–02

## Files to Create

```
app/runtime/
  proposals.py
  approval_fsm.py
  registry.py
  validation.py
```

### `app/runtime/proposals.py`

Define proposal base structure and two types:

**Common fields**

* `proposal_id: str`
* `proposal_type: "docops" | "patchops"`
* `created_at: str`
* `created_by_session_id: str`
* `phase_id: str | None`
* `summary: str`
* `payload: dict` (DocOps or PatchOps payload)
* `status: "draft" | "validated" | "awaiting_approval" | "approved" | "rejected" | "executed"`
* `gate: "A" | "B"` (DocOps= A, PatchOps= B)
* `validation_messages: list[str]`
* `rejection_note: str | None`

### `app/runtime/approval_fsm.py`

* Enforce allowed transitions only
* Fail closed on invalid transitions

Allowed transitions:

* `draft -> validated`
* `validated -> awaiting_approval`
* `awaiting_approval -> approved|rejected`
* `approved -> executed`

### `app/runtime/registry.py`

* Persist proposals as artifacts:

  * `.agent_ide/artifacts/proposal_<ts>_<proposal_id>.json`
* Update `project_state.runtime.pending_proposal_*` pointers during awaiting approval
* Support retrieving proposal by id

### `app/runtime/validation.py`

* generic validation harness used later by DocOps/PatchOps
* For now: validate required fields present and gate assignment matches type

## Public Interfaces (must exist)

```python
# app/runtime/registry.py
def submit_proposal(workspace_root: str, proposal: dict) -> str: ...
def get_proposal(workspace_root: str, proposal_id: str) -> dict: ...
def list_proposals(workspace_root: str) -> list[dict]: ...

# app/runtime/approval_fsm.py
def transition(proposal: dict, new_status: str, *, note: str | None = None) -> dict: ...

# app/runtime/validation.py
def validate_proposal_minimal(proposal: dict) -> tuple[bool, list[str]]: ...
```

## Invariants

* No proposal executes without approval
* Proposals are immutable once approved (payload unchanged)
* Pending proposal pointers must be set only when status is `awaiting_approval`
* Rejection requires a note (corporate review friendliness)

## Validation / Done Criteria

* Submit proposal → stored as artifact
* Transition rules enforced
* Pending proposal pointers update correctly
* Listing proposals works

## Forbidden Actions

* Do NOT implement DocOps execution
* Do NOT implement PatchOps apply
* Do NOT implement LangGraph
* Do NOT implement Gradio UI

---

## NEXT HANDOFF CHUNK (after Anti Gravity completes 00–03)

When these are done, the next packets are:

* Step 4 DocOps
* Step 5 PatchOps + diffs
* Step 6 Atomic FS core
* Step 7 Apply + verify
* Step 8 LangGraph
* Step 9 UI
* Step 10 Walkthrough acceptance harness

Say: **“Generate handoff packets 04–06”** when you want the next tranche.
