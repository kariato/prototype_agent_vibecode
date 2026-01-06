## Critique (so we don’t drift again)

If we don’t make dependencies explicit, Anti Gravity will “parallelize” the wrong things and you’ll get a UI bolted onto an unstable runtime. The correct order is **state + invariants first**, then proposals/approvals, then PatchOps, then LangGraph, then UI polish. Anything else is a rework trap.

---

# Implementation Order (Authoritative)

This is the order Anti Gravity should implement in. Each step lists **hard dependencies**, **outputs**, and **public interfaces**.

## Step 0 — Repo Skeleton + Env Loader

**Depends on:** nothing
**Outputs (code):**

* `app/main.py` (entrypoint)
* `app/config/env.py` (dotenv loader + typed config)
* `app/config/settings.py` (runtime settings object)

**Interfaces:**

* `load_settings() -> Settings`

---

## Step 1 — Workspace Bootstrap + State Persistence

**Depends on:** Step 0
**Outputs (code):**

* `app/state/state_schema.py` (Pydantic models)
* `app/state/project_state.py` (load/save/update + file locks)
* `app/state/workspace.py` (initialize directories)

**Interfaces:**

* `init_workspace(abs_path) -> ProjectState`
* `load_state(workspace_root) -> ProjectState`
* `save_state(state) -> None`
* `update_state(patch) -> ProjectState`

---

## Step 2 — Artifact Store (Option B) + Run Logs

**Depends on:** Step 1
**Outputs (code):**

* `app/state/artifacts.py` (read/write/list artifacts under `.agent_ide/artifacts/`)
* `app/state/run_logs.py` (append-only logs under `documents/RUN_LOGS/`)

**Interfaces:**

* `write_artifact(kind, payload) -> ArtifactRef`
* `read_artifact(ref) -> dict`
* `list_artifacts(kind=None) -> list[ArtifactRef]`
* `append_run_log(entry) -> RunLogRef`

---

## Step 3 — Proposal Model + Unified Approval State Machine

**Depends on:** Steps 1–2
**Outputs (code):**

* `app/runtime/proposals.py` (Proposal base + DocOpsProposal + PatchOpsProposal)
* `app/runtime/approval_fsm.py` (state transitions + invariants)
* `app/runtime/registry.py` (proposal registry stored via artifacts + pointers in state)

**Interfaces:**

* `submit_proposal(proposal) -> proposal_id`
* `validate_proposal(proposal) -> ValidationResult`
* `record_approval(proposal_id, decision, note=None) -> None`
* `get_proposal(proposal_id) -> Proposal`

---

## Step 4 — DocOps Writer + Archive Rules

**Depends on:** Steps 1–3
**Outputs (code):**

* `app/tools/doc_writer.py` (Create/Rewrite/Append/CreatePhaseDoc)
* `app/runtime/docops.py` (DocOps proposal assembly + validation + execution)

**Interfaces:**

* `execute_docops(proposal_id) -> ExecutionReport`

---

## Step 5 — PatchOps Spec Implementation (No Apply Yet)

**Depends on:** Steps 1–3
**Outputs (code):**

* `app/runtime/patchops.py` (PatchOps schema + validation rules)
* `app/tools/diffgen.py` (unified diff generator)
* `app/state/diff_artifacts.py` (stores diff into `documents/RUN_LOGS/*.diff`)

**Interfaces:**

* `validate_patchops(payload) -> ValidationResult`
* `generate_diff(payload) -> DiffRef`

---

## Step 6 — Atomic FS Core (Phase 08 checklist)

**Depends on:** Steps 1–2
**Outputs (code):**

* `app/tools/atomic_fs.py`

  * temp write
  * fsync
  * backup rename
  * rollback
  * recovery scan

**Interfaces:**

* `apply_transaction(patchops_payload) -> ExecutionReport`
* `scan_recovery(workspace_root) -> RecoveryReport`

---

## Step 7 — Patch Apply + Verification Loop (Phase 05 runtime)

**Depends on:** Steps 3, 5, 6
**Outputs (code):**

* `app/runtime/execution_engine.py`

  * apply approved patch proposals
  * record verification (user paste)
  * repair proposal generation (cap=3)

**Interfaces:**

* `execute_patch(proposal_id) -> ExecutionReport`
* `record_verification(proposal_id, passed, output) -> None`
* `generate_repair(proposal_id, verification_output) -> Proposal`

---

## Step 8 — LangGraph Runtime Orchestration

**Depends on:** Steps 3–7
**Outputs (code):**

* `app/runtime/langgraph/graph.py` (topology)
* `app/runtime/langgraph/nodes/*` (intake/route/assemble/validate/checkpoint/await/execute/verify/close/error)
* `app/runtime/langgraph/checkpointing.py` (checkpoint artifact writes + state pointers)
* `app/runtime/events.py` (event stream schema)

