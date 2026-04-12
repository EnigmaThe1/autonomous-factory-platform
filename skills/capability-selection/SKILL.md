# Capability Selection

## Purpose
Choose the minimum optional capability set required for a mission.

## Use when
- the mission may need plugins, MCP servers, specialist agents, or domain packs
- the operator wants a large available toolkit without loading everything at once
- the task spans multiple possible tool paths

## Inputs
- mission contract
- repo discovery findings
- capability registry

## Procedure
1. Summarize the mission and constraints.
2. List the optional capability classes that could help.
3. Check the registry for matching entries.
4. Separate capabilities into:
   - required now
   - useful later
   - unnecessary
5. Justify each selection.
6. Prefer the smallest sufficient set.
7. Note any validation or security implications.

## Output
- mission summary
- required now
- useful later
- rejected
- reasons
- activation order
