# Glossary

## Adapter
A thin integration layer that connects Autonomous Factory to an external environment such as Cursor, VS Code, CLI, CI, or a cloud workspace without becoming the main runtime.

## Approval
An explicit operator-governed decision that allows a blocked or guarded action to proceed.

## Authoritative Mission Contract
The normalized, compiled mission specification produced by the Mission Compiler and consumed by downstream planning and execution.

## Bounded Autonomy
Autonomy constrained by policy, scope, evidence, recoverability, and explicit protected boundaries.

## Compiler Findings
The set of path corrections, ambiguities, contradictions, assumptions, and policy bindings discovered during mission compilation.

## Control Plane
The part of the platform responsible for mission intake, compilation, routing, state transitions, approvals, and governance.

## Evidence Contract
A structured statement of what evidence is required, preferred, or optional for a work item or mission decision.

## Evidence Sufficiency
The decision framework that determines whether enough evidence exists to continue, replan, retry, or block.

## Mission
A bounded unit of autonomous work initiated by an operator or internal subsystem.

## Mission Compiler
The subsystem that reconciles raw operator intent against repo truth, policy, and feasibility before execution begins.

## Mission Matrix
A reusable set of regression missions used to verify the system’s behavior across mission shapes and failure classes.

## Operator
A human who starts missions, reviews findings, grants approvals, inspects evidence, and controls promotion.

## Orchestrator / Controller
The supervisory subsystem that manages missions, work items, agents, failures, approvals, and completion.

## Protected Recovery Spine
The set of policies, paths, and mechanisms that must remain safe, observable, and recoverable even during failure.

## Standalone Platform
The target product form where the main runtime, dashboard, persistence, and orchestration live outside an editor extension host.

## Thin Editor Adapter
A lightweight extension/client used only to send workspace context, open files, and display state, while the main logic stays in the standalone platform.

## Work Item
A bounded unit of agent-assigned work within a mission.
