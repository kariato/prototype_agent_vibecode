Next action is **Task Packet 07 — Patch Apply + Verification Loop (Phase 05 runtime)**.

### Why this is the next action (dependency reality)

* You now have **PatchOps proposals + diffs** (Step 05)
* You now have **Atomic FS transactional apply + recovery scan** (Step 06)
* Step 07 is the glue that turns those into the actual workflow:

  * “approved proposal → execute → user runs pytest → record PASS/FAIL → repair proposal (cap=3) → close”

If you jump to LangGraph (Step 08) now, you’ll end up re-implementing Step 07 logic inside graph nodes (bad layering). If you jump to UI (Step 09), you’ll build screens for functions that don’t exist yet.

### Concrete deliverable of Step 07

A runtime module that exposes these primitives:

* `execute_patch(proposal_id)`

  * calls Atomic FS apply
  * writes execution artifact + run log
  * updates project_state pointers

* `record_verification(proposal_id, passed, output)`

  * stores pasted output as artifact
  * on FAIL: generates a “repair” PatchOps proposal referencing the previous proposal
  * increments repair count (cap=3)

### The one decision to lock before Step 07

**Where does verification output live?**

* Recommended: `.agent_ide/artifacts/verification_<ts>_<proposal_id>.json` (Option B consistent)

If you want, I’ll generate **Task Packet 07** in the same strict format as 04–06.
Next action is **Task Packet 07 — Patch Apply + Verification Loop (Phase 05 runtime)**.

### Why this is the next action (dependency reality)

* You now have **PatchOps proposals + diffs** (Step 05)
* You now have **Atomic FS transactional apply + recovery scan** (Step 06)
* Step 07 is the glue that turns those into the actual workflow:

  * “approved proposal → execute → user runs pytest → record PASS/FAIL → repair proposal (cap=3) → close”

If you jump to LangGraph (Step 08) now, you’ll end up re-implementing Step 07 logic inside graph nodes (bad layering). If you jump to UI (Step 09), you’ll build screens for functions that don’t exist yet.

### Concrete deliverable of Step 07

A runtime module that exposes these primitives:

* `execute_patch(proposal_id)`

  * calls Atomic FS apply
  * writes execution artifact + run log
  * updates project_state pointers

* `record_verification(proposal_id, passed, output)`

  * stores pasted output as artifact
  * on FAIL: generates a “repair” PatchOps proposal referencing the previous proposal
  * increments repair count (cap=3)

### The one decision to lock before Step 07

**Where does verification output live?**

* Recommended: `.agent_ide/artifacts/verification_<ts>_<proposal_id>.json` (Option B consistent)

If you want, I’ll generate **Task Packet 07** in the same strict format as 04–06.
## Critique (so we don’t accidentally smear responsibilities)

Step 07 must **not** re-implement Atomic FS or PatchOps validation rules. It must orchestrate:

* “approved PatchOps proposal” → apply via Atomic FS
* “user verification output” → PASS/FAIL
* FAIL → repair proposal generation (cap=3)
  If Anti Gravity tries to be clever here, you’ll get duplicated logic and conflicting truth sources.

---

# Anti Gravity Task Packet 07 — Patch Apply + Verification Loop (Runtime Orchestration)

## Goal

Implement the **runtime workflow** for PatchOps execution and human verification:

1. Execute an **approved** PatchOps proposal by calling Atomic FS transaction apply
2. Pause for the user to run tests/lint externally
3. Record verification output (PASS/FAIL)
4. On FAIL, generate a **repair PatchOps proposal** (cap=3)
5. Persist artifacts + update `project_state` pointers consistently

This step produces runtime orchestration only. No LangGraph and no UI yet.

---

## Depends On

* Task 00 (settings)
* Task 01 (workspace + project_state)
* Task 02 (artifact store + run logs)
* Task 03 (proposal registry + approval FSM)
* Task 05 (PatchOps schema/validation + diff generation)
* Task 06 (Atomic FS apply + recovery scan)

---

## Files to Create / Modify

Create:

```
app/runtime/execution_engine.py
app/runtime/verification.py
app/runtime/repair.py
app/runtime/status.py
app/state/verification_artifacts.py
```

Modify (only if needed):

```
app/runtime/registry.py
app/state/state_schema.py
```

---

## Data Contracts (Frozen)

### Verification Artifact (Option B)

Stored in `.agent_ide/artifacts/` as:

* `verification_<ts>_<proposal_id>.json`

Fields:

* `proposal_id`
* `created_at`
* `session_id`
* `passed: bool`
* `raw_output: str`
* `parser_hint: str | None` (optional)
* `notes: str | None`

### Execution Flow States

We keep this in `project_state.runtime`:

* `pending_proposal_id` / `pending_proposal_artifact_path`
* `last_execution_artifact_path`
* `last_verification_artifact_path`
* `resume_node` (optional placeholder for LangGraph later)
* `repair_attempts_by_phase` (already in schema)

If `state_schema.py` lacks:

* `last_execution_artifact_path: str | None`
* `last_verification_artifact_path: str | None`
  add them now.

---

## Core Behaviors (Authoritative)

### 1) Execute Approved PatchOps Proposal

`execute_patch_proposal()` must:

Preconditions (fail closed):

* proposal exists
* proposal_type == patchops
* proposal.status == approved
* proposal.gate == "B"
* recovery scan reports no blocking incomplete transactions (see below)

Steps:

1. Run `scan_recovery(workspace_root)`

   * If issues exist:

     * write a run log entry “Recovery required”
     * return a structured error requiring manual recovery
2. Load proposal payload
3. (Optional but recommended) re-validate PatchOps payload against current workspace:

   * if pre_hash mismatch → refuse execution (`STALE_STATE`)
