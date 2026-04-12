# Generic Trust Policy

## Purpose
Define which capability sources are trusted, which require approval, and which are forbidden.

## Trust tiers
- T0: local core assets already bundled with the plugin
- T1: approved local or internal marketplace assets
- T2: approved public official sources
- T3: community or unknown sources that require explicit review

## Default activation policy
- T0: may auto-enable if mission requires it
- T1: may auto-enable if mission requires it and risk is low/medium
- T2: suggest first, ask before install or activation unless local policy says otherwise
- T3: never auto-install; research only until operator approval

## Risk bands
- low: research-only, read-only tools
- medium: code editing, local validation, safe MCP reads
- high: deployments, infra mutation, remote execution, secrets-adjacent tools

## Operator review triggers
- new plugin install
- new MCP server enablement
- networked package install
- deployment or infrastructure write actions
- actions touching credentials, billing, or production-like systems
