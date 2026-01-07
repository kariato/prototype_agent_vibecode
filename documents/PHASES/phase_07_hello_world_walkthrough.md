# Walkthrough — Hello World (Acceptance Proof)

**Phase ID:** 07 (Formalized)
**Status:** Canonical Proof
**Last Updated:** 2026-01-06

## 1. Setup
1.  Initialize Workspace: Click **🚀 Bootstrap Workspace**.
2.  Add Scaffold: Click **🚀 Create Acceptance Scaffold**.
    - Expected: `adder.py` and `tests/test_adder.py` are created.

## 2. DocOps Proof (Gate A)
1.  Submit Intent: Paste `@docs phase create 10 Acceptance Proof` in the Manual Proposal Entry.
2.  Status: "Awaiting Approval".
3.  Action: Click **✅ Approve** and then **⚡ Execute Action**.
    - Expected: Document created in `documents/PHASES/`. Check **Navigator**.

## 3. PatchOps Proof (Gate B)
1.  Submit Intent: Create a PatchOps proposal that makes `add(a, b)` return `a + b + 1` (deliberate bug).
2.  Status: "Awaiting Approval".
3.  Inspect: Check **Diff Viewer** for the exact incorrect change.
4.  Action: Click **✅ Approve** and then **⚡ Execute Action**.
    - Expected: `adder.py` is updated.

## 4. Verification & Repair
1.  Verify: Run `pytest tests/test_adder.py` (externally).
2.  Action: Paste the failing output into the **Verification** tab and click **❌ FAIL**.
    - Expected: System generates a **Repair Proposal** and switches to it.
3.  Action: Click **✅ Approve** (Repair) and **⚡ Execute Action**.
4.  Verify: Run `pytest` again. Paste PASS output and click **✅ PASS**.
    - Expected: Phase is closed. Audit log updated.

## 5. Recovery Proof
1.  Induce: Manually create a file `.adder.py.bak.999` in the root.
2.  Refresh: Click **Refresh History**.
    - Expected: **🚨 Recovery Required!** alert appears.
3.  Action: Click **🗑️ Clean Up Artifacts**.
