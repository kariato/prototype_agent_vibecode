## Critique (because Step 08 is a classic failure point)

If Anti Gravity builds LangGraph as “the place logic lives,” you’ll get side effects inside nodes and your whole safety model collapses. Step 08 must treat LangGraph as **orchestration only**: nodes call the already-built runtime/tool interfaces, and checkpoints/events are first-class.

---

# Anti Gravity Task Packet 08 — LangGraph Runtime Orchestration (Pause/Resume + Checkpoints)

## Goal

Implement a **LangGraph-based agent runtime** that orchestrates the already-built system:

* Intake user intent
* Route to DocOps vs PatchOps workflows
* Assemble proposals (DocOps/PatchOps)
* Validate proposals (fail closed)
* Write checkpoints before every pause
* Pause for human approval (Gate A/B)
* Execute via runtime engines (DocOps execute / Patch apply)
* Pause for manual verification (PatchOps only)
* Close phase by writing run log entries and clearing pointers
* Error handling + repair loop (cap=3)

**No side effects inside nodes.** Nodes must call existing runtime/tool interfaces.

---

## Depends On

* Task 00 (settings)
* Task 01 (workspace + project_state)
* Task 02 (artifacts + run logs)
* Task 03 (proposal + approval FSM + registry)
* Task 04 (DocOps)
* Task 05 (PatchOps diff-first)
* Task 06 (Atomic FS)
* Task 07 (Patch apply + verification loop)

---

## Files to Create / Modify

Create:

```
app/runtime/events.py
app/runtime/langgraph/
  __init__.py
  graph.py
  checkpointing.py
  state.py
  nodes/
    intake.py
    plan_route.py
    assemble.py
    validate.py
    checkpoint.py
    await_approval.py
    execute.py
    await_verification.py
    close_phase.py
    error_handler.py
```

Modify (only if needed):

```
app/state/state_schema.py
app/runtime/registry.py
app/runtime/execution_engine.py
app/runtime/docops.py
```

---

## LangGraph State Model (Frozen)

### `app/runtime/langgraph/state.py`

Define a Pydantic model `GraphState`:

Required fields:

* `workspace_root: str`
* `session_id: str`
* `user_input: str | None`
* `route: str | None`  # "doc" | "patch" | "show" | "noop"
* `phase_id: str | None`
* `proposal_id: str | None`
* `proposal_artifact_path: str | None`
* `checkpoint_id: str | None`
* `checkpoint_artifact_path: str | None`
* `last_event_id: int`  # monotonically increasing for UI stream
* `error: dict | None`
* `repair_attempts: int`  # local counter (global counter is in project_state)

Optional but useful:

* `messages: list[dict]`  # chat message log (role/content)
* `validation_messages: list[str]`
* `recovery_required: bool`
* `recovery_report: dict | None`

**Hard rule:** GraphState must be serializable to checkpoint artifact.

---

## Event Stream Contract (UI-facing later)

### `app/runtime/events.py`

Define `Event` objects (dict schema is fine, Pydantic preferred):

* `event_id: int`
* `ts: str`
* `type: str` (enum-like)
* `message: str`
* `payload: dict`

Event types (minimum set):

* `INFO`
* `STATE_UPDATE`
* `PROPOSAL_CREATED`
* `PROPOSAL_VALIDATED`
* `AWAITING_APPROVAL`
* `APPROVED`
* `REJECTED`
* `EXECUTION_STARTED`
* `EXECUTION_RESULT`
* `AWAITING_VERIFICATION`
* `VERIFICATION_RECORDED`
* `REPAIR_PROPOSED`
* `ERROR`
* `RECOVERY_REQUIRED`
* `CHECKPOINT_WRITTEN`
* `PHASE_CLOSED`

---

## Checkpointing (Mandatory)

### `app/runtime/langgraph/checkpointing.py`

Checkpoints stored as artifacts:

* `.agent_ide/artifacts/checkpoint_<ts>_<checkpoint_id>.json`

Checkpoint must include:

* `checkpoint_id`
* `created_at`
* `resume_node` (node name)
* `graph_state` (serialized)
* `proposal_id` (if any)
* `notes` (optional)

Update `project_state.runtime` pointers:

* `last_checkpoint_id`
* `last_checkpoint_artifact_path`
* `resume_node`

Interfaces:

```python
def write_checkpoint(workspace_root: str, state: dict, resume_node: str, session_id: str) -> str: ...
def load_last_checkpoint(workspace_root: str) -> dict | None: ...
```

---

## Node Responsibilities (No Side Effects Inside Nodes)

### Node: `intake`

**Input:** `user_input` string
**Output:** add `messages` entry, emit INFO event

### Node: `plan_route`

Determines:

* `route = "doc" | "patch" | "show" | "noop"`
* (Optional) infer `phase_id`

Rules (simple, deterministic for now):

* If input begins with `/doc` → doc
* If begins with `/patch` → patch
* If begins with `/show` → show
* Else default `doc` (document-first bias)

### Node: `assemble`

Creates a proposal payload (draft) based on route:

* For `doc`: create DocOps proposal with up to 3 actions (skeleton is OK)
* For `patch`: create PatchOps proposal skeleton (operations empty acceptable now) OR optionally accept provided payload in user_input
* For `show`: no proposal, just event output

**Important:** No LLM required in Step 08; keep assembly deterministic/skeleton-based.
(LLM integration can be added later as a tool call, but not required in this step.)

