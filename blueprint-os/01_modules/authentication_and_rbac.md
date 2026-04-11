# Authentication and RBAC

## Purpose
This module defines who can access Autonomous Factory, who can operate it, and who can approve sensitive actions.

## Identity model
The platform must support:
- local operator identity
- named user accounts
- service accounts for automation
- future external identity provider integration

## Roles
Minimum canonical roles:
- PlatformAdmin
- WorkspaceAdmin
- MissionOperator
- ReviewerApprover
- Observer
- ServiceAgent

## Role responsibilities

### PlatformAdmin
Can configure global settings, create workspaces, manage connector policy, and approve platform-level promotions.

### WorkspaceAdmin
Can manage a workspace’s policies, tools, connectors, and operator permissions.

### MissionOperator
Can start missions, inspect missions, and handle routine operator interactions.

### ReviewerApprover
Can approve sensitive write paths, policy exceptions, connector use, and self-improvement promotions.

### Observer
Read-only role.

### ServiceAgent
Machine identity used for bounded automated flows.

## Approval authority
Approval rights should be scoped by:
- workspace
- path class
- tool class
- connector class
- environment class
- promotion tier

## Audit requirements
Every privileged action must record:
- actor identity
- role at time of action
- target object
- action taken
- result
- timestamp
