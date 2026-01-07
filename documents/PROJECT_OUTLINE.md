# Project Outline — Lightweight Document-First Agent IDE

## Context / Problem Statement
Current AI coding agents often suffer from "vibe-based" coding, where they begin implementation without a clear, approved plan, leading to architectural drift and unreviewable changes. This project aims to build an IDE that enforces a document-first workflow.

## Constraints
- **Absolute Paths**: All workspace references must be absolute.
- **No Git**: Traceability is handled via internal logs and archives.
- **Approval Gates**: Every document change and code patch requires explicit user approval.
- **Small Phases**: Changes are limited to ≤3 files and ≤200 LOC per phase.
- **Atomic Operations**: File writes must be atomic and include rollback support.

## Phases
1. [x] Phase 01: Project Bootstrap
2. [/] Phase 02: Documents UI + DocOps
3. [ ] Phase 03: Approval State Machine + PatchOps Gate
4. [ ] Phase 04: PatchOps Engine (Diff-First)
5. [ ] Phase 05: Atomic FS + Rollback
6. [ ] Phase 06: Manual Verification Loop
7. [ ] Phase 07: repair loop + Cap
8. [ ] Phase 08: LangGraph Runtime Orchestration
9. [ ] Phase 09: Gradio UI Integration (Full)
10. [ ] Phase 10: Walkthrough Acceptance Harness

## Definition of Done
- All phases implemented and verified.
- Traceability Matrix satisfies corporate audit requirements.
- Walkthrough succeeds in a clean workspace.
