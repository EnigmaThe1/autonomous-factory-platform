# Data contracts

## Purpose
This module defines the schema-governed contracts that connect AF subsystems.

## Canonical contracts
The platform must define and version schemas for:
- mission intake request
- compiled mission contract
- work item
- role packet
- evidence contract
- tool request / tool result
- approval request / approval outcome
- recovery decision
- operator event
- report artifact
- websocket / realtime event envelope

## Contract governance
- contracts must be versioned
- breaking changes require migration rules
- storage and API representations must be aligned
- dashboards and adapters must consume typed envelopes

## Core rule
No critical subsystem should communicate using only informal prose or ad hoc object shapes.
