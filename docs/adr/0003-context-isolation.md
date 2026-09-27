# ADR 0003: Deny-by-default context and capability projection

Status: accepted.

Only ContextBuilder reads authoritative state. Inputs and knowledge use exact
allowlists; artifacts require both policy selection and reader ACL; private and
long-term memory use agent namespaces. Serialized deep copies prevent mutation
of shared objects. A bound tool gateway checks every invocation. Prompts are not
access control. Trusted Python extensions remain inside the process trust boundary.

The shared-context benchmark uses separate explicitly broadened definitions;
it does not modify isolated policies. Publishing a summary intentionally releases
that artifact to its readers; arbitrary semantic secret detection is not promised.
