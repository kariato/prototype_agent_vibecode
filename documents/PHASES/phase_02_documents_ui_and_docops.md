# Phase 02 — Documents UI + DocOps Command Protocol

**Phase ID:** 02
**Status:** Draft
**Last Updated:** 2026-01-06

---

## 1. Objective

Define and implement the **document creation workflow** in the IDE, including:

* a Gradio UI focused on `/documents`
* a machine-parseable **DocOps** command protocol that packages “create/overwrite/archive document” into explicit agent actions
* strict guardrails so the agent can only write within `/documents` and must archive before rewrite

This phase establishes how the user and agent collaboratively generate the **project outline + phase docs + ADRs + run logs** under approvals.

---

## 2. Scope

This phase is limited to:

* UI panels and controls required to:
  * view `/documents`
  * request creation of `PROJECT_OUTLINE.md`
  * request creation of `PHASES/phase_XX_*.md`
  * approve/reject document outputs (Gate A)
  * show archive history for rewritten docs
* Definition of a **DocOps protocol** (structured actions) including:
  * CreateDoc
  * RewriteDoc (with archival)
  * AppendLog
  * CreatePhaseDoc (templated)
  * CreateADR (templated)
* Mapping DocOps → LangGraph “agent actions” (node/tool boundaries), without implementing broader PatchOps yet
* Rules for doc rewrite + archive (Option 2: rewrite current, archive old)

---

## 3. Non-Goals

This phase explicitly does **not**:

* Implement PatchOps or apply code changes
* Run tests or commands
* Implement full Approval Gate B (patch approval)
* Implement LangGraph repair loops
* Add repo-wide code search features (beyond what’s needed for doc creation)
* Modify anything outside `/documents` (except minimal state transitions already defined in Phase 01)

---

## 4. Files to Change (Max 3, Excluding Tests)

This phase is permitted to create/modify only:

1. `/documents/*` (create/rewrite/archive docs + add run logs)
2. `/.agent_ide/project_state.json` (update doc-related state only)
3. `/documents/RUN_LOGS/*` (append-only new log files)
4. `app/` directory for implementation code (NEW)

---

##  acceptance criteria

* The UI has a “Documents” workspace that can:
  * list docs under `/documents`
  * open and display selected doc content
* The user can trigger doc generation actions:
  * Create/Rewrite `PROJECT_OUTLINE.md`
  * Create a new Phase doc using the locked template
  * Create an ADR doc using an ADR template
* Any doc rewrite automatically archives the old version to:
  * `/documents/_archive/<timestamp>/<relative_path>`
* Agent outputs doc edits as **DocOps actions** in a structured, parseable format
* The UI shows a preview of proposed doc changes and requires **Gate A approval** before writing
* All doc writes and approvals create a run log entry in `/documents/RUN_LOGS/`

---

## 7. Manual Commands

* How to start IDE
* How to bootstrap a workspace

---

## 8. Risks and Rollback

### Risks
* Agent writes outside `/documents`
* Accidental overwrite without archive
* DocOps format drifts and becomes unparseable
* UI allows write without approval

### Rollback
* No destructive rollback
* All doc operations are reversible via archived copies
* Fail closed: if parsing/validation fails, do not write

---

## 10. Changelog
* **2026-01-06** — Initial draft created by Agent
