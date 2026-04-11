# Data Flow

## Mission start flow
1. operator submits title/prompt via dashboard or adapter
2. mission record is persisted immediately
3. Mission Compiler reads workspace/repo truth and normalizes contract
4. compiler findings and normalized contract are stored
5. orchestrator seeds first work items
6. runtime emits events to dashboard and adapters

## Execution flow
1. orchestrator selects runnable work item
2. role packet is built from compiled contract
3. agent runs with scoped context and tools
4. evidence and outputs are recorded
5. review/validation consumes outputs
6. completion or recovery is decided

## Failure flow
1. tool/validation failure occurs
2. failure classifier evaluates cause
3. evidence sufficiency evaluates whether it matters
4. continue / retry / replan / block decision is taken
5. operator-visible outcome is emitted
