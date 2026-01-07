## Critique (this is your corporate proof layer)

If Step 10 is “just a demo,” it won’t survive review. It must be a **reproducible acceptance harness** that proves: approvals, artifacts, atomic apply, verification loop, repair cap, recovery banner. Ideally it runs without hand-editing files (except test commands the user runs).

---

# Anti Gravity Task Packet 10 — Phase 07 Walkthrough Acceptance Harness

## Goal

Deliver a **reproducible, end-to-end walkthrough** (and optional automated checks) that proves the system works from a clean workspace:

* Document-first flow works
* PatchOps diff-first flow works
* Approval gates work
* Atomic FS apply works
* Manual verification loop works (PASS/FAIL)
* Repair proposal generation works and respects cap
* Artifacts + run logs are produced and auditable
* Recovery detection works

This is the “acceptance package” for corporate review.

---

## Depends On

* Task 00–09 complete (full runtime + UI)

---

## Deliverables (Workspace Documents + Optional Tests)

### A) Walkthrough Document (Required)

Create in workspace documents:

```
documents/PHASES/phase_07_hello_world_walkthrough.md
```

It must contain:

* Preconditions
* Step-by-step actions in UI
* Expected artifacts and file outputs at each step
* Expected approval points and pauses
* Expected run logs that should exist
* Troubleshooting section (recovery required, stale state, rollback)

### B) Example Project Scaffold Generator (Recommended)

A small helper that creates a known workspace fixture for the walkthrough (so the reviewer doesn’t craft files manually).

Create repo tool:

```
app/tools/scaffold_phase07.py
```

This tool will create in the chosen workspace root:

```
adder.py
tests/test_adder.py
pyproject.toml  (or requirements.txt)
```

**Important:** This scaffold tool is still a “tool” (side effects allowed). It must write only within workspace root.

### C) Optional Automated Smoke Test (Nice-to-have, not required)

Create repo tests:

```
tests/e2e/test_phase07_walkthrough_smoke.py
```

This cannot run Gradio interactively, but it can:

* init workspace
* submit proposal
* approve proposal
* execute docops
* submit patchops
* validate diff exists
* approve
* execute patch apply
* record verification outputs (fake strings)
* ensure repair proposals generated
* verify artifacts and run logs exist

---

## Files to Create / Modify (repo code)

Create:

```
app/tools/scaffold_phase07.py
app/runtime/walkthrough_checks.py
```

Modify (only if needed):

```
app/ui/gradio_app.py   (add a “Phase 07 Scaffold Workspace” button)
documents templates (none in repo; all in workspace)
```

---

## Walkthrough Content Requirements (Document Contract)

### `documents/PHASES/phase_07_hello_world_walkthrough.md` must include:

#### 1) Setup

* Confirm `.env` configured
* Start the app
* Select absolute workspace path
* Click “Load / Init Workspace”
* Confirm lock acquired and state created

**Expected outputs:**

* `.agent_ide/project_state.json`
* `documents/*` folders

#### 2) DocOps proof (Gate A)

* In Runtime tab, submit a doc intent (example):

  * “Create PROJECT_OUTLINE.md with Phase list”
* Confirm DocOps proposal appears with up to 3 actions
* Approve (Gate A)
* Resume
* Confirm file exists and archive rules are in place on rewrite

**Expected artifacts/logs:**

* `proposal_*.json` in `.agent_ide/artifacts/`
* `execution_*.json` for docops
* `run_*_docops_*.md` in `documents/RUN_LOGS/`

#### 3) PatchOps proof (Gate B) — introduce a deliberate failure

* Scaffold baseline project (button or tool)
* Propose patch that breaks tests (example: make `add()` return wrong value)
* Confirm diff generated and visible
* Approve (Gate B)
* Resume to execute
* Confirm execution committed

**Expected artifacts/logs:**

* patch proposal artifact
* `patch_*.diff` in `documents/RUN_LOGS/`
* `execution_*.json` from Atomic FS
* `run_*_execute_patch_*.md`

#### 4) Verification FAIL → Repair loop

* User runs:

  * `pytest -q` (manual)
* Paste output, select FAIL, record verification
* Confirm repair proposal created and diff exists
* Approve repair proposal
* Resume execute repair
* Run pytest again
* Paste PASS

**Expected:**

* `verification_*.json`
* repair `proposal_*.json`
* repair `patch_*.diff`
* repair attempt counter incremented in state

#### 5) Repair cap demonstration (Required narrative, optional execution)

* Describe how to hit cap by failing 3 times
* Expected system behavior: “Repair limit reached; no further repairs auto-generated”

#### 6) Recovery detection demonstration

* Explain how to simulate leftover `.bak.<proposal_id>` or `.tmp` (or induce mid-apply crash)
* Confirm UI shows “Recovery Required”
* Confirm graph refuses execution until resolved

---

## Scaffold Tool Requirements

### `app/tools/scaffold_phase07.py`

Public interface:

```python
def scaffold_phase07_workspace(workspace_root: str) -> dict: ...
```

Creates:

* `adder.py` (simple add function)
* `tests/test_adder.py` (expects correct behavior)
* Minimal packaging:

  * `requirements.txt` (pytest) OR `pyproject.toml` (pytest)
    Choose one and be consistent.

Returns:

* files created list
* any warnings

**Safety:**

* Must not overwrite existing files unless explicit `force=True` param is passed (default False)

---

## Walkthrough Checks Helper (Optional but useful for reviewer confidence)

### `app/runtime/walkthrough_checks.py`

Provide functions that can be invoked to validate the workspace has expected outputs:

```python
def check_expected_paths(workspace_root: str, expected_rel_paths: list[str]) -> tuple[bool, list[str]]: ...
def check_artifact_exists(workspace_root: str, kind: str, contains: dict | None = None) -> tuple[bool, str | None]: ...
def check_run_log_contains(workspace_root: str, needle: str) -> tuple[bool, str | None]: ...
```

---

## UI Hook (Recommended)

Add a button in Runtime tab:

* “Create Phase 07 Scaffold”
  Calls:
* `scaffold_phase07_workspace(workspace_root)`

And writes a run log entry:

* `run_*_scaffold_phase07.md`

---

## Invariants (Non-Negotiable)

* Walkthrough must be executable by a developer with no tribal knowledge
* Every major claim must map to a visible artifact or run log
* Scaffold tool writes only within workspace root
* No Git required
* Tests are run by user, not by the agent

---

## Validation / Done Criteria

Anti Gravity must show:

1. Fresh workspace → walkthrough completes end-to-end
2. Generated artifacts exist:

* proposal, execution, checkpoint (if used), verification

3. Run logs exist and reference artifacts
4. Repair proposal generated on FAIL and capped
5. Recovery required state blocks execution

---

## Forbidden Actions

* Don’t turn this into a marketing doc
* Don’t rely on external services besides the LLM endpoint (which may be mocked)
* Don’t skip atomic behavior (Step 06) in walkthrough proof
* Don’t add new features (Git, auto-test running, etc.)

---

If you want to make this *extra* corporate-friendly, the next refinement is to add a **“Traceability Matrix”** mapping requirements → phases → artifacts (one page).
