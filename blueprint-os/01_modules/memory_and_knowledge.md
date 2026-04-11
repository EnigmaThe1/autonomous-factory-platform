# Memory and Knowledge Module

## Purpose
Define how Autonomous Factory stores, retrieves, and uses durable knowledge, mission memory, and operator context.

## Memory layers

### 1. Mission-local memory
- findings generated during a mission
- current assumptions and compiler findings
- intermediate evidence and task outcomes
- short-horizon working context

### 2. Project memory
- repo facts
- architectural invariants
- prior validated decisions
- recurring failure signatures
- accepted recovery patterns

### 3. Operator preference memory
- default autonomy preferences
- approval expectations
- preferred report shape
- deployment preferences
- recurring constraints

### 4. Program / platform memory
- canonical architecture truth
- implementation ledger state
- regression matrix outcomes
- promotion and rollback history

## Requirements
- memory must be typed and source-aware
- memory used in execution should distinguish verified fact from heuristic assumption
- durable memory should be exportable and auditable
- memory must never become the only source of truth when repo or runtime truth is available

## Retrieval priorities
1. current mission truth
2. current repo truth
3. canonical blueprint/ledger truth
4. durable operator preferences
5. prior mission history

## Future direction
- introduce richer retrieval with confidence and freshness scoring
- link memory to evidence contracts and mission compiler findings
