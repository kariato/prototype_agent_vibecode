# Traceability Matrix — Lightweight Agent IDE

## Purpose
Demonstrate end-to-end traceability from requirements through design phases, implementation artifacts, and verifiable outputs.

## Requirements Mapping

| Req ID | Requirement                           | Phase(s) | Primary Components                          | Artifacts / Evidence                         | Acceptance Signal                      |
| ------ | ------------------------------------- | -------- | ------------------------------------------- | -------------------------------------------- | -------------------------------------- |
| R-01   | Workspace isolated by absolute path   | 01, 12   | `state/manager.py`, `config/settings.py`    | `.agent_ide/project_state.json`              | Workspace root is absolute, validated  |
| R-02   | No Git dependency                     | All      | N/A (architectural)                         | Absence of git logic                         | No git calls, no repo assumptions      |
| R-03   | All config via dotenv + project state | 01, 12   | `config/settings.py`, `state/manager.py`    | `.env`, `project_state.json`                 | Settings reproducible, state persisted |
| R-04   | Document-first workflow               | 02       | `docops/protocol.py`, `docops/writer.py`    | `documents/*.md`, archive files              | Docs exist before code changes         |
| R-05   | Approval at each mutation step        | 03       | `proposals/models.py`, `main.py`            | proposal artifacts, checkpoints              | No execution without approval          |
| S-01   | Atomic file writes                    | 08       | `patchops/engine.py` (write_atomic)        | execution artifacts                          | No partial files                       |
| S-02   | Proposal-level all-or-nothing         | 08       | backup + rollback logic                     | `.bak.*`, execution report                   | Rollback restores state                |
| S-03   | Crash recovery detection              | 08       | `main.py` (scan_for_recovery)               | recovery report                              | UI blocks execution until resolved     |
| S-04   | Visual Timeline Traceability          | 12       | `runtime/events.py`, `main.py`             | `EventLog` markdown table                    | Color-coded historical audit trail     |
| V-01   | Manual verification only              | 05, 07   | `main.py` (handle_verification)             | verification artifacts                       | User pastes output                     |
| V-03   | Automatic repair proposal on FAIL     | 07       | `orchestration/repair_lane.py`              | repair proposal artifacts                    | Repair awaits approval                 |
| O-03   | Human-readable run logs               | 01-12    | run log writer                              | `documents/RUN_LOGS/*.md`                    | Reviewer readable narrative            |
| U-01   | Gradio-based UI                       | 01, 09   | `main.py`                                   | running UI                                   | Accessible locally                     |
| U-02   | Multi-panel separation                | 09       | `main.py` (Gradio Columns)                  | UI tabs/columns                              | Clear 4-panel separation               |
| U-03   | Typed Configuration UI                | 12       | `config/settings.py`                        | `.env` template                              | Validation for project parameters      |
