Good. Your head hurting is a signal that we’ve accumulated enough structure that the **next step should be concrete**. If we keep abstracting, you’ll lose the thread and start making contradictory decisions.

Also: I’m locking in that **Option 2 (Execution Hardening)** is queued right after the walkthrough. Not optional, just *sequenced*.

## Critique

A walkthrough that’s too “toy” will lie to you. It has to include at least one realistic failure (hash mismatch, failed tests, repair proposal) or it won’t validate the runtime spec. If it’s only “happy path,” it’s basically a demo, not a spec test.

---

# Phase 07 — End-to-End “Hello World” Walkthrough

**Location:** `/documents/PHASES/phase_07_hello_world_walkthrough.md`

## 1) Objective

Create a canonical, step-by-step walkthrough that exercises the complete loop:

**DocOps → Approval → PatchOps → Diff Review → Approval → Apply → User-run tests → Failure → Repair proposal → Approval → Apply → Pass → Close phase**

This walkthrough becomes:

* the user guide
* the acceptance test script
* the regression spec for future changes

## 2) Scope

* Define a minimal sample workspace (can be a tiny Python project)
* Define exact user actions (UI buttons + chat commands)
* Define expected agent outputs (DocOps/PatchOps blocks)
* Define expected artifacts created
* Define at least **one forced failure** and repair loop

No code implementation here—just the scripted scenario and expected behaviors.

## 3) Non-goals

* No performance tuning
* No automatic test execution
* No multi-user features
* No new protocols

## 4) Walkthrough scenario (the actual script we’ll write)

We’ll do **one micro-feature** with tests.

### Proposed sample project (choose one)

**Option A (recommended): Python “adder” library**

* `adder.py` with `add(a,b)`
* tests with `pytest`
* small diffs, very deterministic

**Option B: Node “string utils”**

* `utils.js` with `slugify()`
* tests with `vitest`
* slightly more moving parts

**Option C: Mixed minimal (too much for Hello World)**

* avoid; it creates noise

### Must include these events

1. **Bootstrap** workspace (Phase 01 behavior)
2. **Create/Rewrite** outline + phase doc via DocOps (bundle ≤3)
3. **Approve docs** (unified approval UI)
4. **Propose PatchOps** for adding a function + tests
5. **Review diff** in diff viewer
6. **Approve patch** (Gate B)
7. **Apply patch**
8. **User runs tests** and pastes output
9. **Forced failure** (intentional)

   * Example: test expects wrong output OR missing import
