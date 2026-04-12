# Local Overlays

This directory is intentionally empty by default.

Projects can add optional local overlays here to specialize the universal kernel
without modifying the core plugin. A local overlay can define:

- protected paths
- preferred validation commands
- report formats
- project-specific agents or skills
- domain-specific capability pack entries

Suggested pattern:
- keep the universal core unchanged
- put project-only policy in a separate overlay file
- reference the overlay from the mission or operator instructions when needed
