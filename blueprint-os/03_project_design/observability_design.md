# Observability design

## Goals
- make AF diagnosable under real operator load
- reduce time spent guessing why a mission failed
- correlate mission compiler, orchestration, tool, and UI behavior

## Event bus model
All major subsystems publish structured events into a common event stream. Events are persisted to the database and optionally exported to an analytics store.

## Core correlation chain
- session id
- workspace id
- mission id
- work item id
- interaction id
- tool invocation id

## Minimum event families
- compiler events
- orchestration events
- tool events
- evidence events
- approval events
- UI/operator action events
- adapter events

## Operator-facing panels
- compiler findings panel
- mission timeline panel
- runtime diagnostics panel
- start-attempt status panel
