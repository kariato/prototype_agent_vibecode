# Risk Register — Lightweight Agent IDE

This document explicitly defines the **boundaries of the system**. It lists what the IDE **refuses to do** (Out of Scope) and the **risks mitigated** by our Phase 01–10 architectural decisions.

## 1. Safety & Security Boundaries

| Risk Category | System Refusal / Constraint | Rationale (Mitigation) |
| :--- | :--- | :--- |
| **Direct Mutations** | Refuses to write files outside of the `app/tools` layer. | Prevents "hallucinating" agents from bypassing the approval state machine. |
| **Unapproved Changes** | Refuses to apply any code or document change without a signed approval record. | Ensures a human-in-the-loop for every filesystem side effect. |
| **Denylisted Paths** | Refuses to touch `.env`, `.git/`, `.agent_ide/` (except artifacts), or system directories. | Protects secrets and IDE internal state from agent corruption. |
| **Network Autonomy** | Refuses to allow agents to make outbound network calls (in v1). | Mitigates data exfiltration risks. User must run all external commands manually. |
| **Path Traversal** | Refuses any path containing `..` or absolute paths outside the workspace root. | Prevents "jailbreaking" the workspace sandbox. |

## 2. Integrity & Recovery Boundaries

| Failure Scenario | Defensive Strategy | Rationale |
| :--- | :--- | :--- |
| **Crashed Write** | **Atomic FS**: Writes to temp files, then renames. | Prevents corrupted or partial files if the process or machine crashes midway. |
| **Broken Code** | **Verified Repair Loop**: Forces user to run tests/lint and paste output. | Prevents agents from "assuming" code works. Verification is an external gate. |
| **State Drift** | **Shadow Archiving**: All rewrites move the pre-image to `_archive/`. | Provides a 100% reliable "undo" path even without git. |
| **Concurrent Access** | **Session Locking**: Writes a lock ID to `project_state.json`. | Prevents two agents or UI sessions from corrupting the same project simultaneously. |

## 3. Explicitly Out of Scope (Phase v1)

- **Automated Command Execution**: The system will NOT run `pytest`, `npm test`, or `lint` on its own. This is a deliberate safety gap.
- **Git Integration**: The system does NOT rely on git. It assumes it is the authoritative audit trail for the local workspace.
- **Multi-File Refactors (>3 files)**: Refuses to bundle more than 3 files per proposal to maintain human-reviewable diff density. 

## 4. Residual Risks

- **User "Blind" Approval**: The system cannot prevent a user from clicking "Approve" on a malicious patch. It only ensures that if they do, the action is **logged, archived, and attributable**.
- **Local Environment Poisoning**: Since the user runs the tests, any vulnerabilities in the project's dependencies are the user's responsibility to manage via their OS.

---
**Status:** Verified/Closed (Phase 13 Final Audit)
