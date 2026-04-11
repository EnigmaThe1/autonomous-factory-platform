# Autonomy and Recoverability Doctrine

## Core position
Autonomy is valuable only when recoverability is stronger than the autonomy itself.

## Consequences
- every autonomous action must remain within policy and scope
- every critical failure must produce a visible state change
- optional failures should not derail the mission
- required failures should produce structured recovery or clear block states
- mission history must remain durable and inspectable

## Product stance
The standalone platform is justified largely because it improves recoverability by removing dependence on fragile shared editor runtimes.
