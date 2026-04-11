# Roadmap Module

## Phase 0 — Platform re-foundation
- finalize standalone blueprint
- identify reusable extension-era core logic
- define package boundaries
- define migration rules

## Phase 1 — Core platform skeleton
- API service
- mission store
- event store
- worker/runtime process
- minimal web dashboard

## Phase 2 — Mission Compiler and orchestration core
- port or rebuild mission compiler
- port work-item lifecycle and mission controller
- preserve persistence-first outcomes

## Phase 3 — Evidence and recovery engine
- make evidence contracts first-class
- port necessity/sufficiency logic
- port failure classification and recovery routing

## Phase 4 — Agent runtime and tool gateway
- role packet execution
- sandboxed workspace actions
- adapter boundaries for file/terminal/git/test tools

## Phase 5 — Dashboard and operator UX
- mission list
- inspector
- timeline
- approvals
- reports
- compiler findings
- error/outcome visibility

## Phase 6 — Adapter integration
- Cursor adapter
- VS Code adapter
- CLI adapter
- optional CI/Git host integrations

## Phase 7 — Regression matrix execution and hardening
- run matrix on standalone platform
- compare against extension-era failure patterns
- tighten telemetry and promotion rules

## Phase 8 — Deferred advanced capabilities
- controlled self-improvement
- multi-repo coordination
- distributed runners
- enterprise policy packs

## v2 roadmap note
The next execution-ready planning pass should derive concrete repo structure, service manifests, and schema-first API definitions from the new v2 module files.
