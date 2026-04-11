# Canonical Blueprint — Autonomous Factory

## 1. System identity

**Name:** Autonomous Factory

**System type:** AI-native autonomous software delivery platform

**Primary form factor:** Standalone backend + standalone web dashboard + optional thin editor adapters

**Primary operating mode:** Mission-driven, evidence-first, bounded autonomy

## 2. Mission

Autonomous Factory exists to turn high-level software goals into safe, observable, recoverable execution across planning, research, implementation, review, and validation without forcing the operator to hand-craft perfect prompts or babysit every step.

The platform should behave like a technically competent delivery controller:
- interpret rough operator intent
- reconcile it against repo truth and policy
- compile it into an authoritative execution contract
- route work to specialized agents
- use tools only when necessary
- recover intelligently from failure
- produce auditable evidence and promotion decisions

## 3. Users and operators

### Primary users
- solo founders building AI-native software systems
- technical leads running complex refactors or implementation missions
- platform engineers who want governed autonomous execution on real repositories
- advanced operators who need durable evidence, rollback, and mission traceability

### Secondary users
- reviewers and validators who inspect mission output
- product/operations stakeholders who need visibility into progress, risks, and decisions
- future enterprise teams who need policy-controlled automation over multiple repos

## 4. Core problem being solved

The current extension-host model is too fragile for the level of autonomy the system needs. Shared extension hosts, webview/service-worker issues, editor lifecycle quirks, and UI-bridge brittleness consume effort that should instead go into core mission intelligence.

The system therefore moves to a standalone architecture that solves:
- brittle prompt literalism
- weak mission intake and contract formation
- over-reliance on generic tools and heuristics
- poor distinction between optional and required evidence
- weak recoverability when tool failures are misclassified
- runtime coupling to third-party editor infrastructure

## 5. AI-native design stance

Autonomous Factory is explicitly AI-native.
It does not bolt a model onto an otherwise static workflow. The platform assumes that:
- mission intake must be interpreted, normalized, and compiled
- specialized agent roles produce better outcomes than one undifferentiated model loop
- tool use must be governed by necessity and evidence sufficiency
- autonomy must be bounded, observable, and recoverable
- architectural truth must remain durable across conversations, runs, and releases

The canonical five-agent model is preserved:
1. **Planner** — decomposes and sequences work
2. **Researcher** — resolves uncertainty and gathers evidence
3. **Implementer** — performs bounded changes and artifact generation
4. **Reviewer** — critiques output against intent and architecture
5. **Validator** — proves claims, runs checks, and controls promotion

The orchestrator/controller remains separate and supervises the loop.

## 6. High-level architecture

The system is composed of six major layers:

1. **Operator surfaces**
   - standalone web dashboard
   - REST/WebSocket API
   - optional thin adapters for Cursor, VS Code, CLI, and other clients

2. **Control plane**
   - mission intake
   - mission compiler/preflight
   - orchestration and routing
   - policy binding
   - approvals and promotion decisions

3. **Execution plane**
   - agent runtime
   - work-item runner
   - tool gateway
   - sandboxed workspace execution
   - artifact generation and mutation services

4. **Evidence and recoverability plane**
   - evidence contracts
   - tool necessity / evidence sufficiency evaluation
   - failure classification
   - recovery routing
   - rollback/promotion decision support

5. **State plane**
   - mission store
   - event/timeline store
   - implementation ledger
   - memory and knowledge services
   - artifact and evidence storage

6. **Adapter plane**
   - editor/file-system adapters
   - VCS adapters
   - CI/testing adapters
   - cloud/runtime adapters

## 7. Major components

### 7.1 Mission Compiler
Transforms raw user intent into a normalized, authoritative mission contract by reconciling it against repo truth, policy boundaries, input/output semantics, and execution feasibility.

### 7.2 Mission Orchestrator / Controller
Owns mission state transitions, routing, work-item scheduling, bounded autonomy, approvals, and mission completion semantics.

### 7.3 Agent Runtime
Runs the five specialist agents with role-specific task packets derived from the compiled contract.

### 7.4 Tool Gateway
Executes file, terminal, VCS, test, research, and integration tools behind policy and evidence gates.