4. Call Atomic FS:

   * `apply_patchops_transaction(workspace_root, proposal_id, payload, session_id=...)`
5. Write execution artifact pointer into state:

   * `state.runtime.last_execution_artifact_path = <relpath>`
6. Transition proposal status:

   * if Atomic FS stage == committed → mark proposal executed
   * else (rolled_back/failed) → leave proposal approved (or mark executed_failed—pick one and freeze; recommended: do NOT advance to executed on failure)
7. Append run log entry summarizing result + pointing to execution artifact

Return:

* ExecutionReport dict (from atomic fs) plus proposal id

**Important:** Step 07 does not decide “pass/fail” of tests. Only file apply success/failure.

---

### 2) Record Verification (PASS/FAIL)

`record_verification()` must:

Preconditions:

* proposal exists
* proposal_type == patchops
* proposal was executed successfully (i.e., last execution stage committed)

  * If not, refuse verification as invalid sequence

Steps:

1. Write verification artifact JSON
2. Update state pointer:

   * `state.runtime.last_verification_artifact_path = <relpath>`
3. Append run log entry:

   * include passed/fail summary
   * pointer to verification artifact
4. If passed:

   * clear pending proposal pointers if they point at this proposal
   * return “verified_pass”
5. If failed:

   * increment repair attempt counter for the relevant phase

     * use `proposal.phase_id` if set; else use `"unknown"`
   * if attempts >= MAX_REPAIR_ATTEMPTS:

     * create a run log entry “Repair limit reached”
     * return “repair_blocked”
   * else generate repair proposal (below)
   * return repair proposal id + diff artifact pointer

---

### 3) Repair Proposal Generation (Fail → Repair PatchOps)

This step **does not apply** anything. It generates a new PatchOps proposal for review/approval.

Constraints:

* Repair proposal must reference the failed proposal:

  * `payload.meta = { "repair_of": "<proposal_id>", "verification_artifact": "<relpath>" }`
* Must still respect PatchOps constraints:

  * max 3 non-test files
  * no documents/.agent_ide
* Must generate diffs (Task 05)
* Must end in `awaiting_approval` state (Gate B)

How to generate repair:

* Minimal approach (acceptable): create a “repair-needed” proposal skeleton with placeholder operations and require the agent (later LangGraph) to fill it.
* Better approach (recommended for utility now): use a deterministic heuristic repair builder:

  * parse common pytest failure patterns (AssertionError, NameError, ImportError)
  * identify likely affected file from traceback
  * propose minimal patch to correct obvious issues (still as a proposal/diff, not applied)

**Critical:** No LLM calls are required in Step 07. Keep it deterministic; LangGraph will handle LLM later.

---

## Interfaces (Must Exist)

### Execution engine

```python
# app/runtime/execution_engine.py
def execute_patch_proposal(workspace_root: str, proposal_id: str, session_id: str) -> dict: ...
```

### Verification recording

```python
# app/runtime/verification.py
def record_verification(
    workspace_root: str,
    proposal_id: str,
    session_id: str,
    passed: bool,
    raw_output: str,
    *,
    notes: str | None = None
) -> dict: ...
```

### Repair generation

```python
# app/runtime/repair.py
def generate_repair_proposal(
    workspace_root: str,
    failed_proposal_id: str,
    verification_artifact_path: str,
    session_id: str
) -> str: ...
```

### Verification artifact writer

```python
# app/state/verification_artifacts.py
def write_verification_artifact(
    workspace_root: str,
    proposal_id: str,
    session_id: str,
    passed: bool,
    raw_output: str,
    notes: str | None = None
) -> str: ...
```

---

## Required Logging / Artifacts

For execute:

* execution artifact already written by Atomic FS (Task 06)
* must append run log:

  * `run_<ts>_execute_patch_<proposal_id>.md`

For verification:

* write verification artifact under `.agent_ide/artifacts/`
* append run log:

  * `run_<ts>_verify_<proposal_id>.md`

For repair:

* store repair proposal as artifact via proposal registry
* generate and store diff under `documents/RUN_LOGS/patch_<ts>_<repair_id>.diff`
* append run log:

  * `run_<ts>_repair_proposed_<repair_id>.md`

---

## Recovery Handling (must integrate)

Before executing patch proposals:

* call `scan_recovery()`
* if it returns issues, block execution and instruct “Recovery Required”
* write run log with RecoveryReport summary

---

## Invariants (Non-Negotiable)

* Never apply patches unless proposal is approved (Gate B)
* Never record verification unless last execution committed
* Repair attempts capped at MAX_REPAIR_ATTEMPTS
* Repair proposals still go through full PatchOps validation + diff generation
* No LLM calls in this step (LangGraph later)
* No UI in this step

---

## Validation / Done Criteria (must demonstrate)

Anti Gravity must demonstrate end-to-end **without UI**:

1. Create a workspace with:

   * `adder.py`
   * `tests/test_adder.py`
2. Create a PatchOps proposal that intentionally breaks tests
3. Approve it (via FSM)
4. Call `execute_patch_proposal()` → Atomic FS commits
5. Call `record_verification(..., passed=False, raw_output="<pytest output>")`

   * must create verification artifact
   * must create repair proposal in `awaiting_approval`
   * must generate repair diff artifact
6. Approve and execute repair proposal
7. Record PASS verification
8. Confirm:

   * run logs exist for execute/verify/repair
   * state pointers updated
   * repair attempt counter increments and stops at cap if forced to repeat failures

---

## Forbidden Actions

* Do NOT implement LangGraph yet
* Do NOT implement Gradio UI yet
* Do NOT bypass PatchOps validation
* Do NOT bypass Atomic FS
* Do NOT write proposal payloads under `documents/`

---
