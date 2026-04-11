# Module Boundaries

## Core modules
- mission-compiler
- mission-controller
- evidence-engine
- failure-and-recovery
- agent-runtime
- persistence
- diagnostics

## Platform UI modules
- dashboard frontend
- operator views
- report viewers
- approvals UI

## Adapter modules
- cursor adapter
- vscode adapter
- cli adapter
- future cloud/CI adapters

## Boundary rules
- adapters may not own canonical mission truth
- dashboard may not invent state not present in backend truth
- core modules should not depend on editor/webview APIs
- evidence and recovery logic should remain backend-side
