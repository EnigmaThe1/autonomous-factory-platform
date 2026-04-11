# Storage and State Module

## Purpose
Define durable platform state and storage strategy.

## Core persistent entities
- mission
- mission runtime
- compiled mission contract
- compiler findings
- work item
- evidence contract
- approval request
- mission event
- mission report
- artifact/evidence file
- implementation ledger entry

## Preferred initial storage design
- PostgreSQL for structured mission/state truth
- filesystem or object storage for large artifacts/reports
- optional Redis or queue backend for concurrency and scheduling

## State design rules
- mission state must be serializable and replayable
- UI should derive from stored truth, not ephemeral front-end assumptions
- normalized contracts and findings must survive restart
- no critical state should depend on webview or editor cache

## Migration note
Current extension-era JSON/document-style mission persistence can inform the relational schema, but the standalone platform should formalize state transitions and durable indexes.
