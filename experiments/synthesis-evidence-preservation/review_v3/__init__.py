"""Stores human judgments; does not perform semantic review or model generation."""

PROTOCOL_VERSION = "observable-evidence-lineage-v3"
SCHEMA_VERSION = "3.3.0"
BUILDER_VERSION = "3.3.0"
RULE_VERSION = "3.0.0-candidate"
STATUS = {
    "design": "DESIGN IMPLEMENTED",
    "human_review": "HUMAN REVIEW NOT STARTED",
    "codebook": "CODEBOOK CANDIDATE PREPARED",
    "pilot_human_review": "PILOT HUMAN REVIEW NOT STARTED",
    "main_human_review": "MAIN HUMAN REVIEW NOT STARTED",
    "human_labels": 0,
    "real_translation_assets_prepared": 0,
    "freeze": "NOT FINAL-FROZEN",
}
