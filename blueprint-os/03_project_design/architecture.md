# Architecture

## High-level structure

Autonomous Factory is organized as a layered standalone platform.

```text
Operator / Adapter Clients
  -> API + Realtime Gateway
    -> Mission Compiler
      -> Orchestrator / Controller
        -> Agent Runtime
          -> Tool Gateway / Workspace Runners
            -> Repo / Filesystem / Tests / External Integrations

Persistence and Diagnostics underpin all layers.
```

## Main services

### 1. API Gateway
Receives mission requests and operator actions, authenticates sessions in future versions, and fans out realtime updates.

### 2. Mission Compiler Service
- path normalization
- repo truth reconciliation
- input/output separation
- ambiguity classification
- authoritative mission contract generation

### 3. Mission Controller Service
- mission lifecycle
- queue scheduling
- approvals
- completion collapse
- failure/recovery control

### 4. Agent Runtime Service
- role packet execution
- model/provider routing
- structured outputs
- tool-use mediation

### 5. Tool Gateway / Runner Service
- bounded file actions
- terminal execution
- VCS/test/build operations
- evidence capture

### 6. State and Artifact Services
- database-backed mission truth
- artifact storage
- report storage
- ledger and diagnostics persistence

### 7. Dashboard Frontend
- operator list/inspect/control surfaces

## Migration architecture note
Extension-era modules should be split into:
- platform-core reusable logic
- adapter-specific UI/bridge logic
The latter must not contaminate the new core.
