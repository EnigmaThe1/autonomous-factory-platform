# Workflows

## Workflow 1 — Start mission
- operator submits mission
- mission is persisted
- compiler runs
- normalized contract is stored
- controller seeds work and begins execution

## Workflow 2 — Approval flow
- guarded action triggers approval
- dashboard surfaces request
- operator approves/rejects
- controller resumes accordingly

## Workflow 3 — Recovery flow
- failure occurs
- classify cause
- evaluate evidence sufficiency
- continue / retry / replan / block
- emit visible outcome

## Workflow 4 — Report flow
- mission completes or blocks
- report bundle is generated
- operator reviews final verdict and evidence links
