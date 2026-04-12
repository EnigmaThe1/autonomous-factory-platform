# Customization Pack Creator

## Purpose
Create a project-local overlay without changing the universal plugin core.

## Use when
- a project wants extra protected paths
- a team wants stricter coding or review rules
- domain-specific validation or reporting is needed

## Procedure
1. Identify what is truly project-specific.
2. Keep universal behavior in the core.
3. Put local rules in a separate overlay document or config.
4. Reference the overlay only when it exists.
5. Avoid hardcoding repo-specific assumptions into the plugin core.

## Output
- local overlay proposal
- what stays universal
- what becomes project-specific