Calls:

* `submit_proposal()` from registry to persist as artifact
  Sets:
* `proposal_id`, `proposal_artifact_path`
  Emits:
* `PROPOSAL_CREATED`

### Node: `validate`

Calls the correct validator:

* DocOps: `validate_docops_payload`
* PatchOps: `validate_patchops_payload` and `generate_patchops_diff` if valid

Transitions proposal status accordingly:

* draft → validated → awaiting_approval
  Stores validation messages in proposal artifact and GraphState
  Emits:
* `PROPOSAL_VALIDATED` or `ERROR`

### Node: `checkpoint`

Writes checkpoint artifact and updates project_state pointers.
Emits:

* `CHECKPOINT_WRITTEN`

### Node: `await_approval` (PAUSE NODE)

This node must:

* write checkpoint with `resume_node="await_approval"`
* emit `AWAITING_APPROVAL`
* then halt execution until external signal updates proposal status

**Mechanism (design):**

* The runner returns control to caller with a “need approval” status.
* Resume is done by calling `resume_graph()` after approval/rejection.

### Node: `execute`

Dispatch based on proposal type:

* DocOps: `execute_docops(workspace_root, proposal_id, session_id)`
* PatchOps: `execute_patch_proposal(workspace_root, proposal_id, session_id)` (Step 07)

Emit:

* `EXECUTION_STARTED`
* `EXECUTION_RESULT`

If PatchOps committed successfully:

* proceed to `await_verification`
  If DocOps succeeded:
* proceed to `close_phase`
  If execution failed:
* go to `error_handler`

### Node: `await_verification` (PAUSE NODE)

For PatchOps only:

* write checkpoint with `resume_node="await_verification"`
* emit `AWAITING_VERIFICATION`
* halt until external verification is recorded

Resume is done by calling `resume_graph()` after verification recorded.

### Node: `close_phase`

* Append run log entry “phase closed”
* Clear any pending proposal pointers if appropriate
* Emit `PHASE_CLOSED`
* Write final checkpoint with `resume_node=None` (optional)

### Node: `error_handler`

Handles:

* validation errors
* execution errors
* stale state
* recovery required
* verification fail triggers repair proposals via Step 07 (already does this on record_verification; graph should surface and route back to await approval)

Rules:

* If recovery required: emit `RECOVERY_REQUIRED`, stop
* If proposal rejected: stop with event
* If repair proposed: set proposal_id to new repair proposal and route back to `await_approval`
* Cap repair loops at `MAX_REPAIR_ATTEMPTS` (from settings and/or project_state)

---

## Graph Topology (Frozen)

### `app/runtime/langgraph/graph.py`

Graph flow:

1. intake
2. plan_route
3. assemble
4. validate
5. checkpoint
6. await_approval (pause)
7. execute
8. checkpoint
9. (if patch) await_verification (pause)
10. close_phase

Error edges:

* from validate → error_handler
* from execute → error_handler
* from await_verification resume (if verification failed and repair created) → await_approval

---

## Runner Interfaces (Must Exist)

### `app/runtime/langgraph/graph.py`

```python
def run_graph(workspace_root: str, session_id: str, user_input: str) -> list[dict]: ...
def resume_graph(workspace_root: str, session_id: str) -> list[dict]: ...
```

`run_graph` returns an ordered list of Event dicts.

`resume_graph` loads last checkpoint and continues from `resume_node`.

---

## Recovery Integration (Required)

Before executing PatchOps in `execute` node:

* call `scan_recovery(workspace_root)`
* if issues exist:

  * emit `RECOVERY_REQUIRED`
  * stop (do not attempt execution)

---

## Invariants (Non-Negotiable)

* Nodes do not write files directly; they call runtime/tool interfaces only
* Checkpoint is written before any pause
* Approval is an external signal; graph pauses must be explicit
* Verification is an external signal; graph pauses must be explicit
* Proposal payloads remain in `.agent_ide/artifacts/`
* Diffs remain in `documents/RUN_LOGS/`
* Repair loops capped at `MAX_REPAIR_ATTEMPTS`

---

## Validation / Done Criteria (Must Demonstrate)

Anti Gravity must demonstrate without UI:

### Doc flow

1. `run_graph("/doc create PROJECT_OUTLINE")`
2. Graph creates DocOps proposal, validates, pauses for approval
3. Manually approve proposal (FSM + registry)
4. `resume_graph()` executes DocOps, closes phase

### Patch flow (happy)

1. `run_graph("/patch update adder.py ...")` (payload can be injected or skeleton)
2. Proposal validated, diff produced, pause for approval
3. Approve
4. `resume_graph()` applies patch via Atomic FS
5. Graph pauses for verification
6. Call `record_verification(passed=True, output="pytest ... PASS")`
7. `resume_graph()` closes phase

### Patch flow (fail → repair)

1. Same as above, but record FAIL
2. Repair proposal created
3. Graph routes back to await approval for repair proposal

---

## Forbidden Actions

* Do NOT build Gradio UI yet (Step 09)
* Do NOT embed side effects in LangGraph nodes
* Do NOT call the LLM in Step 08 (keep deterministic)
* Do NOT bypass approvals/verification pauses
* Do NOT implement PatchOps apply logic here (it’s Step 06/07)

---

If you want the next packet after 08, it’s **Task Packet 09 — Gradio UI Panels + Wiring** (now that runtime is complete).