### 7.5 Evidence Engine
Represents required/preferred/optional evidence, tool necessity, substitute evidence, and sufficiency-before-blocking decisions.

### 7.6 State and Ledger Services
Persist missions, work items, approvals, memory, artifacts, findings, reports, and implementation truth.

### 7.7 Operator Dashboard
Displays mission queue, timeline, approvals, reports, compiler findings, evidence status, agent activity, and system health.

## 8. Data and state model summary

The core persistent entities are:
- mission
- compiled mission contract
- work item
- evidence contract
- approval request
- recovery chain
- mission event / timeline entry
- report / artifact
- implementation ledger entry
- memory item / knowledge item
- run metrics and diagnostics

State must be durable, replayable, and safe to serialize.
No critical execution truth should live only in transient UI state.

## 9. Runtime and deployment summary

The preferred deployment model is:
- local-first Dockerized or native single-node stack for development
- optional remote multi-service deployment for heavier usage
- API + web frontend + worker services + durable database
- optional queue/cache layer for scaling
- optional adapters running near workspaces or repos

The editor extension becomes an adapter, not the main runtime host.

## 10. Safety, autonomy, and recoverability summary

The system must preserve the following invariants:
- never execute raw missions blindly
- always bind policy before mutation
- always prefer evidence before claiming completion
- never let optional tool failure block a mission by default
- always preserve a protected recovery spine
- always keep rollback and promotion decisions explicit
- always keep operator-visible outcomes for success, block, and failure
- never silently drop mission-start or action-trigger failures

## 11. Current implementation status

Current state is **transition-in-progress**.

Already proven or partially built in the extension codebase:
- mission orchestration concepts
- work-item lifecycle controls
- failure classification and recovery routing
- tool necessity / evidence sufficiency logic
- mission compiler preflight logic
- regression mission matrix documentation

Current weakness:
- heavy coupling to editor extension runtime, webviews, and shared host behavior

Strategic conclusion:
- retain reusable core logic
- migrate primary runtime into standalone platform
- keep editor integration as thin optional adapter

## 12. Roadmap summary

Near-term roadmap:
1. define standalone platform blueprint and migration plan
2. extract control-plane and mission-state logic into platform-core modules
3. build API and dashboard
4. build local execution/runtime adapter layer
5. reattach editor adapters as thin clients
6. run regression mission matrix on the standalone platform
7. add controlled self-improvement subsystem later

## 13. Open risks and unresolved decisions

Open items:
- exact persistence stack (Postgres only vs Postgres + queue/cache)
- sandboxing model for local tool execution
- multi-repo/multi-workspace tenancy boundaries
- how much of current extension code can be lifted directly vs rewritten cleanly
- exact adapter protocol for editor clients
- when to introduce structured compile-time blocking vs conservative continuation

## 14. Supporting files

- detailed architecture: `03_project_design/architecture.md`
- agent model: `03_project_design/agent_roles.md`
- orchestration: `01_modules/orchestration.md`
- tools: `01_modules/tools_and_capabilities.md`
- safety: `01_modules/safety_and_guardrails.md`
- execution plan: `04_execution/implementation_plan.md`
- roadmap: `01_modules/roadmap.md`


## v2 enhancement pass

This blueprint has been deepened in six operationally critical areas so the platform can move from architecture-level clarity toward build-ready specification:

1. observability and telemetry
2. authentication, RBAC, and auditability
3. execution isolation and resource governance
4. data contracts and event schemas
5. secrets, connectors, and credential governance
6. self-improvement governance and promotion control

These areas are no longer treated as secondary concerns. They are part of the canonical platform contract. Any implementation claiming conformance to this blueprint must respect the policies and interfaces defined in the v2 enhancement files.

## non-negotiable v2 invariants

- Every mission produces a traceable chain from intake to outcome.
- Every operator action produces a visible result, visible rejection, or visible error.
- Every connector and credential has explicit scope, auditability, and revocation semantics.
- Every execution lane has isolation, timeouts, quotas, and termination controls.
- Every stored mission contract, evidence contract, and event message is schema-governed.
- Self-improvement is missionized, bounded, validated, reversible, and never free-form self-rewrite.
