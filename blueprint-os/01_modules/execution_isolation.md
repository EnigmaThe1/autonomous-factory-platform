# Execution isolation

## Purpose
This module defines how AF executes work safely.

## Isolation layers

### 1. Mission isolation
Each mission should execute in a bounded mission context with:
- mission id
- workspace binding
- policy binding
- execution budget
- temp/runtime directories
- kill switch

### 2. Tool isolation
Tool invocations should be categorized by risk:
- read-only
- bounded write
- validation/build/test
- networked integration
- protected/high-risk

Each category should have default time, memory, and permission bounds.

### 3. Process isolation
Preferred execution model:
- backend process for control plane
- worker processes for tool execution
- optional container sandbox for risky or high-impact jobs

## Resource governance
Each mission should support:
- CPU limit
- memory limit
- wall-clock timeout
- step budget
- retry budget
- output size limits

## Kill and recovery semantics
The platform must be able to:
- terminate a mission
- terminate a work item
- terminate a tool subprocess
- mark partial execution as recoverable or not
- resume from durable state where safe
