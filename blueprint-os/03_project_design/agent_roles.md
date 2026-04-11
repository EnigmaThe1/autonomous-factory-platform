# Agents Module

## Purpose
Define the canonical specialist agents, their responsibilities, boundaries, and handoffs.

## Canonical agents

### Planner
- decomposes the compiled mission into staged work
- defines dependency order
- proposes replans when evidence changes
- never claims implementation completion without downstream proof

### Researcher
- resolves uncertainty
- gathers repo truth, environment truth, documentation, and external evidence where allowed
- feeds findings back into planning, review, and validation
- should avoid speculative claims when primary evidence is available

### Implementer
- performs bounded mutations, artifact generation, and execution actions
- must honor write scope, policy, and deliverable contracts
- cannot be considered done solely because tools ran; outputs must exist and match contract

### Reviewer
- critiques output against the compiled contract, architecture, and implementation quality
- should focus on current-scope deliverables, not future mission wishlists
- must distinguish advisory findings from hard blockers

### Validator
- proves claims through tests, checks, evidence, and explicit verdicts
- controls pass/fail/inconclusive validation states
- feeds promotion decisions and recovery routing

## Non-agent control-plane role

### Orchestrator / Controller
Not one of the five agents. Owns mission lifecycle, policy, routing, approvals, and recovery decisions.

## Agent interaction model
- agents receive role-specific packets, not raw user prompts
- outputs are machine-usable and evidence-linked when practical
- agent work remains subordinate to the compiled mission contract

## Key invariants
- no agent may silently widen scope
- no agent may bypass protected boundaries
- no agent may redefine mission truth unilaterally
- reviewer and validator should never be skipped in flows that require them
