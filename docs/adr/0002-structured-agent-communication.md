# ADR 0002: Schema-validated publications and explicit routing

Status: accepted.

Unbounded peer chat obscures dependencies and allows accidental disclosure.
Agents publish Pydantic-validated outputs as versioned artifacts. Messages route
references only to named recipients with intersecting visibility permissions.
Evidence references must originate in the sender's visible context. Uncertainty
is first-class. Free text may occur inside typed findings, not as control flow.
The tradeoff is that application authors must define schemas and routing upfront.
