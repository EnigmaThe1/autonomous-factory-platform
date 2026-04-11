# Secrets and connectors

## Purpose
This module governs external access.

## Connector classes
- source control
- issue trackers
- CI providers
- cloud/storage providers
- model providers
- messaging/notification providers
- documentation/search providers

## Secret rules
- secrets are never persisted in plain mission state
- secrets are never logged in plaintext
- secret access is auditable at metadata level
- connectors are scoped by workspace and role
- missions receive connector authority through policy, not implicit inheritance

## Connector policy dimensions
- enabled / disabled
- allowed mission classes
- allowed roles
- read-only vs mutating
- approval required or not
- rate and quota limits
