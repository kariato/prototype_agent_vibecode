# Project Outline — Lightweight Document-First Agent IDE

## Context / Problem Statement
Current AI coding agents often suffer from "vibe-based" coding, where they begin implementation without a clear, approved plan, leading to architectural drift and unreviewable changes. This project has built an IDE that enforces a document-first workflow, strictly reviewed patches, and atomic execution with full auditability.

## Constraints (Verified)
- **Absolute Paths**: All workspace references are strictly absolute.
- **No Git**: Traceability is handled via internal logs, JSON artifacts, and file archives.
- **Approval Gates**: Every document change and code patch requires explicit user approval via FSM.
- **Small Phases**: Patch changes are limited to ≤3 files and ≤200 LOC per proposal.
- **Atomic Operations**: File writes use a temp->fsync->rename protocol with automatic rollback on failure.

## Implementation Phases (100% Complete)
1. [x] Phase 01: Project Bootstrap (Workspace & State)
2. [x] Phase 02: Documents UI & DocOps Protocol
3. [x] Phase 03: Unified Approval FSM & Proposal Registry
4. [x] Phase 04: PatchOps Protocol & Unified Diff Generation
5. [x] Phase 05: PatchOps Engine (Hash Validation & File Targeting)
6. [x] Phase 06: Runtime Checkpointing, Resumption & Artifact Stores
7. [x] Phase 07: Repair Loop Logic & Attempt Capping
8. [x] Phase 08: Atomic FS Core (Backup/Rollback/Recovery)
9. [x] Phase 09: Full UI Consolidation (4 Canonical Panels)
10. [x] Phase 10: Acceptance Harness & Scaffold Tools
11. [x] Phase 11: Hand-Off Protocol & Risk Management
12. [x] Phase 12: Architectural Hardening & Visual Timeline UI

## Final Status: COMPLETED
The system is ready for production-level local use. All core invariants (safety, atomic writes, and traceability) are active and verified.
