# Provider Routing Module

## Purpose
Define how models/providers are selected for mission roles and workloads.

## Routing principles
- choose the best model for the task, not one model for everything
- prefer stronger reasoning models for planning/compiler/review work
- allow cheaper/faster models for bounded formatting or simple tasks
- keep provider selection explicit and inspectable
- support local models later without changing mission semantics

## Initial routing stance

### Planner / Mission Compiler
- high reasoning quality favored
- must handle ambiguity, path normalization, and contract shaping well

### Researcher
- strong retrieval and summarization quality favored
- may use web-aware or context-heavy providers where policy allows

### Implementer
- balanced coding performance, tool-use discipline, and context retention

### Reviewer / Validator
- high judgment reliability and structured output discipline favored

## Requirements
- provider routing should be configurable per role
- mission contract may override defaults when justified
- failure/retry logic should permit fallback providers when safe
- all routing decisions should be visible in logs or operator views

## Future direction
- dynamic routing based on mission complexity and recent provider performance
- confidence and cost-aware provider orchestration