10. Agent generates **repair PatchOps** proposal (repair attempt #1)
11. Approve repair, apply, re-run tests
12. Pass, close phase, confirm logs + artifacts + pointers

### Forced failure method (pick one)

* **Failure type 1 (best):** a test that fails due to an intentional mismatch, then repair updates code/test to align.
* **Failure type 2:** stale-state hash mismatch by editing a file manually between propose and apply (this tests STALE_STATE_ERROR).
* **Failure type 3:** IO error (permissions) — realistic but annoying to reproduce.

I recommend we include **Failure type 1** in the core walkthrough, and keep Failure type 2 as an optional “advanced walkthrough.”

## 5) Expected artifacts checklist (what the walkthrough asserts)

* `/documents/PROJECT_OUTLINE.md` exists
* `/documents/PHASES/phase_07_hello_world_walkthrough.md` exists
* `/documents/RUN_LOGS/run_*` entries exist for each major step
* `/.agent_ide/project_state.json` updated with:

  * pending proposal pointers during approval pauses
  * last checkpoint pointers
* `/.agent_ide/artifacts/` contains:

  * proposal payload(s)
  * checkpoint snapshots/summaries
  * execution report(s)
* Archive folder only appears if docs are rewritten

## 6) Acceptance criteria

The walkthrough is “done” when someone can follow it and observe:

* the UI pauses at approvals correctly
* resuming works
* a failure creates a repair proposal
* repair cap enforcement is *not* triggered (only 1 repair here)
* everything is visible via the Proposal/Checkpoint/Execution viewers

---

## Two ways to proceed (you choose)

1. **Lock the sample project choice** (A/B) and I’ll write the full Phase 07 doc script end-to-end.
2. If you don’t want to decide: I’ll default to **Option A (Python + pytest)** because it’s the cleanest signal-to-noise.

Which do you want: **A (Python/pytest)** or **B (Node/vitest)**?

Locked: **Phase 07 uses Python + pytest**.

## Critique

If we don’t explicitly force one failure and one recovery, Phase 07 will be a feel-good demo that proves nothing. So this walkthrough will include an **intentional failing test** on the first pass, then a repair PatchOps proposal that fixes it.

---

# Phase 07 — Hello World Walkthrough (Python + pytest)

**File:** `/documents/PHASES/phase_07_hello_world_walkthrough.md`
**Status:** Draft
**Last Updated:** 2026-01-06

---

## 1) Objective

Provide a canonical end-to-end walkthrough that exercises the full system loop:

**DocOps → Approval → PatchOps → Diff Review → Approval → Apply → User-run tests → FAIL → Repair proposal → Approval → Apply → PASS → Close**

This document is both:

* a user guide
* a runtime acceptance test
* a regression checklist

---

## 2) Scope

* Local workspace
* Python minimal project
* pytest-based unit testing
* Includes one deliberate failure + one repair
* Uses unified approval state machine

No code is implemented in this doc—only the scripted flow and expected artifacts.

---

## 3) Non-goals

* No performance testing
* No automated test execution
* No lint enforcement (optional, not required here)
* No concurrency testing
* No execution hardening (queued next as Phase 08)

---

## 4) Preconditions

### Environment

* Python installed in the environment used to run tests
* pytest available (installed by user if needed)

### IDE configuration assumptions

* `.env` exists for runtime options
* Workspace is within allowed roots (if configured)

### Repair cap

* Repair cap is 3, but this walkthrough should use **only 1** repair attempt.

---

## 5) Sample Project Definition (Hello World Project)

### Workspace root

User creates/selects a folder, e.g.:

* `hello_agent_ide_py/`

### Minimal file target

We will create (via PatchOps):

* `adder.py`
* `tests/test_adder.py`

**Note:** Creation of these files occurs through PatchOps proposals, not direct writes.

---

## 6) Walkthrough Script (Step-by-Step)

### Step 1 — Bootstrap workspace (Phase 01 behavior)

**User action (UI):**

* Select `hello_agent_ide_py/`
* Click `Initialize / Bootstrap`

**Expected outcomes:**

* Directories created:

  * `documents/`, `documents/PHASES/`, `documents/DECISIONS/`, `documents/RUN_LOGS/`, `documents/_archive/`
  * `.agent_ide/`
* State created:

  * `.agent_ide/project_state.json` exists and includes absolute `workspace.root_path`
* Run log created:

  * `documents/RUN_LOGS/run_<ts>_phase01_bootstrap.md`

**UI checks:**

* Workspace shows status “initialized”
* Run log visible in Run Logs tab

---

### Step 2 — Create Phase 07 walkthrough doc via DocOps (bundle ≤ 3)

**User action (chat command):**

* `@docs:phase create 07 hello-world-walkthrough`

**Expected agent response:**

* A single `<DOCOPS>...</DOCOPS>` block with ≤ 3 actions, typically:

  1. `CreatePhaseDoc` for this Phase 07 doc
  2. `AppendLog` (optional)
  3. (Optional) Outline update only if needed

**Expected UI behavior:**

* UI enters `DocOps_Proposed`
* “Write Docs” is disabled until approval

**Approval:**

* User approves the proposal (Gate A style)
* User clicks “Write Docs”

**Expected artifacts:**

* `documents/PHASES/phase_07_hello_world_walkthrough.md` created
* Doc proposal artifact stored:

  * `.agent_ide/artifacts/proposal_<ts>_<proposal_id>.json`
* Run log references proposal artifact path

---

### Step 3 — PatchOps proposal #1: Create adder + tests (INTENTIONAL FAIL)

**User intent (chat):**

* “Create a minimal `add(a,b)` function and a pytest test suite. Make the first run fail intentionally so we can test the repair loop.”

**Expected agent response:**

* A single `<PATCHOPS>...</PATCHOPS>` block (file-level only) containing:

  * `adder.py` (create)
  * `tests/test_adder.py` (create)
* Validation passes:

  * paths are inside workspace
  * no denylisted paths
  * ≤ 3 non-test files constraint observed (tests excluded by rule)
* Diff viewer shows the unified diffs

**Deliberate failure requirement**

* The initial test must fail. Example pattern:

  * Code returns `a + b`
  * Test asserts wrong expected value for one case (e.g., expects `add(2,2)==5`)
    This is deliberate and documented in the proposal summary.

**Approval:**

* User approves PatchOps proposal (Gate B)
* Execution begins only after approval

**Expected artifacts:**

* Proposal artifact:

  * `.agent_ide/artifacts/proposal_<ts>_<proposal_id>.json`
* Diff artifact (human readable):

  * `documents/RUN_LOGS/patch_<ts>_phase07.diff`
* Checkpoints recorded before/after approval and execution
* Execution report artifact:

  * `.agent_ide/artifacts/execution_<ts>_<proposal_id>.json`

---

### Step 4 — Apply PatchOps proposal #1

**User action (UI):**

* Click “Execute / Apply Proposal” (enabled only in Approved state)

**Expected behavior:**

* Pre-hash validation occurs (create operations have null pre_hash)
* Files are written:

  * `adder.py`
  * `tests/test_adder.py`
* Execution finishes SUCCESS (apply success ≠ test success)

**Expected UI events:**

* `EXECUTION_STARTED`
* `EXECUTION_FINISHED` with report pointer

---

### Step 5 — User-run verification (pytest) — EXPECT FAIL

**User action (outside UI):**

* Run tests:

  * `pytest -q` (or equivalent)
* Paste output into verification textbox

**Expected result:**

* FAIL (one assertion failure)

**Expected UI behavior:**

* UI enters `Awaiting_Verification` then records `VERIFICATION_RECORDED` as fail

**Expected logging:**

* Run log entry includes pasted output excerpt and marks verification FAIL

---

### Step 6 — Repair PatchOps proposal #2 (attempt 1 of max 3)

**Agent behavior:**

* Analyze pasted output
* Generate a repair PatchOps proposal (new proposal_id) referencing failed proposal_id
* Keep scope minimal (likely update only the failing test expectation OR clarify acceptance criteria)

**Expected PatchOps content:**

* `tests/test_adder.py` (update)
* Possibly `adder.py` (only if bug truly exists)

**Approval:**

* User reviews diff
* Approves repair proposal (Gate B)

**Apply:**

* User applies repair
* Execution succeeds

**Artifacts:**

* New proposal artifact + execution report artifact
* Run log references both and marks “Repair attempt 1”

---

### Step 7 — Re-run pytest — EXPECT PASS

**User action:**

* Run `pytest -q`
* Paste output

**Expected result:**

* PASS

**Expected system response:**

* Phase 07 marked successful
* Close-phase behavior writes final run log entry and updates phase status in `project_state.json`

---

## 7) Required UI Evidence Checklist

During this walkthrough, the user must be able to view:

* Proposal History:

  * both PatchOps proposal IDs + statuses
* Checkpoint History:

  * checkpoints around approval pauses
* Execution Reports:

  * show applied files
* Run Logs:

  * narrative timeline, with pointers to artifacts

If any of these views are missing, Decision 1 (Option B artifacts) has not been properly compensated for.

---

## 8) Expected Files After Completion

At workspace root:

* `adder.py`
* `tests/test_adder.py`

Under control directories:

* `documents/PHASES/phase_07_hello_world_walkthrough.md`
* `documents/RUN_LOGS/run_*_phase07*.md`
* `documents/RUN_LOGS/patch_*_phase07.diff`
* `.agent_ide/project_state.json`
* `.agent_ide/artifacts/proposal_*`
* `.agent_ide/artifacts/execution_*`
* `.agent_ide/artifacts/checkpoint_*`

---

## 9) Failure Injection Notes (Why this is required)

This walkthrough intentionally forces a test failure to prove:

* the verification pause works
* repair proposal generation works
* approval gating works for repairs
* audit artifacts remain coherent across attempts

---

## 10) Changelog

* **2026-01-06** — Initial draft created by Agent

---

## 11) Gate A Status

⛔ **Not Approved**

---

## Next legal move

If this Phase 07 doc matches what you want, say:

**“Approve Phase 07 Docs”**

Then the next step is the Phase 07 **Build Packet** (still no code): exact UI actions, exact expected event sequence, and the required state/artifact fields that must change at each step.

Also queued (not forgotten): **Execution Hardening** as the subsequent phase after Phase 07.
