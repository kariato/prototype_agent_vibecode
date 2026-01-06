Good. Option A + no git + approval at each step is coherent. The “document-first, phased” requirement is the right constraint to stop the agent from hallucinating architecture and immediately coding itself into a corner.

That said, your current requirement has a flaw: **“Always create unit tests” + “end user runs them”** can deadlock. If the agent can’t execute tests, it can’t close the loop. That’s fine if you accept slower iteration, but then you must specify **what counts as “done”** at each phase without automated verification. We can fix this by making verification a **user-ack step** plus an optional “suggested command set” the user can run.

Below is a tightened **Specification v0.2** for your lightweight Gradio IDE.

---

# Spec: Lightweight Document-First Agent IDE (Gradio + LangGraph + OpenAI-compatible)

## 1) Operating model

### Workspace

* User selects a **local folder** as the workspace root.
* All reads/writes are constrained to this root.
* No git required. Change tracking is done via:

  * Patch artifacts (diff files)
  * File hashes
  * Run logs

### Document-first requirement (hard)

* A subdirectory **`/documents/`** must exist (auto-created if missing).
* The agent must **write documentation first** (markup files) and only then implement code.

**Markup format:** Markdown (`.md`) for readability and portability.

---

## 2) Canonical workflow: Phases + approvals

### Lifecycle

Every project change is handled as a **Phase Plan**. The agent must:

1. **Phase 0: Document the plan**

   * Create/overwrite: `/documents/PROJECT_OUTLINE.md`
   * Create: `/documents/PHASES/phase_01_<slug>.md`, etc.
   * Output includes:

     * Goal
     * Scope
     * Files expected to change
     * Acceptance criteria
     * Test plan (unit tests required)
     * Risk/rollback notes

2. **User approval #1: Approve the outline**

   * No code edits allowed before this approval.

3. **Execute Phase 1**

   * Agent produces **a proposed patch** for the phase.
   * Agent produces **unit test patch** in same phase (or a paired “test phase” if needed).
   * Agent produces **lint suggestions** and optional config but does not enforce running.

4. **User approval #2: Approve Phase 1 patch**

   * Apply patch only after explicit approval.

5. **User runs tests/lint (manual)**

   * UI provides one-click “copy commands” and a log box for results.
   * User pastes results back into chat.
   * (Optional: allow the app to run tests locally later, but not required in v1.)

6. **User approval #3: Accept Phase 1 verification outcome**

   * If failed, agent enters a “repair loop” for same phase with new proposed patch.

7. Repeat for each phase.

**Key rule:** A phase is not “complete” until:

* docs exist for the phase,
* patch applied,
* tests created,
* user confirms results (pass/fail) and approves closure.

---

## 3) Directory + document spec

### Required structure

* `/documents/`

  * `PROJECT_OUTLINE.md`
  * `/PHASES/`

    * `phase_01_<slug>.md`
    * `phase_02_<slug>.md`
  * `/DECISIONS/`

    * `ADR_0001_<slug>.md` (Architecture Decision Records; optional but recommended)
  * `/RUN_LOGS/`

    * `run_<timestamp>_<phase>.md`

### PROJECT_OUTLINE.md must include

* Project name (inferred or user-provided)
* Context / problem statement
* Constraints (your constraints become defaults)
* Glossary (optional)
* Phase list (numbered)
* Definition of Done (global)

### Each phase document must include (template)

* **Phase ID + Name**
* **Objective**
* **Non-goals**
* **Planned file changes** (paths)
* **Implementation steps** (bullets)
* **Acceptance criteria** (testable statements)
* **Unit tests to add** (files + scenarios)
* **Manual test steps** (commands)
* **Risks / rollback**
* **Approval checklist** (explicit)

**Critique:** If you don’t force “Planned file changes” and “Acceptance criteria”, the agent will drift into vague refactors. Those two fields keep it honest.

---

## 4) Gradio UI spec (minimum viable panels)

### A) Workspace panel

* Folder selector (path)
* “Scan workspace” button
* Read-only display:

  * detected languages
  * detected test frameworks
  * detected package managers

### B) Chat panel

* User ↔ agent messages
* Agent messages are categorized:

  * DOC (documentation output)
  * PLAN (phase plan)
  * PATCH (diff summary)
  * VERIFY (instructions/results handling)

### C) Tabs (right side)

1. **Documents**

   * File list rooted at `/documents`
   * Viewer/editor (read-only by default; user can edit if desired)
2. **Proposed Patch**

   * Diff viewer
   * “Approve & Apply” button
   * “Reject” button with reason input
3. **File Explorer**

   * Tree view + search box
4. **Run Logs**

   * Chronological runs, tool trace summaries

### D) Approval controls (always visible)

* Current step indicator: `Outline -> Phase N Doc -> Phase N Patch -> Verification -> Close`
* Buttons:

  * Approve step
  * Reject step
* Each approval creates an entry in `/documents/RUN_LOGS/…`

---

