# Data contracts

## Mission intake request
Fields:
- title
- raw mission text
- workspace id
- actor id
- adapter source
- requested provider/model hints

## Compiled mission contract
Fields:
- contract version
- normalized objective
- normalized scope
- normalized inputs
- normalized outputs
- path corrections
- compiler findings
- success criteria
- policy binding
- unresolved ambiguities

## Work item
Fields:
- work item id
- mission id
- role
- title
- step contract
- expected deliverables
- evidence contract reference
- dependencies
- status

## Event envelope
Fields:
- event id
- event type
- mission id
- work item id optional
- interaction id optional
- timestamp
- severity
- payload
