# Execution isolation model

## Recommended MVP
- control plane service
- worker service
- per-mission temp directories
- bounded subprocess execution
- optional containerized lane for higher-risk tasks

## Isolation classes
- inline safe read lane
- bounded workspace mutation lane
- validation/build lane
- external connector lane
- high-risk sandbox lane

## Promotion rule
Higher-risk lanes must not automatically become the default for ordinary tasks.