## 5) Agent contract: strict step gating

### Hard gates

* Gate 1: **Docs must be written** before patch generation.
* Gate 2: **Patch must be proposed** before apply.
* Gate 3: **User must approve** before apply.
* Gate 4: **Phase closure requires user-provided verification result**.

### Repair loop

If user reports failing tests:

* Agent must:

  * update the phase doc with a “Fix attempt #k” section
  * propose a minimal corrective patch
  * request approval again

**Critique:** Without updating the docs during repairs, you lose traceability and repeat mistakes.

---

## 6) Patch system (Option A strict)

### Patch artifact rules

* All edits expressed as diff hunks with:

  * file path
  * pre-image hash
  * post-image hash
* Patch saved to: `/documents/RUN_LOGS/patch_<timestamp>_<phase>.diff`

### Allowed operations (v1)

* Create file
* Update file
* Delete file (requires extra confirmation)

### Patch review requirements

* Diff viewer must show:

  * summary (files changed, LOC)
  * risk flags (new deps, deletes, big edits)
* User must approve before apply.

---

## 7) Unit test requirement

### Policy

* Every code-changing phase must include tests unless phase is explicitly “docs-only”.
* If no test framework is present:

  * Phase 1 should include adding one (minimal configuration)
  * Document the choice in an ADR

### Test deliverables

* Test plan in phase doc
* Test files in repo
* Commands to run tests (documented)
* User runs tests and pastes output

**Critique:** “Always create tests” is only meaningful if you also enforce “what tests” and “what scenarios.” Otherwise you’ll get a single trivial test that asserts `True`.

---

## 8) General-purpose language/framework handling

### Workspace detection (lightweight heuristics)

* Python: `pyproject.toml`, `requirements.txt`, `pytest.ini`
* JS/TS: `package.json`, `tsconfig.json`, `jest.config.*`, `vitest.config.*`
* Java: `pom.xml`, `build.gradle`
* Etc.

### Output behavior

* Agent should choose the most likely test framework from existing config.
* If ambiguous, default to:

  * Python → pytest
  * JS/TS → vitest (or jest if already present)
* Record framework choices in ADR.

---

## 9) Minimal persistence model (no git)

Store run state in `/documents/RUN_LOGS/` plus an internal session state:

* `session.json` (in app cache, not necessarily written to repo)
* Docs + diffs + approvals written to `/documents`

This gives you “auditability” without git.

---

## 10) LangGraph graph spec (node-level)

### Nodes

1. `Intake`

   * parse request, constraints
2. `OrientWorkspace`

   * scan tree, detect languages/frameworks
3. `DraftOutlineDocs`

   * write `PROJECT_OUTLINE.md` + phase docs
4. `AwaitOutlineApproval` (UI gate)
5. `RetrievePhaseContext`

   * read relevant files based on phase doc
6. `DraftPhasePatch`

   * produce patch + tests patch
7. `AwaitPatchApproval` (UI gate)
8. `ApplyPatch`
9. `AwaitUserVerification`

   * user provides test outputs
10. `ClosePhase`

* update phase doc with outcome

11. loop to next phase or repair loop

### State fields (conceptual)

* `workspace_root`
* `current_phase_id`
* `phase_docs_paths[]`
* `proposed_patch`
* `applied_patch_ids[]`
* `user_verification_logs[]`
* `decisions[]`

---

## 11) Acceptance criteria for the IDE itself (your build target)

### v1 is “done” when:

* User can select a folder.
* Agent creates `/documents/` + outline + phase docs.
* UI forces approval before any patch applies.
* Agent can propose patches and apply them.
* Patch artifacts + run logs are persisted in `/documents/RUN_LOGS/`.
* Agent can generate unit tests for at least Python + JS projects.
* User can paste test output and agent can create a fix patch.

---

## Two design forks you should decide now (they affect everything)

### Fork 1: Phase granularity

* **Option 1 (safe):** phases are small, 1–3 files each.
* **Option 2 (fast):** phases can be large, but you enforce strict acceptance criteria and risk scoring.

**My take:** choose Option 1. General-purpose + no git + manual verification means you need smaller diffs.

### Fork 2: Document overwrite policy

* **Option 1:** documents are append-only (history preserved).
* **Option 2:** documents rewritten for “current truth.”

**My take:** append-only for RUN_LOGS, but PHASE docs can be “living docs” with a changelog section.

---

## Probing question (non-social, design-critical)

When you say “Approval at each step,” do you mean:

1. approve **docs**, then approve **patch**, then approve **phase closure** (3 approvals per phase),
   or
2. approve **every individual file change** inside a patch?

Be careful: (2) will make the tool unusable. If you *think* you want (2), that’s your anxiety talking, not good design.

If you answer that one, I’ll lock the **exact step-state machine** (UI states + allowed buttons per state) and the **exact Markdown templates** for `PROJECT_OUTLINE.md` and `phase_XX.md` so the agent can’t wiggle out of structure.
