# Task Lifecycle Module

## Purpose
Describe the lifecycle of missions and work items.

## Mission lifecycle
1. created
2. compiling
3. queued
4. running
5. awaiting_input / approval
6. blocked
7. completed
8. failed
9. cancelled
10. archived

## Work-item lifecycle
1. todo
2. in_progress
3. awaiting_approval
4. blocked
5. failed
6. dead_letter
7. done
8. skipped

## Lifecycle invariants
- every visible operator action should result in a visible lifecycle outcome
- work items must not transition to done without required evidence
- review/validation should stay phase-aware and scope-aware
- recovery chains must preserve ancestry and cause

## Required metadata
- parent work item
- retry count
- recovery chain id
- spawned-from-failure reference
- expected deliverables
- evidence contract reference
- changed files / affected artifacts where applicable
