Good instinct. This is exactly what corporate reviewers look for when they want to answer **“can I trust this system?”** without reading 40 pages.

Below is a **clean, one-page Traceability Matrix** that maps **requirements → phases → concrete artifacts → proof signals**. This is paste-ready for Anti-Gravity *and* defensible in review.

---

# Traceability Matrix — Lightweight Agent IDE

## Purpose

Demonstrate end-to-end traceability from **requirements** through **design phases**, **implementation artifacts**, and **verifiable outputs**, ensuring:

* no hidden behavior
* no unverifiable side effects
* full auditability

---

## Legend

* **Req ID** — Stable requirement identifier
* **Phase(s)** — SDLC / Task Packets where requirement is implemented
* **Primary Components** — Code modules responsible
* **Artifacts / Evidence** — Files/logs that prove compliance
* **Acceptance Signal** — What a reviewer can check

---

## Core System Requirements

| Req ID | Requirement                           | Phase(s)           | Primary Components                          | Artifacts / Evidence                         | Acceptance Signal                      |
| ------ | ------------------------------------- | ------------------ | ------------------------------------------- | -------------------------------------------- | -------------------------------------- |
| R-01   | Workspace isolated by absolute path   | 00, 01             | `workspace.py`, `settings.py`               | `.agent_ide/project_state.json`              | Workspace root is absolute, validated  |
| R-02   | No Git dependency                     | All                | N/A (architectural)                         | Absence of git logic                         | No git calls, no repo assumptions      |
| R-03   | All config via dotenv + project state | 00, 01             | `env.py`, `settings.py`, `project_state.py` | `.env`, `.env.example`, `project_state.json` | Settings reproducible, state persisted |
| R-04   | Document-first workflow               | 04                 | `docops.py`, `doc_writer.py`                | `documents/*.md`, archive files              | Docs exist before code changes         |
| R-05   | Approval at each mutation step        | 03, 04, 05, 07, 08 | FSM + LangGraph pause nodes                 | proposal artifacts, checkpoints              | No execution without approval          |
| R-06   | Max 3 actions per proposal            | 03, 04, 05         | Proposal validation                         | proposal payload                             | Validation fails at >3                 |
| R-07   | Separate DocOps and PatchOps          | 03–05              | Proposal schemas                            | proposal artifacts                           | Gate A vs Gate B enforced              |

---

## Safety & Integrity Requirements

| Req ID | Requirement                      | Phase(s)   | Primary Components      | Artifacts / Evidence       | Acceptance Signal              |
| ------ | -------------------------------- | ---------- | ----------------------- | -------------------------- | ------------------------------ |
| S-01   | Atomic file writes               | 06         | `atomic_fs.py`          | execution artifacts        | No partial files               |
| S-02   | Proposal-level all-or-nothing    | 06         | backup + rollback logic | `.bak.*`, execution report | Rollback restores state        |
| S-03   | Crash recovery detection         | 06, 07, 08 | `recovery_scan.py`      | recovery report            | UI blocks execution            |
| S-04   | No side effects in orchestration | 08         | LangGraph nodes         | Code inspection            | Nodes call tools only          |
| S-05   | No UI direct writes              | 09         | UI handlers             | absence of FS writes       | UI is read + call-only         |
| S-06   | Denylisted paths protected       | 01, 05, 06 | path validation         | validation errors          | documents/.agent_ide untouched |

---

## Verification & Repair Requirements

| Req ID | Requirement                       | Phase(s) | Primary Components     | Artifacts / Evidence      | Acceptance Signal      |
| ------ | --------------------------------- | -------- | ---------------------- | ------------------------- | ---------------------- |
| V-01   | Manual verification only          | 07       | `verification.py`      | verification artifacts    | User pastes output     |
| V-02   | PASS/FAIL recorded immutably      | 07       | verification artifacts | `verification_*.json`     | Audit trail exists     |
| V-03   | Automatic repair proposal on FAIL | 07       | `repair.py`            | repair proposal artifacts | Repair awaits approval |
| V-04   | Repair attempts capped            | 07       | state counter          | `project_state.json`      | Repair stops at cap    |
| V-05   | Tests/lint run externally         | 07       | design constraint      | walkthrough doc           | No auto-test code      |

---

## Observability & Audit Requirements

| Req ID | Requirement                  | Phase(s)   | Primary Components  | Artifacts / Evidence      | Acceptance Signal       |
| ------ | ---------------------------- | ---------- | ------------------- | ------------------------- | ----------------------- |
| O-01   | All proposals persisted      | 03         | registry            | `proposal_*.json`         | Reconstructable history |
| O-02   | All executions logged        | 04, 06, 07 | execution artifacts | `execution_*.json`        | Deterministic replay    |
| O-03   | Human-readable run logs      | 02+        | run log writer      | `documents/RUN_LOGS/*.md` | Reviewer readable       |
| O-04   | Checkpoints before pauses    | 08         | checkpointing       | `checkpoint_*.json`       | Pause/resume works      |
| O-05   | Diff visibility before apply | 05, 09     | diff artifacts      | `.diff` files             | Reviewer sees changes   |

---

## UI & Interaction Requirements

| Req ID | Requirement                | Phase(s) | Primary Components | Artifacts / Evidence | Acceptance Signal  |
| ------ | -------------------------- | -------- | ------------------ | -------------------- | ------------------ |
| U-01   | Gradio-based UI            | 09       | `gradio_app.py`    | running UI           | Accessible locally |
| U-02   | Multi-panel separation     | 09       | UI panels          | UI tabs              | Clear separation   |
| U-03   | Approval & resume controls | 08, 09   | FSM + graph resume | events + state       | Explicit pauses    |
| U-04   | Artifact inspection        | 09       | artifact viewers   | JSON previews        | Audit-friendly     |
| U-05   | Recovery banner            | 06, 09   | recovery scan      | UI warning           | Execution blocked  |

---

## End-to-End Proof Requirement

| Req ID | Requirement                 | Phase(s)   | Primary Components     | Artifacts / Evidence | Acceptance Signal     |
| ------ | --------------------------- | ---------- | ---------------------- | -------------------- | --------------------- |
| E-01   | Hello World walkthrough     | 10         | scaffold + walkthrough | phase_07 doc         | New dev succeeds      |
| E-02   | Deliberate failure recovery | 06, 07, 10 | rollback + repair      | artifacts + logs     | No corruption         |
| E-03   | Full audit trail            | All        | combined               | proposals + logs     | Reviewer traceability |

---

## Executive Summary (for reviewers)

* Every **mutation** is proposed, approved, logged, and reversible
* Every **pause** is checkpointed
* Every **failure** is observable and recoverable
* The UI cannot violate system invariants
* The walkthrough proves the system, not slides

---

### Where this puts you

You now have:

* a **complete SDLC spec**
* a **stepwise execution plan**
* a **safety-first runtime**
* and a **traceability matrix that passes governance review**

This is no longer “an AI coding tool.”
It’s an **auditable engineering system**.

If you want one final tightening pass, the only remaining optional artifact is:

> **Risk Register (1 page)** — explicitly listing what the system refuses to do and why.

But you are already in a defensible position.
