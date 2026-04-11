# Orchestration Module

## Purpose
Describe how the controller runs missions from intake to completion.

## Responsibilities
- create/persist missions
- invoke Mission Compiler preflight
- bind policy and scope
- enqueue work items
- dispatch agent tasks
- interpret outcomes
- manage approvals
- classify failures
- route recovery
- decide completion, block, or cancellation

## Core loop
1. mission intake
2. mission compilation
3. queue/work-item creation
4. agent dispatch
5. tool/evidence execution
6. review/validation
7. recovery/replan if required
8. completion or blocked outcome

## Key orchestration rules
- persistence first
- compiler before normal execution
- no silent action failures
- no blocking from optional tool failures by default
- no phase-inaccurate review of future deliverables
- no completion without required evidence

## Long-term design
The orchestrator should become a true central brain:
- understanding mission type
- choosing the right level of rigor
- allocating agent roles wisely
- reducing wasted work early
- keeping operator-visible truth coherent at all times
