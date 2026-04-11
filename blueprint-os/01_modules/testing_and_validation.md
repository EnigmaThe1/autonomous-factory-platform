# Testing and Validation Module

## Purpose
Define how the platform proves correctness, regressions, and release readiness.

## Validation layers

### Unit tests
For pure logic:
- compiler normalization
- evidence sufficiency
- failure classification
- lifecycle transitions
- policy decisions

### Integration tests
For multi-module flows:
- mission start
- compile -> queue -> execute -> review -> validate
- blocked_before_schedule visibility
- recovery routing
- approvals

### UI/contract tests
For dashboard and adapters:
- visible outcome guarantee
- no dead-button behavior
- mission list/inspector refresh
- start/abort/resume/report interactions

### Regression mission matrix
Use the mission matrix as a behavioral acceptance suite across mission families.

## Release gate
A release candidate should not be promoted unless:
- core unit/integration suites pass
- matrix smoke subset passes
- no silent critical failure remains in start/action paths
- persistence and recovery invariants hold
