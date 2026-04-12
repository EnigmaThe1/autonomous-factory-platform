# Host Boundary Awareness

## Purpose
Recognize when a task or tool action crosses from ordinary project work into host-machine-critical territory.

## Use when
- the task may touch operating system files
- the task may modify global packages or system configuration
- a command looks disk-destructive or privilege-sensitive
- you need to separate project-space freedom from machine-safety boundaries

## Procedure
1. Identify whether the action is inside project space or host-critical space.
2. Check whether the action touches system paths, credential stores, boot paths, or machine-level disk actions.
3. If host risk exists, suggest the smallest safer alternative.
4. Keep ordinary project work unconstrained.

## Output
- boundary classification
- risk summary
- safe alternative if needed
- note confirming preserved autonomy inside the task space
