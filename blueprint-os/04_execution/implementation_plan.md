# Implementation Plan

## Stage 1 — Re-platform foundation
Outputs:
- repository structure for standalone platform
- platform-core package boundaries
- initial backend/frontend skeleton
- persistence schema draft

Validation:
- services boot
- health endpoint works
- dashboard shell loads

## Stage 2 — Mission start and compiler
Outputs:
- persistence-first mission creation
- Mission Compiler service
- compiler findings persistence
- visible blocked-before-schedule outcomes

Validation:
- wrong-path normalization test
- input/output separation test
- visible mission start outcomes

## Stage 3 — Orchestration and lifecycle
Outputs:
- queueing
- work-item lifecycle
- approvals
- completion/block semantics

Validation:
- queued -> running -> blocked/completed flows
- no silent action failures

## Stage 4 — Evidence and recovery
Outputs:
- evidence contracts
- tool necessity classification
- failure classification
- recovery routing

Validation:
- optional probe failure does not block by default
- required evidence failure routes correctly

## Stage 5 — Tool gateway and workspace execution
Outputs:
- bounded filesystem and terminal tools
- validation/test execution hooks
- artifact/report generation

Validation:
- scope enforcement
- protected boundary behavior

## Stage 6 — Dashboard UX
Outputs:
- mission list
- inspector
- timeline
- approvals and reports
- compiler findings panel

Validation:
- visible outcome guarantee for all major actions

## Stage 7 — Adapter reintegration
Outputs:
- thin Cursor/VS Code adapter
- CLI adapter

Validation:
- adapter actions reach backend correctly
- adapter failure does not corrupt platform truth

## Stage 8 — Regression certification
Outputs:
- first matrix run results
- release-candidate hardening

Validation:
- matrix subset passes
- key quality/latency metrics improve relative to extension-era baseline
