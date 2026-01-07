# Phase 07 — Hello World Walkthrough (Python + pytest)

**Phase ID:** 07
**Status:** Completed
**Last Updated:** 2026-01-06

---

## 1) Objective

Exercise the full system loop: **DocOps → Approval → PatchOps → Diff Review → Approval → Apply → Verify (FAIL) → Repair → Approval → Apply → Verify (PASS) → Close**.

---

## 2) Walkthrough Steps

### Step 1: Bootstrap
- [ ] Click "🚀 Bootstrap Workspace"
- [ ] Verify `documents/` and `.agent_ide/` are created.

### Step 2: Phase Plan
- [ ] In "Proposal JSON", type `@docs:phase create 07 hello-world-walkthrough` and click Submit.
- [ ] Verify a DocOps proposal is created for the Phase 07 doc.
- [ ] Approve and Execute.

### Step 3: Initial Patch (Intentional Fail)
- [ ] Submit a PatchOps proposal for:
  - `adder.py`: `def add(a,b): return a + b`
  - `tests/test_adder.py`: `def test_add(): from adder import add; assert add(2,2) == 5`
- [ ] Review Diff (ensure line `+ assert add(2,2) == 5` is visible).
- [ ] Approve and Execute.

### Step 4: Verification (FAIL)
- [ ] Run `pytest` manually.
- [ ] Paste `AssertionError: assert 4 == 5` into the Verification tab.
- [ ] Click **❌ FAIL**.
- [ ] Verify that a **Repair Proposal** is automatically generated in the Approval Center.

### Step 5: Repair & PASS
- [ ] Review Repair Diff (should fix `5` to `4`).
- [ ] Approve and Execute.
- [ ] Run `pytest` and paste passing output.
- [ ] Click **✅ PASS**.
- [ ] Confirm phase completion in logs.

---

## 3) Expected Outcomes
- Full audit history in `documents/RUN_LOGS/`.
- Proposal and execution artifacts in `.agent_ide/artifacts/`.
- State correctly tracked in `project_state.json`.
