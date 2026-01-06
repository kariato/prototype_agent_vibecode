Good choices. Small phases prevent thrash. “Rewrite docs but archive prior versions” is sane and keeps the docs readable while preserving history.

You only said “1 approve docs” and stopped—so I’m going to interpret that as: **you approve the outline/docs once per phase, and then you still want explicit approval to apply the patch** (otherwise “approval at each step” collapses). If that interpretation is wrong, it’ll show up immediately when we formalize the state machine.

## Critique (important)

If you approve docs but *don’t* approve patch application, you’ve created a rubber-stamp system: the agent can write nice docs and then do something else in code. The patch approval is the actual safety control. So the spec will keep **two approvals per phase** at minimum: **Doc approval** and **Patch approval**. Phase closure can be implicit once you paste test results, unless you want a third.

---

# Updated Spec Addendum: Archiving + Approval State Machine + Small Phase Rules

## A) Document rewrite + archive rule

### Rule

Any time the agent would overwrite an existing doc in `/documents/`, it must:

1. Move the existing file to `/documents/_archive/<YYYYMMDD_HHMMSS>/...` preserving relative path.
2. Write the new version to the original location.

### Example

* Existing: `/documents/PROJECT_OUTLINE.md`
* Archive to: `/documents/_archive/20260106_121530/PROJECT_OUTLINE.md`
* New file written to: `/documents/PROJECT_OUTLINE.md`

### Applies to

* `PROJECT_OUTLINE.md`
* any `/documents/PHASES/*.md`
* any ADR file if rewritten (rare; ideally ADRs are append-only, but your rule covers it)

**Non-archived**

* `/documents/RUN_LOGS/*` are append-only; no rewriting.

**Edge case**

* If the archive folder already exists for that timestamp (unlikely), add suffix `_01`, `_02`.

---

## B) “Small phase” constraints (Fork 1 Option 1)

A phase is considered valid only if it meets all of:

* touches **≤ 3 files** (excluding unit test files)
* total diff **≤ 200 LOC** (configurable)
* has **1 primary objective**
* has **explicit acceptance criteria**
* includes **unit tests** that correspond to acceptance criteria

If the agent cannot keep within constraints, it must split into Phase N / N+1.

**Critique:** Without a hard LOC/file cap, “small phases” becomes a vibe and agents will violate it under pressure.

---

## C) Approval state machine (per phase)

### States

**S0: Idle**

* No phase active.

**S1: Draft Phase Doc**

* Agent creates/updates:

  * `/documents/PHASES/phase_NN_<slug>.md`
  * (optionally) `/documents/PROJECT_OUTLINE.md` if outline changed
* Any overwritten docs must be archived first.

**Gate A: Doc Approval (you approve docs)**

* UI shows: phase doc content + checklist
* Buttons:

  * ✅ Approve Docs
  * ❌ Reject Docs (requires reason)

**S2: Retrieve Context**

* Agent is allowed to read/search project files relevant to phase.

**S3: Propose Patch**

* Agent outputs:

  * Patch (diff)
  * Test additions (diff)
  * Command suggestions (tests + optional lint)
* Patch stored as artifact in `/documents/RUN_LOGS/patch_<timestamp>_phaseNN.diff`

**Gate B: Patch Approval (must exist, or you lose safety)**

* Buttons:

  * ✅ Approve & Apply Patch
  * ❌ Reject Patch (requires reason)
  * 🟨 Request Revision (requires note: “reduce diff”, “split phase”, etc.)

**S4: Apply Patch**

* Apply patch to filesystem (no git).
* Record applied file hashes in run log.

**S5: Verification (user-run)**

* UI displays:

  * recommended commands (copy buttons)
  * a textbox for you to paste output
* Agent reads pasted output and decides:

  * pass → proceed
  * fail → create repair mini-phase *within same phase doc* (Fix attempt #k) and go back to S3

**S6: Close Phase**

* Agent rewrites phase doc to include:

  * results summary
  * pasted verification output (or excerpt)
  * final status: PASS/FAIL
* Archive old phase doc before rewrite.

Then either:

* start next phase → S1
* stop → S0

### Minimum approvals per phase

* **Doc Approval** (Gate A) ✅ (your requirement)
* **Patch Approval** (Gate B) **required for Option A** even if you didn’t re-state it

If you *insist* on only approving docs, say it explicitly and we’ll call it out as a deliberate risk.

---

## D) Phase doc template (locked format)

Filename: `/documents/PHASES/phase_NN_<slug>.md`

Required sections (agent must not omit):

1. **Objective**
2. **Scope**
3. **Non-goals**
4. **Files to change (max 3, exclude tests)**
5. **Acceptance criteria**
6. **Unit test plan**
7. **Manual commands**
8. **Risk / rollback**
9. **Approval checklist**
10. **Changelog**
11. **Verification results** (initially empty; filled at closure)

Changelog must include:

* timestamp
* author = Agent
* summary of doc rewrite reason

---

## E) UI implications (Gradio)

Always-visible “Phase Control Bar”:

* Current State (S1–S6)
* Current Phase (NN + name)
* Approve/Reject buttons only when at Gate A or Gate B
* “Show archive diff” link for docs when rewritten

---

## One design decision you still haven’t pinned down (critical)

When you approve docs (Gate A), do you want the phase doc to include:

* **exact file paths** (you already do), AND
* **exact function/class targets** (e.g., “edit `Foo.bar()`”), OR just file-level?

File-only is easier but looser. Function-level targets massively reduce agent wandering in general-purpose repos.

If you don’t answer, I’m going to default to **file paths + target symbols when discoverable** (best effort), because general-purpose otherwise turns into vague edits.
