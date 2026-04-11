# Recoverability-First Rule

When there is a trade-off between more raw autonomy and better recoverability, prefer better recoverability.

Examples:
- persist mission state before risky downstream work
- surface blocked outcomes instead of failing invisibly
- keep rollback/promotion explicit
- keep evidence contracts durable
- keep UI actions visibly acknowledged
