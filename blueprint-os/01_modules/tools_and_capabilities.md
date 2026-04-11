# Tools and Capabilities Module

## Purpose
Define the tool surface the platform can use and how it is governed.

## Tool categories
- filesystem read/write/edit tools
- terminal/command tools
- git/VCS tools
- test/build/lint tools
- research/fetch tools
- adapter tools (editor, CI, issue trackers, etc.)

## Governing principles
- tool use is subordinate to mission contract and evidence needs
- required/preferred/optional tool necessity must be explicit or inferable
- tool failures are interpreted through evidence sufficiency, not only raw tool status
- unsafe tool classes remain policy-gated

## Capability roadmap
Initial platform should support:
- local repo/workspace operations
- bounded terminal execution
- report/artifact generation
- validation command execution
- mission evidence capture

Later capabilities:
- multi-workspace adapters
- cloud runner execution
- enterprise integrations
- richer browsing/research and approval bundles