**Interfaces:**

* `run_graph(user_input) -> event_stream`
* `resume_graph(workspace_root) -> event_stream`

---

## Step 9 — Gradio UI (Panels + Wiring)

**Depends on:** Steps 1–8
**Outputs (code):**

* `app/ui/gradio_app.py`
* `app/ui/panels/`

  * `documents.py`
  * `diff_viewer.py`
  * `runtime_console.py`
  * `verification.py`
* `app/ui/actions.py` (UI handlers → runtime calls)

**Interfaces:**

* UI sends: intent / approve / reject / execute / paste verification
* UI renders: event stream + artifact viewers

---

## Step 10 — Phase 07 Walkthrough Harness (Acceptance Script)

**Depends on:** Steps 1–9
**Outputs (code+docs):**

* `documents/PHASES/phase_07_hello_world_walkthrough.md` (already spec’d)
* `tests/e2e/test_walkthrough_phase07.py` (optional automation)
* `sample/hello_agent_ide_py/` scaffold (optional)

**Interfaces:**

* Running the walkthrough produces required artifacts and logs

---

# Dependency Graph (Mermaid)

```mermaid
flowchart LR
  S0[Step 0\nRepo + dotenv] --> S1[Step 1\nWorkspace + project_state]
  S1 --> S2[Step 2\nArtifacts + Run Logs]
  S1 --> S3
  S2 --> S3[Step 3\nProposals + Approval FSM]

  S3 --> S4[Step 4\nDocOps Writer]
  S3 --> S5[Step 5\nPatchOps + Diff (no apply)]

  S2 --> S6[Step 6\nAtomic FS Core]
  S5 --> S7[Step 7\nPatch Apply + Verify Loop]
  S6 --> S7
  S3 --> S7

  S4 --> S8[Step 8\nLangGraph Runtime]
  S7 --> S8
  S5 --> S8
  S3 --> S8

  S8 --> S9[Step 9\nGradio UI]
  S4 --> S9
  S5 --> S9
  S7 --> S9

  S9 --> S10[Step 10\nPhase 07 Walkthrough Acceptance]
```

---

# Interface Boundaries (so Anti Gravity doesn’t blur layers)

## State Layer (`app/state/*`)

Owns:

* `project_state.json`
* locks
* artifact I/O
* run logs

Exports:

* `init/load/save/update`
* `artifact read/write/list`
* `append_run_log`

## Runtime Layer (`app/runtime/*`)

Owns:

* proposal definitions
* approval FSM
* validation policies
* execution orchestration
* LangGraph nodes

Exports:

* `submit/validate/approve/reject`
* `execute_docops/execute_patch`
* `record_verification`
* `run_graph/resume_graph`

## Tools Layer (`app/tools/*`)

Owns:

* side effects only (filesystem writes)
* diff generation
* atomic transactions

Exports:

* `doc_writer`
* `atomic_fs.apply_transaction`

## UI Layer (`app/ui/*`)

Owns:

* rendering
* user inputs
* wiring handlers

Exports:

* nothing (calls runtime only)

---

# Build Strategy Notes (to prevent rework)

* Do **not** start Gradio UI until Steps 1–7 are stable.
* Do **not** “shortcut” PatchOps apply without Atomic FS core.
* Do **not** store payloads in `documents/` (you chose artifact store B); surface them via UI viewers instead.

---

If you want this in a format Anti Gravity can consume as discrete tasks, say: **“convert into Anti Gravity task packets”** and I’ll output each step as a self-contained implementation brief (inputs, outputs, file list, tests, done-criteria).

Good. That reaction tells me we finally hit the **correct abstraction level**.

You now have three things that matter—and almost nothing extra:

1. **A frozen system design** (no more invention needed)
2. **A strict implementation order** (no accidental re-architecture)
3. **A dependency graph that enforces discipline**

At this point:

* You are **not** in the weeds.
* You are at the **handoff boundary** between design and execution.
* Anti Gravity can build this without “interpreting intent.”

### Why this version works (brief, concrete)

* Every step produces **real modules**, not concepts.
* Every step has **hard dependencies**, so nothing gets built prematurely.
* The UI is last, which prevents polish-driven architectural rot.
* Atomic execution is a first-class dependency, not a bolt-on.

### What *not* to do next

* Don’t add phases.
* Don’t “simplify” approvals.
* Don’t merge layers for convenience.
* Don’t let Anti Gravity skip Step 6 (Atomic FS). That’s the spine.

### Safe next moves (choose only one when ready)

* **Convert to Anti Gravity task packets** (clean handoff, zero thinking)
* **Freeze and pause** (this design will still be correct in a month)
* **Start Step 0–1 only** (bootstrap + state, no agent yet)

Nothing here is fragile. You can walk away and come back without losing coherence.

When you’re ready, just name the next move.
