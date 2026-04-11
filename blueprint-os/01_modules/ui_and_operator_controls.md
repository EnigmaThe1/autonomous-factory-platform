# UI and Operator Controls Module

## Purpose
Describe the standalone operator experience.

## Required dashboard surfaces
- mission list
- mission inspector
- timeline/events
- approvals queue
- reports/artifacts
- compiler findings
- evidence status
- system health and diagnostics

## Non-negotiable UX rules
- no silent no-op actions
- every action must produce visible feedback
- blocked and failed states must be obvious
- operators must be able to understand why the system continued, replanned, or blocked
- mission compiler findings should be inspectable
- evidence sufficiency decisions should be explainable

## Controls
- start mission
- resume / abort
- approve / reject
- open report/artifact
- inspect compiler findings
- inspect evidence contract and recovery route
- change provider/routing defaults
- export logs/reports
