# Overlay Policy Check

## Purpose
Detect whether a local project policy overlay exists and how it should affect the current task.

## Use when
- a project may have local conventions
- protected paths, report templates, or deployment gates may exist
- the universal core should defer to local policy

## Procedure
1. Look for local policy or overlay files.
2. Summarize any applicable local rules.
3. Separate mandatory local rules from optional conventions.
4. Fall back to universal behavior if no overlay exists.

## Output
- local overlay found or not found
- applicable local rules
- fallback behavior if none exists
