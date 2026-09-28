# Pilot human review

MOCK VALIDATION — NOT LLM RESULTS

These are executed outputs. Automatic tags are review candidates, not causal conclusions.
Gold appears ONLY in this evaluator-side report, never in a model request.

## v2-causal-hard / C2 / repetition 0

Status: succeeded; run: 542b1b4ff3224036b57b918c499f94cb

### Task

Trace a distribution-centre outage across power, cooling, temperature and storage protection. The backup barrier may interrupt the chain, so establish its state rather than assuming every upstream fault propagates.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "d3682347007c42bd8fbf885c2d8c9faf",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "ambient",
          "value": "hot",
          "evidence_ids": [
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "backup_power",
          "value": "failed",
          "evidence_ids": [
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "cooling",
          "value": "stopped",
          "evidence_ids": [
            "e_eadd621aa2a2"
          ]
        },
        {
          "subject": "grid",
          "value": "lost",
          "evidence_ids": [
            "e_52ac92ec2906"
          ]
        },
        {
          "subject": "rack_temperature",
          "value": "critical",
          "evidence_ids": [
            "e_834864ec7d1e"
          ]
        },
        {
          "subject": "staff_report",
          "value": "power_problem",
          "evidence_ids": [
            "e_373d0c1e7322"
          ]
        },
        {
          "subject": "storage",
          "value": "offline",
          "evidence_ids": [
            "e_fbf4535276d8"
          ]
        },
        {
          "subject": "thermal_shutdown",
          "value": "triggered",
          "evidence_ids": [
            "e_88b424f7d3b1"
          ]
        }
      ],
      "insights": [
        {
          "subject": "heat_removal",
          "value": "insufficient",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "mechanism",
          "value": "power_cooling_shutdown",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_834864ec7d1e",
            "e_88b424f7d3b1",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2",
            "e_fbf4535276d8"
          ]
        },
        {
          "subject": "power",
          "value": "unavailable",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "thermal_risk",
          "value": "realized",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_834864ec7d1e",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_373d0c1e7322",
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_373d0c1e7322",
      "e_52ac92ec2906",
      "e_80fa8d35888c",
      "e_834864ec7d1e",
      "e_88b424f7d3b1",
      "e_eadd621aa2a2",
      "e_f8dd2cdaa0f2",
      "e_fbf4535276d8"
    ],
    "created_at": "2026-09-28T14:58:12.885490Z"
  },
  {
    "id": "eb2506ee2be84b0a88812f7a29753085",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "ambient",
          "value": "hot",
          "evidence_ids": [
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "backup_power",
          "value": "failed",
          "evidence_ids": [
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "cooling",
          "value": "stopped",
          "evidence_ids": [
            "e_eadd621aa2a2"
          ]
        },
        {
          "subject": "grid",
          "value": "lost",
          "evidence_ids": [
            "e_52ac92ec2906"
          ]
        },
        {
          "subject": "rack_temperature",
          "value": "critical",
          "evidence_ids": [
            "e_834864ec7d1e"
          ]
        },
        {
          "subject": "staff_report",
          "value": "power_problem",
          "evidence_ids": [
            "e_373d0c1e7322"
          ]
        },
        {
          "subject": "storage",
          "value": "offline",
          "evidence_ids": [
            "e_fbf4535276d8"
          ]
        },
        {
          "subject": "thermal_shutdown",
          "value": "triggered",
          "evidence_ids": [
            "e_88b424f7d3b1"
          ]
        }
      ],
      "insights": [
        {
          "subject": "heat_removal",
          "value": "insufficient",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "mechanism",
          "value": "power_cooling_shutdown",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_834864ec7d1e",
            "e_88b424f7d3b1",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2",
            "e_fbf4535276d8"
          ]
        },
        {
          "subject": "power",
          "value": "unavailable",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "thermal_risk",
          "value": "realized",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_834864ec7d1e",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_373d0c1e7322",
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_373d0c1e7322",
      "e_52ac92ec2906",
      "e_80fa8d35888c",
      "e_834864ec7d1e",
      "e_88b424f7d3b1",
      "e_eadd621aa2a2",
      "e_f8dd2cdaa0f2",
      "e_fbf4535276d8"
    ],
    "created_at": "2026-09-28T14:58:12.904567Z"
  },
  {
    "id": "aee62abb47844c5baf1fc7f26bd3229b",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "ambient",
          "value": "hot",
          "evidence_ids": [
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "backup_power",
          "value": "failed",
          "evidence_ids": [
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "cooling",
          "value": "stopped",
          "evidence_ids": [
            "e_eadd621aa2a2"
          ]
        },
        {
          "subject": "grid",
          "value": "lost",
          "evidence_ids": [
            "e_52ac92ec2906"
          ]
        },
        {
          "subject": "rack_temperature",
          "value": "critical",
          "evidence_ids": [
            "e_834864ec7d1e"
          ]
        },
        {
          "subject": "staff_report",
          "value": "power_problem",
          "evidence_ids": [
            "e_373d0c1e7322"
          ]
        },
        {
          "subject": "storage",
          "value": "offline",
          "evidence_ids": [
            "e_fbf4535276d8"
          ]
        },
        {
          "subject": "thermal_shutdown",
          "value": "triggered",
          "evidence_ids": [
            "e_88b424f7d3b1"
          ]
        }
      ],
      "insights": [
        {
          "subject": "heat_removal",
          "value": "insufficient",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "mechanism",
          "value": "power_cooling_shutdown",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_834864ec7d1e",
            "e_88b424f7d3b1",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2",
            "e_fbf4535276d8"
          ]
        },
        {
          "subject": "power",
          "value": "unavailable",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "thermal_risk",
          "value": "realized",
          "evidence_ids": [
            "e_52ac92ec2906",
            "e_80fa8d35888c",
            "e_834864ec7d1e",
            "e_eadd621aa2a2",
            "e_f8dd2cdaa0f2"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_373d0c1e7322",
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_373d0c1e7322",
      "e_52ac92ec2906",
      "e_80fa8d35888c",
      "e_834864ec7d1e",
      "e_88b424f7d3b1",
      "e_eadd621aa2a2",
      "e_f8dd2cdaa0f2",
      "e_fbf4535276d8"
    ],
    "created_at": "2026-09-28T14:58:12.925098Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "ambient",
        "value": "hot",
        "evidence_ids": [
          "e_f8dd2cdaa0f2"
        ]
      },
      {
        "subject": "backup_power",
        "value": "failed",
        "evidence_ids": [
          "e_80fa8d35888c"
        ]
      },
      {
        "subject": "cooling",
        "value": "stopped",
        "evidence_ids": [
          "e_eadd621aa2a2"
        ]
      },
      {
        "subject": "grid",
        "value": "lost",
        "evidence_ids": [
          "e_52ac92ec2906"
        ]
      },
      {
        "subject": "rack_temperature",
        "value": "critical",
        "evidence_ids": [
          "e_834864ec7d1e"
        ]
      },
      {
        "subject": "staff_report",
        "value": "power_problem",
        "evidence_ids": [
          "e_373d0c1e7322"
        ]
      },
      {
        "subject": "storage",
        "value": "offline",
        "evidence_ids": [
          "e_fbf4535276d8"
        ]
      },
      {
        "subject": "thermal_shutdown",
        "value": "triggered",
        "evidence_ids": [
          "e_88b424f7d3b1"
        ]
      }
    ],
    "insights": [
      {
        "subject": "heat_removal",
        "value": "insufficient",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      },
      {
        "subject": "mechanism",
        "value": "power_cooling_shutdown",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ]
      },
      {
        "subject": "power",
        "value": "unavailable",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c"
        ]
      },
      {
        "subject": "thermal_risk",
        "value": "realized",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_373d0c1e7322",
        "e_52ac92ec2906",
        "e_80fa8d35888c",
        "e_834864ec7d1e",
        "e_88b424f7d3b1",
        "e_eadd621aa2a2",
        "e_f8dd2cdaa0f2",
        "e_fbf4535276d8"
      ],
      "unknowns": []
    },
    "conclusion": "restore_power_then_cooling_then_storage",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-causal-hard",
  "relevant_evidence_ids": [
    "e_52ac92ec2906",
    "e_80fa8d35888c",
    "e_eadd621aa2a2",
    "e_f8dd2cdaa0f2",
    "e_834864ec7d1e",
    "e_88b424f7d3b1",
    "e_fbf4535276d8"
  ],
  "distractor_ids": [
    "e_10d72e1812e3",
    "e_b27286da986f",
    "e_54f7b7a8a710"
  ],
  "claims": [
    {
      "subject": "grid",
      "value": "lost",
      "supporting_sets": [
        [
          "e_52ac92ec2906"
        ]
      ]
    },
    {
      "subject": "backup_power",
      "value": "failed",
      "supporting_sets": [
        [
          "e_80fa8d35888c"
        ]
      ]
    },
    {
      "subject": "cooling",
      "value": "stopped",
      "supporting_sets": [
        [
          "e_eadd621aa2a2"
        ]
      ]
    },
    {
      "subject": "ambient",
      "value": "hot",
      "supporting_sets": [
        [
          "e_f8dd2cdaa0f2"
        ]
      ]
    },
    {
      "subject": "rack_temperature",
      "value": "critical",
      "supporting_sets": [
        [
          "e_834864ec7d1e"
        ]
      ]
    },
    {
      "subject": "thermal_shutdown",
      "value": "triggered",
      "supporting_sets": [
        [
          "e_88b424f7d3b1"
        ]
      ]
    },
    {
      "subject": "storage",
      "value": "offline",
      "supporting_sets": [
        [
          "e_fbf4535276d8"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "mechanism",
      "value": "power_cooling_shutdown",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "heat_removal",
      "value": "insufficient",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      ]
    },
    {
      "subject": "power",
      "value": "unavailable",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c"
        ]
      ]
    },
    {
      "subject": "thermal_risk",
      "value": "realized",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      ]
    }
  ],
  "expected_conclusion": "restore_power_then_cooling_then_storage",
  "constraints": [
    "grid",
    "backup_power",
    "cooling",
    "ambient",
    "rack_temperature",
    "thermal_shutdown",
    "storage"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_f6fb148902ad59322613",
  "benchmark_version": "2.0.0",
  "optional_claims": [
    {
      "subject": "staff_report",
      "value": "power_problem",
      "supporting_sets": [
        [
          "e_373d0c1e7322"
        ]
      ]
    }
  ],
  "weak_evidence_ids": [
    "e_373d0c1e7322"
  ],
  "evidence_importance": {
    "e_52ac92ec2906": 2,
    "e_80fa8d35888c": 2,
    "e_eadd621aa2a2": 2,
    "e_f8dd2cdaa0f2": 2,
    "e_834864ec7d1e": 2,
    "e_88b424f7d3b1": 2,
    "e_fbf4535276d8": 2
  },
  "decision_supporting_sets": [
    [
      "e_52ac92ec2906",
      "e_80fa8d35888c",
      "e_834864ec7d1e",
      "e_88b424f7d3b1",
      "e_eadd621aa2a2",
      "e_f8dd2cdaa0f2",
      "e_fbf4535276d8"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 1,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.0,
    "collective_claim_coverage_gain": 0.0,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.0,
    "marginal_final_support_loss_max": 0.0,
    "evidence_unique": 0.0,
    "evidence_redundancy": 0.6666666666666666,
    "evidence_jaccard": 1.0,
    "claim_unique": 0.0,
    "claim_redundancy": 0.6666666666666666,
    "claim_jaccard": 1.0,
    "insight_unique": 0.0,
    "insight_redundancy": 0.6666666666666666,
    "insight_jaccard": 1.0,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 22,
    "input_tokens": 6825,
    "output_tokens": 1460,
    "total_tokens": 8285,
    "model_calls": 4,
    "latency_ms": 91.98174998164177,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "analytical",
      "worker_1": "skeptical",
      "worker_2": "systems"
    },
    "partitions": {
      "worker_0": [
        "e_373d0c1e7322",
        "e_54f7b7a8a710",
        "e_80fa8d35888c",
        "e_fbf4535276d8"
      ],
      "worker_1": [
        "e_834864ec7d1e",
        "e_eadd621aa2a2",
        "e_10d72e1812e3"
      ],
      "worker_2": [
        "e_f8dd2cdaa0f2",
        "e_b27286da986f",
        "e_88b424f7d3b1",
        "e_52ac92ec2906"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "ambient=hot",
        "backup_power=failed",
        "cooling=stopped",
        "grid=lost",
        "rack_temperature=critical",
        "storage=offline",
        "thermal_shutdown=triggered"
      ],
      [
        "ambient=hot",
        "backup_power=failed",
        "cooling=stopped",
        "grid=lost",
        "rack_temperature=critical",
        "storage=offline",
        "thermal_shutdown=triggered"
      ],
      [
        "ambient=hot",
        "backup_power=failed",
        "cooling=stopped",
        "grid=lost",
        "rack_temperature=critical",
        "storage=offline",
        "thermal_shutdown=triggered"
      ]
    ],
    "worker_evidence": [
      [
        "e_52ac92ec2906",
        "e_80fa8d35888c",
        "e_834864ec7d1e",
        "e_88b424f7d3b1",
        "e_eadd621aa2a2",
        "e_f8dd2cdaa0f2",
        "e_fbf4535276d8"
      ],
      [
        "e_52ac92ec2906",
        "e_80fa8d35888c",
        "e_834864ec7d1e",
        "e_88b424f7d3b1",
        "e_eadd621aa2a2",
        "e_f8dd2cdaa0f2",
        "e_fbf4535276d8"
      ],
      [
        "e_52ac92ec2906",
        "e_80fa8d35888c",
        "e_834864ec7d1e",
        "e_88b424f7d3b1",
        "e_eadd621aa2a2",
        "e_f8dd2cdaa0f2",
        "e_fbf4535276d8"
      ]
    ],
    "worker_required_insights": [
      [
        "mechanism=power_cooling_shutdown"
      ],
      [
        "mechanism=power_cooling_shutdown"
      ],
      [
        "mechanism=power_cooling_shutdown"
      ]
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "restore_power_then_cooling_then_storage",
    "actual_conclusion": "restore_power_then_cooling_then_storage"
  }
}
```

Candidate patterns: ['all agents repeat same evidence']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-causal-hard / C3 / repetition 0

Status: succeeded; run: 2e3ab6ec366944d9950450b12f3bfd05

### Task

Trace a distribution-centre outage across power, cooling, temperature and storage protection. The backup barrier may interrupt the chain, so establish its state rather than assuming every upstream fault propagates.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "6d54f48844f24c0795a441581983ca85",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "backup_power",
          "value": "failed",
          "evidence_ids": [
            "e_80fa8d35888c"
          ]
        },
        {
          "subject": "staff_report",
          "value": "power_problem",
          "evidence_ids": [
            "e_373d0c1e7322"
          ]
        },
        {
          "subject": "storage",
          "value": "offline",
          "evidence_ids": [
            "e_fbf4535276d8"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_373d0c1e7322",
          "e_80fa8d35888c",
          "e_fbf4535276d8"
        ],
        "unknowns": [
          "grid",
          "cooling",
          "ambient",
          "rack_temperature",
          "thermal_shutdown"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_373d0c1e7322",
      "e_80fa8d35888c",
      "e_fbf4535276d8"
    ],
    "created_at": "2026-09-28T14:58:12.790864Z"
  },
  {
    "id": "e921f10edd6f4ac4b04cb3a6b851e56b",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "cooling",
          "value": "stopped",
          "evidence_ids": [
            "e_eadd621aa2a2"
          ]
        },
        {
          "subject": "rack_temperature",
          "value": "critical",
          "evidence_ids": [
            "e_834864ec7d1e"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_834864ec7d1e",
          "e_eadd621aa2a2"
        ],
        "unknowns": [
          "grid",
          "backup_power",
          "ambient",
          "thermal_shutdown",
          "storage",
          "staff_report"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_834864ec7d1e",
      "e_eadd621aa2a2"
    ],
    "created_at": "2026-09-28T14:58:12.809261Z"
  },
  {
    "id": "86cfd2892e6945b9be848588c287ce18",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "ambient",
          "value": "hot",
          "evidence_ids": [
            "e_f8dd2cdaa0f2"
          ]
        },
        {
          "subject": "grid",
          "value": "lost",
          "evidence_ids": [
            "e_52ac92ec2906"
          ]
        },
        {
          "subject": "thermal_shutdown",
          "value": "triggered",
          "evidence_ids": [
            "e_88b424f7d3b1"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_88b424f7d3b1",
          "e_f8dd2cdaa0f2"
        ],
        "unknowns": [
          "backup_power",
          "cooling",
          "rack_temperature",
          "storage",
          "staff_report"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_52ac92ec2906",
      "e_88b424f7d3b1",
      "e_f8dd2cdaa0f2"
    ],
    "created_at": "2026-09-28T14:58:12.829931Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "ambient",
        "value": "hot",
        "evidence_ids": [
          "e_f8dd2cdaa0f2"
        ]
      },
      {
        "subject": "backup_power",
        "value": "failed",
        "evidence_ids": [
          "e_80fa8d35888c"
        ]
      },
      {
        "subject": "cooling",
        "value": "stopped",
        "evidence_ids": [
          "e_eadd621aa2a2"
        ]
      },
      {
        "subject": "grid",
        "value": "lost",
        "evidence_ids": [
          "e_52ac92ec2906"
        ]
      },
      {
        "subject": "rack_temperature",
        "value": "critical",
        "evidence_ids": [
          "e_834864ec7d1e"
        ]
      },
      {
        "subject": "staff_report",
        "value": "power_problem",
        "evidence_ids": [
          "e_373d0c1e7322"
        ]
      },
      {
        "subject": "storage",
        "value": "offline",
        "evidence_ids": [
          "e_fbf4535276d8"
        ]
      },
      {
        "subject": "thermal_shutdown",
        "value": "triggered",
        "evidence_ids": [
          "e_88b424f7d3b1"
        ]
      }
    ],
    "insights": [
      {
        "subject": "heat_removal",
        "value": "insufficient",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      },
      {
        "subject": "mechanism",
        "value": "power_cooling_shutdown",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ]
      },
      {
        "subject": "power",
        "value": "unavailable",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c"
        ]
      },
      {
        "subject": "thermal_risk",
        "value": "realized",
        "evidence_ids": [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_373d0c1e7322",
        "e_52ac92ec2906",
        "e_80fa8d35888c",
        "e_834864ec7d1e",
        "e_88b424f7d3b1",
        "e_eadd621aa2a2",
        "e_f8dd2cdaa0f2",
        "e_fbf4535276d8"
      ],
      "unknowns": []
    },
    "conclusion": "restore_power_then_cooling_then_storage",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-causal-hard",
  "relevant_evidence_ids": [
    "e_52ac92ec2906",
    "e_80fa8d35888c",
    "e_eadd621aa2a2",
    "e_f8dd2cdaa0f2",
    "e_834864ec7d1e",
    "e_88b424f7d3b1",
    "e_fbf4535276d8"
  ],
  "distractor_ids": [
    "e_10d72e1812e3",
    "e_b27286da986f",
    "e_54f7b7a8a710"
  ],
  "claims": [
    {
      "subject": "grid",
      "value": "lost",
      "supporting_sets": [
        [
          "e_52ac92ec2906"
        ]
      ]
    },
    {
      "subject": "backup_power",
      "value": "failed",
      "supporting_sets": [
        [
          "e_80fa8d35888c"
        ]
      ]
    },
    {
      "subject": "cooling",
      "value": "stopped",
      "supporting_sets": [
        [
          "e_eadd621aa2a2"
        ]
      ]
    },
    {
      "subject": "ambient",
      "value": "hot",
      "supporting_sets": [
        [
          "e_f8dd2cdaa0f2"
        ]
      ]
    },
    {
      "subject": "rack_temperature",
      "value": "critical",
      "supporting_sets": [
        [
          "e_834864ec7d1e"
        ]
      ]
    },
    {
      "subject": "thermal_shutdown",
      "value": "triggered",
      "supporting_sets": [
        [
          "e_88b424f7d3b1"
        ]
      ]
    },
    {
      "subject": "storage",
      "value": "offline",
      "supporting_sets": [
        [
          "e_fbf4535276d8"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "mechanism",
      "value": "power_cooling_shutdown",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_88b424f7d3b1",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2",
          "e_fbf4535276d8"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "heat_removal",
      "value": "insufficient",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      ]
    },
    {
      "subject": "power",
      "value": "unavailable",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c"
        ]
      ]
    },
    {
      "subject": "thermal_risk",
      "value": "realized",
      "supporting_sets": [
        [
          "e_52ac92ec2906",
          "e_80fa8d35888c",
          "e_834864ec7d1e",
          "e_eadd621aa2a2",
          "e_f8dd2cdaa0f2"
        ]
      ]
    }
  ],
  "expected_conclusion": "restore_power_then_cooling_then_storage",
  "constraints": [
    "grid",
    "backup_power",
    "cooling",
    "ambient",
    "rack_temperature",
    "thermal_shutdown",
    "storage"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_f6fb148902ad59322613",
  "benchmark_version": "2.0.0",
  "optional_claims": [
    {
      "subject": "staff_report",
      "value": "power_problem",
      "supporting_sets": [
        [
          "e_373d0c1e7322"
        ]
      ]
    }
  ],
  "weak_evidence_ids": [
    "e_373d0c1e7322"
  ],
  "evidence_importance": {
    "e_52ac92ec2906": 2,
    "e_80fa8d35888c": 2,
    "e_eadd621aa2a2": 2,
    "e_f8dd2cdaa0f2": 2,
    "e_834864ec7d1e": 2,
    "e_88b424f7d3b1": 2,
    "e_fbf4535276d8": 2
  },
  "decision_supporting_sets": [
    [
      "e_52ac92ec2906",
      "e_80fa8d35888c",
      "e_834864ec7d1e",
      "e_88b424f7d3b1",
      "e_eadd621aa2a2",
      "e_f8dd2cdaa0f2",
      "e_fbf4535276d8"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 0,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.5714285714285714,
    "collective_claim_coverage_gain": 0.5714285714285714,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.3333333333333333,
    "marginal_final_support_loss_max": 0.4285714285714286,
    "evidence_unique": 1.0,
    "evidence_redundancy": 0.0,
    "evidence_jaccard": 0.0,
    "claim_unique": 1.0,
    "claim_redundancy": 0.0,
    "claim_jaccard": 0.0,
    "insight_unique": 0,
    "insight_redundancy": 0,
    "insight_jaccard": null,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 0,
    "input_tokens": 5123,
    "output_tokens": 709,
    "total_tokens": 5832,
    "model_calls": 4,
    "latency_ms": 90.54920892231166,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "neutral",
      "worker_1": "neutral",
      "worker_2": "neutral"
    },
    "partitions": {
      "worker_0": [
        "e_373d0c1e7322",
        "e_54f7b7a8a710",
        "e_80fa8d35888c",
        "e_fbf4535276d8"
      ],
      "worker_1": [
        "e_834864ec7d1e",
        "e_eadd621aa2a2",
        "e_10d72e1812e3"
      ],
      "worker_2": [
        "e_f8dd2cdaa0f2",
        "e_b27286da986f",
        "e_88b424f7d3b1",
        "e_52ac92ec2906"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "backup_power=failed",
        "storage=offline"
      ],
      [
        "cooling=stopped",
        "rack_temperature=critical"
      ],
      [
        "ambient=hot",
        "grid=lost",
        "thermal_shutdown=triggered"
      ]
    ],
    "worker_evidence": [
      [
        "e_80fa8d35888c",
        "e_fbf4535276d8"
      ],
      [
        "e_834864ec7d1e",
        "e_eadd621aa2a2"
      ],
      [
        "e_52ac92ec2906",
        "e_88b424f7d3b1",
        "e_f8dd2cdaa0f2"
      ]
    ],
    "worker_required_insights": [
      [],
      [],
      []
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 0.7142857142857143,
        "drop": 0.2857142857142857
      },
      {
        "supported_final_coverage_without": 0.7142857142857143,
        "drop": 0.2857142857142857
      },
      {
        "supported_final_coverage_without": 0.5714285714285714,
        "drop": 0.4285714285714286
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "restore_power_then_cooling_then_storage",
    "actual_conclusion": "restore_power_then_cooling_then_storage"
  }
}
```

Candidate patterns: ['useful unique contribution']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-constraints-medium / C2 / repetition 0

Status: succeeded; run: 92e74179356d4318b8112a59f40cca35

### Task

Select a storage upgrade subject to migration compatibility and a strict spending ceiling. A faster but incompatible or over-budget option cannot be selected.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "c76f62fc07654ebf8dd4ee36f16ee7a9",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "balanced_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_b2512895670a"
          ]
        },
        {
          "subject": "balanced_drive_cost",
          "value": "within_budget",
          "evidence_ids": [
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_48356f221843"
          ]
        },
        {
          "subject": "fast_drive_cost",
          "value": "over_budget",
          "evidence_ids": [
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "migration_slot",
          "value": "available",
          "evidence_ids": [
            "e_96d09490c7d9"
          ]
        },
        {
          "subject": "minimum_throughput",
          "value": "balanced_sufficient",
          "evidence_ids": [
            "e_0929d9514324"
          ]
        }
      ],
      "insights": [
        {
          "subject": "balanced",
          "value": "feasible",
          "evidence_ids": [
            "e_0929d9514324",
            "e_b2512895670a",
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast",
          "value": "excluded",
          "evidence_ids": [
            "e_48356f221843",
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "selection",
          "value": "balanced",
          "evidence_ids": [
            "e_0929d9514324",
            "e_48356f221843",
            "e_b2512895670a",
            "e_c446885a3427",
            "e_d746b153a9c4"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_0929d9514324",
          "e_48356f221843",
          "e_96d09490c7d9",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_0929d9514324",
      "e_48356f221843",
      "e_96d09490c7d9",
      "e_b2512895670a",
      "e_c446885a3427",
      "e_d746b153a9c4"
    ],
    "created_at": "2026-09-28T14:58:12.319759Z"
  },
  {
    "id": "4471af3fbd1f48fea26cc6c162cccf1d",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "balanced_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_b2512895670a"
          ]
        },
        {
          "subject": "balanced_drive_cost",
          "value": "within_budget",
          "evidence_ids": [
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_48356f221843"
          ]
        },
        {
          "subject": "fast_drive_cost",
          "value": "over_budget",
          "evidence_ids": [
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "migration_slot",
          "value": "available",
          "evidence_ids": [
            "e_96d09490c7d9"
          ]
        },
        {
          "subject": "minimum_throughput",
          "value": "balanced_sufficient",
          "evidence_ids": [
            "e_0929d9514324"
          ]
        }
      ],
      "insights": [
        {
          "subject": "balanced",
          "value": "feasible",
          "evidence_ids": [
            "e_0929d9514324",
            "e_b2512895670a",
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast",
          "value": "excluded",
          "evidence_ids": [
            "e_48356f221843",
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "selection",
          "value": "balanced",
          "evidence_ids": [
            "e_0929d9514324",
            "e_48356f221843",
            "e_b2512895670a",
            "e_c446885a3427",
            "e_d746b153a9c4"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_0929d9514324",
          "e_48356f221843",
          "e_96d09490c7d9",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_0929d9514324",
      "e_48356f221843",
      "e_96d09490c7d9",
      "e_b2512895670a",
      "e_c446885a3427",
      "e_d746b153a9c4"
    ],
    "created_at": "2026-09-28T14:58:12.338290Z"
  },
  {
    "id": "6b4ad92af0f14d4492601e804ed4f955",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "balanced_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_b2512895670a"
          ]
        },
        {
          "subject": "balanced_drive_cost",
          "value": "within_budget",
          "evidence_ids": [
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_48356f221843"
          ]
        },
        {
          "subject": "fast_drive_cost",
          "value": "over_budget",
          "evidence_ids": [
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "migration_slot",
          "value": "available",
          "evidence_ids": [
            "e_96d09490c7d9"
          ]
        },
        {
          "subject": "minimum_throughput",
          "value": "balanced_sufficient",
          "evidence_ids": [
            "e_0929d9514324"
          ]
        }
      ],
      "insights": [
        {
          "subject": "balanced",
          "value": "feasible",
          "evidence_ids": [
            "e_0929d9514324",
            "e_b2512895670a",
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast",
          "value": "excluded",
          "evidence_ids": [
            "e_48356f221843",
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "selection",
          "value": "balanced",
          "evidence_ids": [
            "e_0929d9514324",
            "e_48356f221843",
            "e_b2512895670a",
            "e_c446885a3427",
            "e_d746b153a9c4"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_0929d9514324",
          "e_48356f221843",
          "e_96d09490c7d9",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_0929d9514324",
      "e_48356f221843",
      "e_96d09490c7d9",
      "e_b2512895670a",
      "e_c446885a3427",
      "e_d746b153a9c4"
    ],
    "created_at": "2026-09-28T14:58:12.358954Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "balanced_compatibility",
        "value": "yes",
        "evidence_ids": [
          "e_b2512895670a"
        ]
      },
      {
        "subject": "balanced_drive_cost",
        "value": "within_budget",
        "evidence_ids": [
          "e_c446885a3427"
        ]
      },
      {
        "subject": "fast_compatibility",
        "value": "yes",
        "evidence_ids": [
          "e_48356f221843"
        ]
      },
      {
        "subject": "fast_drive_cost",
        "value": "over_budget",
        "evidence_ids": [
          "e_d746b153a9c4"
        ]
      },
      {
        "subject": "migration_slot",
        "value": "available",
        "evidence_ids": [
          "e_96d09490c7d9"
        ]
      },
      {
        "subject": "minimum_throughput",
        "value": "balanced_sufficient",
        "evidence_ids": [
          "e_0929d9514324"
        ]
      }
    ],
    "insights": [
      {
        "subject": "balanced",
        "value": "feasible",
        "evidence_ids": [
          "e_0929d9514324",
          "e_b2512895670a",
          "e_c446885a3427"
        ]
      },
      {
        "subject": "fast",
        "value": "excluded",
        "evidence_ids": [
          "e_48356f221843",
          "e_d746b153a9c4"
        ]
      },
      {
        "subject": "selection",
        "value": "balanced",
        "evidence_ids": [
          "e_0929d9514324",
          "e_48356f221843",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_0929d9514324",
        "e_48356f221843",
        "e_96d09490c7d9",
        "e_b2512895670a",
        "e_c446885a3427",
        "e_d746b153a9c4"
      ],
      "unknowns": []
    },
    "conclusion": "install_balanced",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-constraints-medium",
  "relevant_evidence_ids": [
    "e_d746b153a9c4",
    "e_c446885a3427",
    "e_48356f221843",
    "e_b2512895670a",
    "e_0929d9514324",
    "e_96d09490c7d9"
  ],
  "distractor_ids": [
    "e_71d87df76c2b",
    "e_7595e6f7ee49",
    "e_eb4c061a08fd"
  ],
  "claims": [
    {
      "subject": "fast_drive_cost",
      "value": "over_budget",
      "supporting_sets": [
        [
          "e_d746b153a9c4"
        ]
      ]
    },
    {
      "subject": "balanced_drive_cost",
      "value": "within_budget",
      "supporting_sets": [
        [
          "e_c446885a3427"
        ]
      ]
    },
    {
      "subject": "fast_compatibility",
      "value": "yes",
      "supporting_sets": [
        [
          "e_48356f221843"
        ]
      ]
    },
    {
      "subject": "balanced_compatibility",
      "value": "yes",
      "supporting_sets": [
        [
          "e_b2512895670a"
        ]
      ]
    },
    {
      "subject": "minimum_throughput",
      "value": "balanced_sufficient",
      "supporting_sets": [
        [
          "e_0929d9514324"
        ]
      ]
    },
    {
      "subject": "migration_slot",
      "value": "available",
      "supporting_sets": [
        [
          "e_96d09490c7d9"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "selection",
      "value": "balanced",
      "supporting_sets": [
        [
          "e_0929d9514324",
          "e_48356f221843",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "balanced",
      "value": "feasible",
      "supporting_sets": [
        [
          "e_0929d9514324",
          "e_b2512895670a",
          "e_c446885a3427"
        ]
      ]
    },
    {
      "subject": "fast",
      "value": "excluded",
      "supporting_sets": [
        [
          "e_48356f221843",
          "e_d746b153a9c4"
        ]
      ]
    }
  ],
  "expected_conclusion": "install_balanced",
  "constraints": [
    "fast_drive_cost",
    "balanced_drive_cost",
    "fast_compatibility",
    "balanced_compatibility",
    "minimum_throughput",
    "migration_slot"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_30e3145f43a9520a3e98",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_d746b153a9c4": 2,
    "e_c446885a3427": 2,
    "e_48356f221843": 2,
    "e_b2512895670a": 2,
    "e_0929d9514324": 2,
    "e_96d09490c7d9": 2
  },
  "decision_supporting_sets": [
    [
      "e_0929d9514324",
      "e_48356f221843",
      "e_96d09490c7d9",
      "e_b2512895670a",
      "e_c446885a3427",
      "e_d746b153a9c4"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 1,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.0,
    "collective_claim_coverage_gain": 0.0,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.0,
    "marginal_final_support_loss_max": 0.0,
    "evidence_unique": 0.0,
    "evidence_redundancy": 0.6666666666666666,
    "evidence_jaccard": 1.0,
    "claim_unique": 0.0,
    "claim_redundancy": 0.6666666666666666,
    "claim_jaccard": 1.0,
    "insight_unique": 0.0,
    "insight_redundancy": 0.6666666666666666,
    "insight_jaccard": 1.0,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 18,
    "input_tokens": 6186,
    "output_tokens": 1102,
    "total_tokens": 7288,
    "model_calls": 4,
    "latency_ms": 91.03750006761402,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "systems",
      "worker_1": "skeptical",
      "worker_2": "analytical"
    },
    "partitions": {
      "worker_0": [
        "e_d746b153a9c4",
        "e_96d09490c7d9",
        "e_eb4c061a08fd"
      ],
      "worker_1": [
        "e_c446885a3427",
        "e_48356f221843",
        "e_71d87df76c2b"
      ],
      "worker_2": [
        "e_0929d9514324",
        "e_b2512895670a",
        "e_7595e6f7ee49"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "balanced_compatibility=yes",
        "balanced_drive_cost=within_budget",
        "fast_compatibility=yes",
        "fast_drive_cost=over_budget",
        "migration_slot=available",
        "minimum_throughput=balanced_sufficient"
      ],
      [
        "balanced_compatibility=yes",
        "balanced_drive_cost=within_budget",
        "fast_compatibility=yes",
        "fast_drive_cost=over_budget",
        "migration_slot=available",
        "minimum_throughput=balanced_sufficient"
      ],
      [
        "balanced_compatibility=yes",
        "balanced_drive_cost=within_budget",
        "fast_compatibility=yes",
        "fast_drive_cost=over_budget",
        "migration_slot=available",
        "minimum_throughput=balanced_sufficient"
      ]
    ],
    "worker_evidence": [
      [
        "e_0929d9514324",
        "e_48356f221843",
        "e_96d09490c7d9",
        "e_b2512895670a",
        "e_c446885a3427",
        "e_d746b153a9c4"
      ],
      [
        "e_0929d9514324",
        "e_48356f221843",
        "e_96d09490c7d9",
        "e_b2512895670a",
        "e_c446885a3427",
        "e_d746b153a9c4"
      ],
      [
        "e_0929d9514324",
        "e_48356f221843",
        "e_96d09490c7d9",
        "e_b2512895670a",
        "e_c446885a3427",
        "e_d746b153a9c4"
      ]
    ],
    "worker_required_insights": [
      [
        "selection=balanced"
      ],
      [
        "selection=balanced"
      ],
      [
        "selection=balanced"
      ]
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "install_balanced",
    "actual_conclusion": "install_balanced"
  }
}
```

Candidate patterns: ['all agents repeat same evidence']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-constraints-medium / C3 / repetition 0

Status: succeeded; run: 21875041f93e4d3a921d1adf77131e41

### Task

Select a storage upgrade subject to migration compatibility and a strict spending ceiling. A faster but incompatible or over-budget option cannot be selected.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "97c55d8a17b54f8bb94206c58497818c",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "fast_drive_cost",
          "value": "over_budget",
          "evidence_ids": [
            "e_d746b153a9c4"
          ]
        },
        {
          "subject": "migration_slot",
          "value": "available",
          "evidence_ids": [
            "e_96d09490c7d9"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_96d09490c7d9",
          "e_d746b153a9c4"
        ],
        "unknowns": [
          "balanced_drive_cost",
          "fast_compatibility",
          "balanced_compatibility",
          "minimum_throughput"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_96d09490c7d9",
      "e_d746b153a9c4"
    ],
    "created_at": "2026-09-28T14:58:12.226266Z"
  },
  {
    "id": "21d69399075f4ce0b277637b452379a4",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "balanced_drive_cost",
          "value": "within_budget",
          "evidence_ids": [
            "e_c446885a3427"
          ]
        },
        {
          "subject": "fast_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_48356f221843"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_48356f221843",
          "e_c446885a3427"
        ],
        "unknowns": [
          "fast_drive_cost",
          "balanced_compatibility",
          "minimum_throughput",
          "migration_slot"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_48356f221843",
      "e_c446885a3427"
    ],
    "created_at": "2026-09-28T14:58:12.244463Z"
  },
  {
    "id": "dddbb0d38fd0447fba109f767a5928e5",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "balanced_compatibility",
          "value": "yes",
          "evidence_ids": [
            "e_b2512895670a"
          ]
        },
        {
          "subject": "minimum_throughput",
          "value": "balanced_sufficient",
          "evidence_ids": [
            "e_0929d9514324"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_0929d9514324",
          "e_b2512895670a"
        ],
        "unknowns": [
          "fast_drive_cost",
          "balanced_drive_cost",
          "fast_compatibility",
          "migration_slot"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_0929d9514324",
      "e_b2512895670a"
    ],
    "created_at": "2026-09-28T14:58:12.264746Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "balanced_compatibility",
        "value": "yes",
        "evidence_ids": [
          "e_b2512895670a"
        ]
      },
      {
        "subject": "balanced_drive_cost",
        "value": "within_budget",
        "evidence_ids": [
          "e_c446885a3427"
        ]
      },
      {
        "subject": "fast_compatibility",
        "value": "yes",
        "evidence_ids": [
          "e_48356f221843"
        ]
      },
      {
        "subject": "fast_drive_cost",
        "value": "over_budget",
        "evidence_ids": [
          "e_d746b153a9c4"
        ]
      },
      {
        "subject": "migration_slot",
        "value": "available",
        "evidence_ids": [
          "e_96d09490c7d9"
        ]
      },
      {
        "subject": "minimum_throughput",
        "value": "balanced_sufficient",
        "evidence_ids": [
          "e_0929d9514324"
        ]
      }
    ],
    "insights": [
      {
        "subject": "balanced",
        "value": "feasible",
        "evidence_ids": [
          "e_0929d9514324",
          "e_b2512895670a",
          "e_c446885a3427"
        ]
      },
      {
        "subject": "fast",
        "value": "excluded",
        "evidence_ids": [
          "e_48356f221843",
          "e_d746b153a9c4"
        ]
      },
      {
        "subject": "selection",
        "value": "balanced",
        "evidence_ids": [
          "e_0929d9514324",
          "e_48356f221843",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_0929d9514324",
        "e_48356f221843",
        "e_96d09490c7d9",
        "e_b2512895670a",
        "e_c446885a3427",
        "e_d746b153a9c4"
      ],
      "unknowns": []
    },
    "conclusion": "install_balanced",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-constraints-medium",
  "relevant_evidence_ids": [
    "e_d746b153a9c4",
    "e_c446885a3427",
    "e_48356f221843",
    "e_b2512895670a",
    "e_0929d9514324",
    "e_96d09490c7d9"
  ],
  "distractor_ids": [
    "e_71d87df76c2b",
    "e_7595e6f7ee49",
    "e_eb4c061a08fd"
  ],
  "claims": [
    {
      "subject": "fast_drive_cost",
      "value": "over_budget",
      "supporting_sets": [
        [
          "e_d746b153a9c4"
        ]
      ]
    },
    {
      "subject": "balanced_drive_cost",
      "value": "within_budget",
      "supporting_sets": [
        [
          "e_c446885a3427"
        ]
      ]
    },
    {
      "subject": "fast_compatibility",
      "value": "yes",
      "supporting_sets": [
        [
          "e_48356f221843"
        ]
      ]
    },
    {
      "subject": "balanced_compatibility",
      "value": "yes",
      "supporting_sets": [
        [
          "e_b2512895670a"
        ]
      ]
    },
    {
      "subject": "minimum_throughput",
      "value": "balanced_sufficient",
      "supporting_sets": [
        [
          "e_0929d9514324"
        ]
      ]
    },
    {
      "subject": "migration_slot",
      "value": "available",
      "supporting_sets": [
        [
          "e_96d09490c7d9"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "selection",
      "value": "balanced",
      "supporting_sets": [
        [
          "e_0929d9514324",
          "e_48356f221843",
          "e_b2512895670a",
          "e_c446885a3427",
          "e_d746b153a9c4"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "balanced",
      "value": "feasible",
      "supporting_sets": [
        [
          "e_0929d9514324",
          "e_b2512895670a",
          "e_c446885a3427"
        ]
      ]
    },
    {
      "subject": "fast",
      "value": "excluded",
      "supporting_sets": [
        [
          "e_48356f221843",
          "e_d746b153a9c4"
        ]
      ]
    }
  ],
  "expected_conclusion": "install_balanced",
  "constraints": [
    "fast_drive_cost",
    "balanced_drive_cost",
    "fast_compatibility",
    "balanced_compatibility",
    "minimum_throughput",
    "migration_slot"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_30e3145f43a9520a3e98",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_d746b153a9c4": 2,
    "e_c446885a3427": 2,
    "e_48356f221843": 2,
    "e_b2512895670a": 2,
    "e_0929d9514324": 2,
    "e_96d09490c7d9": 2
  },
  "decision_supporting_sets": [
    [
      "e_0929d9514324",
      "e_48356f221843",
      "e_96d09490c7d9",
      "e_b2512895670a",
      "e_c446885a3427",
      "e_d746b153a9c4"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 0,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.6666666666666666,
    "collective_claim_coverage_gain": 0.6666666666666666,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.33333333333333337,
    "marginal_final_support_loss_max": 0.33333333333333337,
    "evidence_unique": 1.0,
    "evidence_redundancy": 0.0,
    "evidence_jaccard": 0.0,
    "claim_unique": 1.0,
    "claim_redundancy": 0.0,
    "claim_jaccard": 0.0,
    "insight_unique": 0,
    "insight_redundancy": 0,
    "insight_jaccard": null,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 0,
    "input_tokens": 4872,
    "output_tokens": 592,
    "total_tokens": 5464,
    "model_calls": 4,
    "latency_ms": 90.06949991453439,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "neutral",
      "worker_1": "neutral",
      "worker_2": "neutral"
    },
    "partitions": {
      "worker_0": [
        "e_d746b153a9c4",
        "e_96d09490c7d9",
        "e_eb4c061a08fd"
      ],
      "worker_1": [
        "e_c446885a3427",
        "e_48356f221843",
        "e_71d87df76c2b"
      ],
      "worker_2": [
        "e_0929d9514324",
        "e_b2512895670a",
        "e_7595e6f7ee49"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "fast_drive_cost=over_budget",
        "migration_slot=available"
      ],
      [
        "balanced_drive_cost=within_budget",
        "fast_compatibility=yes"
      ],
      [
        "balanced_compatibility=yes",
        "minimum_throughput=balanced_sufficient"
      ]
    ],
    "worker_evidence": [
      [
        "e_96d09490c7d9",
        "e_d746b153a9c4"
      ],
      [
        "e_48356f221843",
        "e_c446885a3427"
      ],
      [
        "e_0929d9514324",
        "e_b2512895670a"
      ]
    ],
    "worker_required_insights": [
      [],
      [],
      []
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 0.6666666666666666,
        "drop": 0.33333333333333337
      },
      {
        "supported_final_coverage_without": 0.6666666666666666,
        "drop": 0.33333333333333337
      },
      {
        "supported_final_coverage_without": 0.6666666666666666,
        "drop": 0.33333333333333337
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "install_balanced",
    "actual_conclusion": "install_balanced"
  }
}
```

Candidate patterns: ['useful unique contribution']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-contradiction-hard / C2 / repetition 0

Status: succeeded; run: cce13dd0494b4739b8b35c8615212cf2

### Task

Resolve apparently conflicting pump-safety reports for the requested operation. Establish which source applies using the condition, calibration and temporal-order records, without automatically trusting either source.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "0c69f9bd8ff740c4ac9b611fe83637c9",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "calibration",
          "value": "valid",
          "evidence_ids": [
            "e_8f26fb7ab3e6"
          ]
        },
        {
          "subject": "dashboard",
          "value": "safe",
          "evidence_ids": [
            "e_a94cd5a160b9"
          ]
        },
        {
          "subject": "dashboard_condition",
          "value": "unloaded",
          "evidence_ids": [
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "operator_memory",
          "value": "usually_safe",
          "evidence_ids": [
            "e_d0640a52ba7d"
          ]
        },
        {
          "subject": "sample_order",
          "value": "test_newer",
          "evidence_ids": [
            "e_89893e78d219"
          ]
        },
        {
          "subject": "target_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_14d55888f9bc"
          ]
        },
        {
          "subject": "test",
          "value": "unsafe",
          "evidence_ids": [
            "e_776a13a3f006"
          ]
        },
        {
          "subject": "test_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_66806cd423ad"
          ]
        }
      ],
      "insights": [
        {
          "subject": "applicable_source",
          "value": "test",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "preferred_source",
          "value": "test",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_89893e78d219",
            "e_8f26fb7ab3e6",
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "resolved_safety",
          "value": "unsafe",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_776a13a3f006",
            "e_89893e78d219",
            "e_8f26fb7ab3e6",
            "e_a94cd5a160b9",
            "e_cc0aae90b4e6"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6",
          "e_d0640a52ba7d"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_14d55888f9bc",
      "e_66806cd423ad",
      "e_776a13a3f006",
      "e_89893e78d219",
      "e_8f26fb7ab3e6",
      "e_a94cd5a160b9",
      "e_cc0aae90b4e6",
      "e_d0640a52ba7d"
    ],
    "created_at": "2026-09-28T14:58:12.414748Z"
  },
  {
    "id": "507f0692a9264df994a3399864e99658",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "calibration",
          "value": "valid",
          "evidence_ids": [
            "e_8f26fb7ab3e6"
          ]
        },
        {
          "subject": "dashboard",
          "value": "safe",
          "evidence_ids": [
            "e_a94cd5a160b9"
          ]
        },
        {
          "subject": "dashboard_condition",
          "value": "unloaded",
          "evidence_ids": [
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "operator_memory",
          "value": "usually_safe",
          "evidence_ids": [
            "e_d0640a52ba7d"
          ]
        },
        {
          "subject": "sample_order",
          "value": "test_newer",
          "evidence_ids": [
            "e_89893e78d219"
          ]
        },
        {
          "subject": "target_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_14d55888f9bc"
          ]
        },
        {
          "subject": "test",
          "value": "unsafe",
          "evidence_ids": [
            "e_776a13a3f006"
          ]
        },
        {
          "subject": "test_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_66806cd423ad"
          ]
        }
      ],
      "insights": [
        {
          "subject": "applicable_source",
          "value": "test",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "preferred_source",
          "value": "test",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_89893e78d219",
            "e_8f26fb7ab3e6",
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "resolved_safety",
          "value": "unsafe",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_776a13a3f006",
            "e_89893e78d219",
            "e_8f26fb7ab3e6",
            "e_a94cd5a160b9",
            "e_cc0aae90b4e6"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6",
          "e_d0640a52ba7d"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_14d55888f9bc",
      "e_66806cd423ad",
      "e_776a13a3f006",
      "e_89893e78d219",
      "e_8f26fb7ab3e6",
      "e_a94cd5a160b9",
      "e_cc0aae90b4e6",
      "e_d0640a52ba7d"
    ],
    "created_at": "2026-09-28T14:58:12.433597Z"
  },
  {
    "id": "9a0d96cedeab4cd0b8dde8b75cdb360f",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "calibration",
          "value": "valid",
          "evidence_ids": [
            "e_8f26fb7ab3e6"
          ]
        },
        {
          "subject": "dashboard",
          "value": "safe",
          "evidence_ids": [
            "e_a94cd5a160b9"
          ]
        },
        {
          "subject": "dashboard_condition",
          "value": "unloaded",
          "evidence_ids": [
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "operator_memory",
          "value": "usually_safe",
          "evidence_ids": [
            "e_d0640a52ba7d"
          ]
        },
        {
          "subject": "sample_order",
          "value": "test_newer",
          "evidence_ids": [
            "e_89893e78d219"
          ]
        },
        {
          "subject": "target_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_14d55888f9bc"
          ]
        },
        {
          "subject": "test",
          "value": "unsafe",
          "evidence_ids": [
            "e_776a13a3f006"
          ]
        },
        {
          "subject": "test_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_66806cd423ad"
          ]
        }
      ],
      "insights": [
        {
          "subject": "applicable_source",
          "value": "test",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "preferred_source",
          "value": "test",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_89893e78d219",
            "e_8f26fb7ab3e6",
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "resolved_safety",
          "value": "unsafe",
          "evidence_ids": [
            "e_14d55888f9bc",
            "e_66806cd423ad",
            "e_776a13a3f006",
            "e_89893e78d219",
            "e_8f26fb7ab3e6",
            "e_a94cd5a160b9",
            "e_cc0aae90b4e6"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6",
          "e_d0640a52ba7d"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_14d55888f9bc",
      "e_66806cd423ad",
      "e_776a13a3f006",
      "e_89893e78d219",
      "e_8f26fb7ab3e6",
      "e_a94cd5a160b9",
      "e_cc0aae90b4e6",
      "e_d0640a52ba7d"
    ],
    "created_at": "2026-09-28T14:58:12.454129Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "calibration",
        "value": "valid",
        "evidence_ids": [
          "e_8f26fb7ab3e6"
        ]
      },
      {
        "subject": "dashboard",
        "value": "safe",
        "evidence_ids": [
          "e_a94cd5a160b9"
        ]
      },
      {
        "subject": "dashboard_condition",
        "value": "unloaded",
        "evidence_ids": [
          "e_cc0aae90b4e6"
        ]
      },
      {
        "subject": "operator_memory",
        "value": "usually_safe",
        "evidence_ids": [
          "e_d0640a52ba7d"
        ]
      },
      {
        "subject": "sample_order",
        "value": "test_newer",
        "evidence_ids": [
          "e_89893e78d219"
        ]
      },
      {
        "subject": "target_condition",
        "value": "loaded",
        "evidence_ids": [
          "e_14d55888f9bc"
        ]
      },
      {
        "subject": "test",
        "value": "unsafe",
        "evidence_ids": [
          "e_776a13a3f006"
        ]
      },
      {
        "subject": "test_condition",
        "value": "loaded",
        "evidence_ids": [
          "e_66806cd423ad"
        ]
      }
    ],
    "insights": [
      {
        "subject": "applicable_source",
        "value": "test",
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_cc0aae90b4e6"
        ]
      },
      {
        "subject": "preferred_source",
        "value": "test",
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_cc0aae90b4e6"
        ]
      },
      {
        "subject": "resolved_safety",
        "value": "unsafe",
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_14d55888f9bc",
        "e_66806cd423ad",
        "e_776a13a3f006",
        "e_89893e78d219",
        "e_8f26fb7ab3e6",
        "e_a94cd5a160b9",
        "e_cc0aae90b4e6",
        "e_d0640a52ba7d"
      ],
      "unknowns": []
    },
    "conclusion": "stop_loaded_operation",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-contradiction-hard",
  "relevant_evidence_ids": [
    "e_a94cd5a160b9",
    "e_cc0aae90b4e6",
    "e_776a13a3f006",
    "e_66806cd423ad",
    "e_14d55888f9bc",
    "e_8f26fb7ab3e6",
    "e_89893e78d219"
  ],
  "distractor_ids": [
    "e_a6ffa433a2a3",
    "e_e83053d8bd81",
    "e_ad7411770ee1"
  ],
  "claims": [
    {
      "subject": "dashboard",
      "value": "safe",
      "supporting_sets": [
        [
          "e_a94cd5a160b9"
        ]
      ]
    },
    {
      "subject": "dashboard_condition",
      "value": "unloaded",
      "supporting_sets": [
        [
          "e_cc0aae90b4e6"
        ]
      ]
    },
    {
      "subject": "test",
      "value": "unsafe",
      "supporting_sets": [
        [
          "e_776a13a3f006"
        ]
      ]
    },
    {
      "subject": "test_condition",
      "value": "loaded",
      "supporting_sets": [
        [
          "e_66806cd423ad"
        ]
      ]
    },
    {
      "subject": "target_condition",
      "value": "loaded",
      "supporting_sets": [
        [
          "e_14d55888f9bc"
        ]
      ]
    },
    {
      "subject": "calibration",
      "value": "valid",
      "supporting_sets": [
        [
          "e_8f26fb7ab3e6"
        ]
      ]
    },
    {
      "subject": "sample_order",
      "value": "test_newer",
      "supporting_sets": [
        [
          "e_89893e78d219"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "resolved_safety",
      "value": "unsafe",
      "supporting_sets": [
        [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "applicable_source",
      "value": "test",
      "supporting_sets": [
        [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_cc0aae90b4e6"
        ]
      ]
    },
    {
      "subject": "preferred_source",
      "value": "test",
      "supporting_sets": [
        [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_cc0aae90b4e6"
        ]
      ]
    }
  ],
  "expected_conclusion": "stop_loaded_operation",
  "constraints": [
    "dashboard",
    "dashboard_condition",
    "test",
    "test_condition",
    "target_condition",
    "calibration",
    "sample_order"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_5ce6499f2edac8a51eeb",
  "benchmark_version": "2.0.0",
  "optional_claims": [
    {
      "subject": "operator_memory",
      "value": "usually_safe",
      "supporting_sets": [
        [
          "e_d0640a52ba7d"
        ]
      ]
    }
  ],
  "weak_evidence_ids": [
    "e_d0640a52ba7d"
  ],
  "evidence_importance": {
    "e_a94cd5a160b9": 2,
    "e_cc0aae90b4e6": 2,
    "e_776a13a3f006": 2,
    "e_66806cd423ad": 2,
    "e_14d55888f9bc": 2,
    "e_8f26fb7ab3e6": 2,
    "e_89893e78d219": 2
  },
  "decision_supporting_sets": [
    [
      "e_14d55888f9bc",
      "e_66806cd423ad",
      "e_776a13a3f006",
      "e_89893e78d219",
      "e_8f26fb7ab3e6",
      "e_a94cd5a160b9",
      "e_cc0aae90b4e6"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 1,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.0,
    "collective_claim_coverage_gain": 0.0,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.0,
    "marginal_final_support_loss_max": 0.0,
    "evidence_unique": 0.0,
    "evidence_redundancy": 0.6666666666666666,
    "evidence_jaccard": 1.0,
    "claim_unique": 0.0,
    "claim_redundancy": 0.6666666666666666,
    "claim_jaccard": 1.0,
    "insight_unique": 0.0,
    "insight_redundancy": 0.6666666666666666,
    "insight_jaccard": 1.0,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 22,
    "input_tokens": 6594,
    "output_tokens": 1352,
    "total_tokens": 7946,
    "model_calls": 4,
    "latency_ms": 91.30579198244959,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "analytical",
      "worker_1": "skeptical",
      "worker_2": "systems"
    },
    "partitions": {
      "worker_0": [
        "e_8f26fb7ab3e6",
        "e_a6ffa433a2a3",
        "e_776a13a3f006"
      ],
      "worker_1": [
        "e_89893e78d219",
        "e_d0640a52ba7d",
        "e_cc0aae90b4e6",
        "e_66806cd423ad",
        "e_ad7411770ee1"
      ],
      "worker_2": [
        "e_a94cd5a160b9",
        "e_14d55888f9bc",
        "e_e83053d8bd81"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "calibration=valid",
        "dashboard=safe",
        "dashboard_condition=unloaded",
        "sample_order=test_newer",
        "target_condition=loaded",
        "test=unsafe",
        "test_condition=loaded"
      ],
      [
        "calibration=valid",
        "dashboard=safe",
        "dashboard_condition=unloaded",
        "sample_order=test_newer",
        "target_condition=loaded",
        "test=unsafe",
        "test_condition=loaded"
      ],
      [
        "calibration=valid",
        "dashboard=safe",
        "dashboard_condition=unloaded",
        "sample_order=test_newer",
        "target_condition=loaded",
        "test=unsafe",
        "test_condition=loaded"
      ]
    ],
    "worker_evidence": [
      [
        "e_14d55888f9bc",
        "e_66806cd423ad",
        "e_776a13a3f006",
        "e_89893e78d219",
        "e_8f26fb7ab3e6",
        "e_a94cd5a160b9",
        "e_cc0aae90b4e6"
      ],
      [
        "e_14d55888f9bc",
        "e_66806cd423ad",
        "e_776a13a3f006",
        "e_89893e78d219",
        "e_8f26fb7ab3e6",
        "e_a94cd5a160b9",
        "e_cc0aae90b4e6"
      ],
      [
        "e_14d55888f9bc",
        "e_66806cd423ad",
        "e_776a13a3f006",
        "e_89893e78d219",
        "e_8f26fb7ab3e6",
        "e_a94cd5a160b9",
        "e_cc0aae90b4e6"
      ]
    ],
    "worker_required_insights": [
      [
        "resolved_safety=unsafe"
      ],
      [
        "resolved_safety=unsafe"
      ],
      [
        "resolved_safety=unsafe"
      ]
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "stop_loaded_operation",
    "actual_conclusion": "stop_loaded_operation"
  }
}
```

Candidate patterns: ['all agents repeat same evidence']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-contradiction-hard / C3 / repetition 0

Status: succeeded; run: a6bb74caa6ff4f7484204ccee8f35bcf

### Task

Resolve apparently conflicting pump-safety reports for the requested operation. Establish which source applies using the condition, calibration and temporal-order records, without automatically trusting either source.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "06c1412aa77f41e38ad1caae84880f0b",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "calibration",
          "value": "valid",
          "evidence_ids": [
            "e_8f26fb7ab3e6"
          ]
        },
        {
          "subject": "test",
          "value": "unsafe",
          "evidence_ids": [
            "e_776a13a3f006"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_776a13a3f006",
          "e_8f26fb7ab3e6"
        ],
        "unknowns": [
          "dashboard",
          "dashboard_condition",
          "test_condition",
          "target_condition",
          "sample_order",
          "operator_memory"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_776a13a3f006",
      "e_8f26fb7ab3e6"
    ],
    "created_at": "2026-09-28T14:58:12.509888Z"
  },
  {
    "id": "4103ef72372a43beab63521ec700f476",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "dashboard_condition",
          "value": "unloaded",
          "evidence_ids": [
            "e_cc0aae90b4e6"
          ]
        },
        {
          "subject": "operator_memory",
          "value": "usually_safe",
          "evidence_ids": [
            "e_d0640a52ba7d"
          ]
        },
        {
          "subject": "sample_order",
          "value": "test_newer",
          "evidence_ids": [
            "e_89893e78d219"
          ]
        },
        {
          "subject": "test_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_66806cd423ad"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_66806cd423ad",
          "e_89893e78d219",
          "e_cc0aae90b4e6",
          "e_d0640a52ba7d"
        ],
        "unknowns": [
          "dashboard",
          "test",
          "target_condition",
          "calibration"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_66806cd423ad",
      "e_89893e78d219",
      "e_cc0aae90b4e6",
      "e_d0640a52ba7d"
    ],
    "created_at": "2026-09-28T14:58:12.528069Z"
  },
  {
    "id": "63e02f41802c48b8bc690a9e0b2434fe",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "dashboard",
          "value": "safe",
          "evidence_ids": [
            "e_a94cd5a160b9"
          ]
        },
        {
          "subject": "target_condition",
          "value": "loaded",
          "evidence_ids": [
            "e_14d55888f9bc"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_a94cd5a160b9"
        ],
        "unknowns": [
          "dashboard_condition",
          "test",
          "test_condition",
          "calibration",
          "sample_order",
          "operator_memory"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_14d55888f9bc",
      "e_a94cd5a160b9"
    ],
    "created_at": "2026-09-28T14:58:12.548619Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "calibration",
        "value": "valid",
        "evidence_ids": [
          "e_8f26fb7ab3e6"
        ]
      },
      {
        "subject": "dashboard",
        "value": "safe",
        "evidence_ids": [
          "e_a94cd5a160b9"
        ]
      },
      {
        "subject": "dashboard_condition",
        "value": "unloaded",
        "evidence_ids": [
          "e_cc0aae90b4e6"
        ]
      },
      {
        "subject": "operator_memory",
        "value": "usually_safe",
        "evidence_ids": [
          "e_d0640a52ba7d"
        ]
      },
      {
        "subject": "sample_order",
        "value": "test_newer",
        "evidence_ids": [
          "e_89893e78d219"
        ]
      },
      {
        "subject": "target_condition",
        "value": "loaded",
        "evidence_ids": [
          "e_14d55888f9bc"
        ]
      },
      {
        "subject": "test",
        "value": "unsafe",
        "evidence_ids": [
          "e_776a13a3f006"
        ]
      },
      {
        "subject": "test_condition",
        "value": "loaded",
        "evidence_ids": [
          "e_66806cd423ad"
        ]
      }
    ],
    "insights": [
      {
        "subject": "applicable_source",
        "value": "test",
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_cc0aae90b4e6"
        ]
      },
      {
        "subject": "preferred_source",
        "value": "test",
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_cc0aae90b4e6"
        ]
      },
      {
        "subject": "resolved_safety",
        "value": "unsafe",
        "evidence_ids": [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_14d55888f9bc",
        "e_66806cd423ad",
        "e_776a13a3f006",
        "e_89893e78d219",
        "e_8f26fb7ab3e6",
        "e_a94cd5a160b9",
        "e_cc0aae90b4e6",
        "e_d0640a52ba7d"
      ],
      "unknowns": []
    },
    "conclusion": "stop_loaded_operation",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-contradiction-hard",
  "relevant_evidence_ids": [
    "e_a94cd5a160b9",
    "e_cc0aae90b4e6",
    "e_776a13a3f006",
    "e_66806cd423ad",
    "e_14d55888f9bc",
    "e_8f26fb7ab3e6",
    "e_89893e78d219"
  ],
  "distractor_ids": [
    "e_a6ffa433a2a3",
    "e_e83053d8bd81",
    "e_ad7411770ee1"
  ],
  "claims": [
    {
      "subject": "dashboard",
      "value": "safe",
      "supporting_sets": [
        [
          "e_a94cd5a160b9"
        ]
      ]
    },
    {
      "subject": "dashboard_condition",
      "value": "unloaded",
      "supporting_sets": [
        [
          "e_cc0aae90b4e6"
        ]
      ]
    },
    {
      "subject": "test",
      "value": "unsafe",
      "supporting_sets": [
        [
          "e_776a13a3f006"
        ]
      ]
    },
    {
      "subject": "test_condition",
      "value": "loaded",
      "supporting_sets": [
        [
          "e_66806cd423ad"
        ]
      ]
    },
    {
      "subject": "target_condition",
      "value": "loaded",
      "supporting_sets": [
        [
          "e_14d55888f9bc"
        ]
      ]
    },
    {
      "subject": "calibration",
      "value": "valid",
      "supporting_sets": [
        [
          "e_8f26fb7ab3e6"
        ]
      ]
    },
    {
      "subject": "sample_order",
      "value": "test_newer",
      "supporting_sets": [
        [
          "e_89893e78d219"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "resolved_safety",
      "value": "unsafe",
      "supporting_sets": [
        [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_776a13a3f006",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_a94cd5a160b9",
          "e_cc0aae90b4e6"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "applicable_source",
      "value": "test",
      "supporting_sets": [
        [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_cc0aae90b4e6"
        ]
      ]
    },
    {
      "subject": "preferred_source",
      "value": "test",
      "supporting_sets": [
        [
          "e_14d55888f9bc",
          "e_66806cd423ad",
          "e_89893e78d219",
          "e_8f26fb7ab3e6",
          "e_cc0aae90b4e6"
        ]
      ]
    }
  ],
  "expected_conclusion": "stop_loaded_operation",
  "constraints": [
    "dashboard",
    "dashboard_condition",
    "test",
    "test_condition",
    "target_condition",
    "calibration",
    "sample_order"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_5ce6499f2edac8a51eeb",
  "benchmark_version": "2.0.0",
  "optional_claims": [
    {
      "subject": "operator_memory",
      "value": "usually_safe",
      "supporting_sets": [
        [
          "e_d0640a52ba7d"
        ]
      ]
    }
  ],
  "weak_evidence_ids": [
    "e_d0640a52ba7d"
  ],
  "evidence_importance": {
    "e_a94cd5a160b9": 2,
    "e_cc0aae90b4e6": 2,
    "e_776a13a3f006": 2,
    "e_66806cd423ad": 2,
    "e_14d55888f9bc": 2,
    "e_8f26fb7ab3e6": 2,
    "e_89893e78d219": 2
  },
  "decision_supporting_sets": [
    [
      "e_14d55888f9bc",
      "e_66806cd423ad",
      "e_776a13a3f006",
      "e_89893e78d219",
      "e_8f26fb7ab3e6",
      "e_a94cd5a160b9",
      "e_cc0aae90b4e6"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 0,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.5714285714285714,
    "collective_claim_coverage_gain": 0.5714285714285714,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.3333333333333333,
    "marginal_final_support_loss_max": 0.4285714285714286,
    "evidence_unique": 1.0,
    "evidence_redundancy": 0.0,
    "evidence_jaccard": 0.0,
    "claim_unique": 1.0,
    "claim_redundancy": 0.0,
    "claim_jaccard": 0.0,
    "insight_unique": 0,
    "insight_redundancy": 0,
    "insight_jaccard": null,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 0,
    "input_tokens": 4974,
    "output_tokens": 693,
    "total_tokens": 5667,
    "model_calls": 4,
    "latency_ms": 90.13108303770423,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "neutral",
      "worker_1": "neutral",
      "worker_2": "neutral"
    },
    "partitions": {
      "worker_0": [
        "e_8f26fb7ab3e6",
        "e_a6ffa433a2a3",
        "e_776a13a3f006"
      ],
      "worker_1": [
        "e_89893e78d219",
        "e_d0640a52ba7d",
        "e_cc0aae90b4e6",
        "e_66806cd423ad",
        "e_ad7411770ee1"
      ],
      "worker_2": [
        "e_a94cd5a160b9",
        "e_14d55888f9bc",
        "e_e83053d8bd81"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "calibration=valid",
        "test=unsafe"
      ],
      [
        "dashboard_condition=unloaded",
        "sample_order=test_newer",
        "test_condition=loaded"
      ],
      [
        "dashboard=safe",
        "target_condition=loaded"
      ]
    ],
    "worker_evidence": [
      [
        "e_776a13a3f006",
        "e_8f26fb7ab3e6"
      ],
      [
        "e_66806cd423ad",
        "e_89893e78d219",
        "e_cc0aae90b4e6"
      ],
      [
        "e_14d55888f9bc",
        "e_a94cd5a160b9"
      ]
    ],
    "worker_required_insights": [
      [],
      [],
      []
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 0.7142857142857143,
        "drop": 0.2857142857142857
      },
      {
        "supported_final_coverage_without": 0.5714285714285714,
        "drop": 0.4285714285714286
      },
      {
        "supported_final_coverage_without": 0.7142857142857143,
        "drop": 0.2857142857142857
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "stop_loaded_operation",
    "actual_conclusion": "stop_loaded_operation"
  }
}
```

Candidate patterns: ['useful unique contribution']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-diagnosis-medium / C2 / repetition 0

Status: succeeded; run: c1c65c75cced430eb53679b420240bf9

### Task

Diagnose an API slowdown. Distinguish retry amplification from database pressure using intervention and control-cluster records. Establish the states of the controls from evidence; temporal coincidence is not enough.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "2bb7779ba904408d8557686621df6de4",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "control_cluster",
          "value": "healthy",
          "evidence_ids": [
            "e_d763d32b097c"
          ]
        },
        {
          "subject": "database_queue",
          "value": "normal",
          "evidence_ids": [
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "request_mix",
          "value": "stable",
          "evidence_ids": [
            "e_ad6549f71bd0"
          ]
        },
        {
          "subject": "retry_setting",
          "value": "raised",
          "evidence_ids": [
            "e_9c8fb7649713"
          ]
        },
        {
          "subject": "rollback",
          "value": "restores",
          "evidence_ids": [
            "e_33d1b3dd49e1"
          ]
        },
        {
          "subject": "slowdown",
          "value": "present",
          "evidence_ids": [
            "e_2e7fdc63a03f"
          ]
        }
      ],
      "insights": [
        {
          "subject": "candidate",
          "value": "retry",
          "evidence_ids": [
            "e_2e7fdc63a03f",
            "e_9c8fb7649713",
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "cause",
          "value": "retry_amplification",
          "evidence_ids": [
            "e_2e7fdc63a03f",
            "e_33d1b3dd49e1",
            "e_9c8fb7649713",
            "e_b295c4348c4b",
            "e_d763d32b097c"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_ad6549f71bd0",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2e7fdc63a03f",
      "e_33d1b3dd49e1",
      "e_9c8fb7649713",
      "e_ad6549f71bd0",
      "e_b295c4348c4b",
      "e_d763d32b097c"
    ],
    "created_at": "2026-09-28T14:58:12.038946Z"
  },
  {
    "id": "073c41252aa54deb975f6cd261d00bb0",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "control_cluster",
          "value": "healthy",
          "evidence_ids": [
            "e_d763d32b097c"
          ]
        },
        {
          "subject": "database_queue",
          "value": "normal",
          "evidence_ids": [
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "request_mix",
          "value": "stable",
          "evidence_ids": [
            "e_ad6549f71bd0"
          ]
        },
        {
          "subject": "retry_setting",
          "value": "raised",
          "evidence_ids": [
            "e_9c8fb7649713"
          ]
        },
        {
          "subject": "rollback",
          "value": "restores",
          "evidence_ids": [
            "e_33d1b3dd49e1"
          ]
        },
        {
          "subject": "slowdown",
          "value": "present",
          "evidence_ids": [
            "e_2e7fdc63a03f"
          ]
        }
      ],
      "insights": [
        {
          "subject": "candidate",
          "value": "retry",
          "evidence_ids": [
            "e_2e7fdc63a03f",
            "e_9c8fb7649713",
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "cause",
          "value": "retry_amplification",
          "evidence_ids": [
            "e_2e7fdc63a03f",
            "e_33d1b3dd49e1",
            "e_9c8fb7649713",
            "e_b295c4348c4b",
            "e_d763d32b097c"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_ad6549f71bd0",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2e7fdc63a03f",
      "e_33d1b3dd49e1",
      "e_9c8fb7649713",
      "e_ad6549f71bd0",
      "e_b295c4348c4b",
      "e_d763d32b097c"
    ],
    "created_at": "2026-09-28T14:58:12.057252Z"
  },
  {
    "id": "06096edd820e449bb9e141df3e39496d",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "control_cluster",
          "value": "healthy",
          "evidence_ids": [
            "e_d763d32b097c"
          ]
        },
        {
          "subject": "database_queue",
          "value": "normal",
          "evidence_ids": [
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "request_mix",
          "value": "stable",
          "evidence_ids": [
            "e_ad6549f71bd0"
          ]
        },
        {
          "subject": "retry_setting",
          "value": "raised",
          "evidence_ids": [
            "e_9c8fb7649713"
          ]
        },
        {
          "subject": "rollback",
          "value": "restores",
          "evidence_ids": [
            "e_33d1b3dd49e1"
          ]
        },
        {
          "subject": "slowdown",
          "value": "present",
          "evidence_ids": [
            "e_2e7fdc63a03f"
          ]
        }
      ],
      "insights": [
        {
          "subject": "candidate",
          "value": "retry",
          "evidence_ids": [
            "e_2e7fdc63a03f",
            "e_9c8fb7649713",
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "cause",
          "value": "retry_amplification",
          "evidence_ids": [
            "e_2e7fdc63a03f",
            "e_33d1b3dd49e1",
            "e_9c8fb7649713",
            "e_b295c4348c4b",
            "e_d763d32b097c"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_ad6549f71bd0",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2e7fdc63a03f",
      "e_33d1b3dd49e1",
      "e_9c8fb7649713",
      "e_ad6549f71bd0",
      "e_b295c4348c4b",
      "e_d763d32b097c"
    ],
    "created_at": "2026-09-28T14:58:12.077698Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "control_cluster",
        "value": "healthy",
        "evidence_ids": [
          "e_d763d32b097c"
        ]
      },
      {
        "subject": "database_queue",
        "value": "normal",
        "evidence_ids": [
          "e_b295c4348c4b"
        ]
      },
      {
        "subject": "request_mix",
        "value": "stable",
        "evidence_ids": [
          "e_ad6549f71bd0"
        ]
      },
      {
        "subject": "retry_setting",
        "value": "raised",
        "evidence_ids": [
          "e_9c8fb7649713"
        ]
      },
      {
        "subject": "rollback",
        "value": "restores",
        "evidence_ids": [
          "e_33d1b3dd49e1"
        ]
      },
      {
        "subject": "slowdown",
        "value": "present",
        "evidence_ids": [
          "e_2e7fdc63a03f"
        ]
      }
    ],
    "insights": [
      {
        "subject": "candidate",
        "value": "retry",
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_9c8fb7649713",
          "e_b295c4348c4b"
        ]
      },
      {
        "subject": "cause",
        "value": "retry_amplification",
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_2e7fdc63a03f",
        "e_33d1b3dd49e1",
        "e_9c8fb7649713",
        "e_ad6549f71bd0",
        "e_b295c4348c4b",
        "e_d763d32b097c"
      ],
      "unknowns": []
    },
    "conclusion": "cap_retries",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-diagnosis-medium",
  "relevant_evidence_ids": [
    "e_2e7fdc63a03f",
    "e_9c8fb7649713",
    "e_b295c4348c4b",
    "e_d763d32b097c",
    "e_33d1b3dd49e1",
    "e_ad6549f71bd0"
  ],
  "distractor_ids": [
    "e_c09b3193ee51",
    "e_d62eee5aad19",
    "e_179221beb5c4"
  ],
  "claims": [
    {
      "subject": "slowdown",
      "value": "present",
      "supporting_sets": [
        [
          "e_2e7fdc63a03f"
        ]
      ]
    },
    {
      "subject": "retry_setting",
      "value": "raised",
      "supporting_sets": [
        [
          "e_9c8fb7649713"
        ]
      ]
    },
    {
      "subject": "database_queue",
      "value": "normal",
      "supporting_sets": [
        [
          "e_b295c4348c4b"
        ]
      ]
    },
    {
      "subject": "control_cluster",
      "value": "healthy",
      "supporting_sets": [
        [
          "e_d763d32b097c"
        ]
      ]
    },
    {
      "subject": "rollback",
      "value": "restores",
      "supporting_sets": [
        [
          "e_33d1b3dd49e1"
        ]
      ]
    },
    {
      "subject": "request_mix",
      "value": "stable",
      "supporting_sets": [
        [
          "e_ad6549f71bd0"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "cause",
      "value": "retry_amplification",
      "supporting_sets": [
        [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "candidate",
      "value": "retry",
      "supporting_sets": [
        [
          "e_2e7fdc63a03f",
          "e_9c8fb7649713",
          "e_b295c4348c4b"
        ]
      ]
    }
  ],
  "expected_conclusion": "cap_retries",
  "constraints": [
    "slowdown",
    "retry_setting",
    "database_queue",
    "control_cluster",
    "rollback",
    "request_mix"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_c1ce004cd90b2248f521",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_2e7fdc63a03f": 2,
    "e_9c8fb7649713": 2,
    "e_b295c4348c4b": 2,
    "e_d763d32b097c": 2,
    "e_33d1b3dd49e1": 2,
    "e_ad6549f71bd0": 2
  },
  "decision_supporting_sets": [
    [
      "e_2e7fdc63a03f",
      "e_33d1b3dd49e1",
      "e_9c8fb7649713",
      "e_ad6549f71bd0",
      "e_b295c4348c4b",
      "e_d763d32b097c"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 1,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.0,
    "collective_claim_coverage_gain": 0.0,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.0,
    "marginal_final_support_loss_max": 0.0,
    "evidence_unique": 0.0,
    "evidence_redundancy": 0.6666666666666666,
    "evidence_jaccard": 1.0,
    "claim_unique": 0.0,
    "claim_redundancy": 0.6666666666666666,
    "claim_jaccard": 1.0,
    "insight_unique": 0.0,
    "insight_redundancy": 0.6666666666666666,
    "insight_jaccard": 1.0,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 18,
    "input_tokens": 5896,
    "output_tokens": 961,
    "total_tokens": 6857,
    "model_calls": 4,
    "latency_ms": 90.2557090157643,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "skeptical",
      "worker_1": "systems",
      "worker_2": "analytical"
    },
    "partitions": {
      "worker_0": [
        "e_d763d32b097c",
        "e_2e7fdc63a03f",
        "e_179221beb5c4"
      ],
      "worker_1": [
        "e_b295c4348c4b",
        "e_d62eee5aad19",
        "e_9c8fb7649713"
      ],
      "worker_2": [
        "e_c09b3193ee51",
        "e_ad6549f71bd0",
        "e_33d1b3dd49e1"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "control_cluster=healthy",
        "database_queue=normal",
        "request_mix=stable",
        "retry_setting=raised",
        "rollback=restores",
        "slowdown=present"
      ],
      [
        "control_cluster=healthy",
        "database_queue=normal",
        "request_mix=stable",
        "retry_setting=raised",
        "rollback=restores",
        "slowdown=present"
      ],
      [
        "control_cluster=healthy",
        "database_queue=normal",
        "request_mix=stable",
        "retry_setting=raised",
        "rollback=restores",
        "slowdown=present"
      ]
    ],
    "worker_evidence": [
      [
        "e_2e7fdc63a03f",
        "e_33d1b3dd49e1",
        "e_9c8fb7649713",
        "e_ad6549f71bd0",
        "e_b295c4348c4b",
        "e_d763d32b097c"
      ],
      [
        "e_2e7fdc63a03f",
        "e_33d1b3dd49e1",
        "e_9c8fb7649713",
        "e_ad6549f71bd0",
        "e_b295c4348c4b",
        "e_d763d32b097c"
      ],
      [
        "e_2e7fdc63a03f",
        "e_33d1b3dd49e1",
        "e_9c8fb7649713",
        "e_ad6549f71bd0",
        "e_b295c4348c4b",
        "e_d763d32b097c"
      ]
    ],
    "worker_required_insights": [
      [
        "cause=retry_amplification"
      ],
      [
        "cause=retry_amplification"
      ],
      [
        "cause=retry_amplification"
      ]
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "cap_retries",
    "actual_conclusion": "cap_retries"
  }
}
```

Candidate patterns: ['all agents repeat same evidence']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-diagnosis-medium / C3 / repetition 0

Status: succeeded; run: abf393fca8f14b359f179c568933744c

### Task

Diagnose an API slowdown. Distinguish retry amplification from database pressure using intervention and control-cluster records. Establish the states of the controls from evidence; temporal coincidence is not enough.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "2baedfd3b9e54d0fb0726eaeb53ad72a",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "control_cluster",
          "value": "healthy",
          "evidence_ids": [
            "e_d763d32b097c"
          ]
        },
        {
          "subject": "slowdown",
          "value": "present",
          "evidence_ids": [
            "e_2e7fdc63a03f"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_d763d32b097c"
        ],
        "unknowns": [
          "retry_setting",
          "database_queue",
          "rollback",
          "request_mix"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2e7fdc63a03f",
      "e_d763d32b097c"
    ],
    "created_at": "2026-09-28T14:58:12.132431Z"
  },
  {
    "id": "507b2e0d28244bac9eaa263b3aad5ab2",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "database_queue",
          "value": "normal",
          "evidence_ids": [
            "e_b295c4348c4b"
          ]
        },
        {
          "subject": "retry_setting",
          "value": "raised",
          "evidence_ids": [
            "e_9c8fb7649713"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_9c8fb7649713",
          "e_b295c4348c4b"
        ],
        "unknowns": [
          "slowdown",
          "control_cluster",
          "rollback",
          "request_mix"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_9c8fb7649713",
      "e_b295c4348c4b"
    ],
    "created_at": "2026-09-28T14:58:12.150491Z"
  },
  {
    "id": "59a8d9215a784ff1ac76ecc2a986bc4b",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "request_mix",
          "value": "stable",
          "evidence_ids": [
            "e_ad6549f71bd0"
          ]
        },
        {
          "subject": "rollback",
          "value": "restores",
          "evidence_ids": [
            "e_33d1b3dd49e1"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_33d1b3dd49e1",
          "e_ad6549f71bd0"
        ],
        "unknowns": [
          "slowdown",
          "retry_setting",
          "database_queue",
          "control_cluster"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_33d1b3dd49e1",
      "e_ad6549f71bd0"
    ],
    "created_at": "2026-09-28T14:58:12.171761Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "control_cluster",
        "value": "healthy",
        "evidence_ids": [
          "e_d763d32b097c"
        ]
      },
      {
        "subject": "database_queue",
        "value": "normal",
        "evidence_ids": [
          "e_b295c4348c4b"
        ]
      },
      {
        "subject": "request_mix",
        "value": "stable",
        "evidence_ids": [
          "e_ad6549f71bd0"
        ]
      },
      {
        "subject": "retry_setting",
        "value": "raised",
        "evidence_ids": [
          "e_9c8fb7649713"
        ]
      },
      {
        "subject": "rollback",
        "value": "restores",
        "evidence_ids": [
          "e_33d1b3dd49e1"
        ]
      },
      {
        "subject": "slowdown",
        "value": "present",
        "evidence_ids": [
          "e_2e7fdc63a03f"
        ]
      }
    ],
    "insights": [
      {
        "subject": "candidate",
        "value": "retry",
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_9c8fb7649713",
          "e_b295c4348c4b"
        ]
      },
      {
        "subject": "cause",
        "value": "retry_amplification",
        "evidence_ids": [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_2e7fdc63a03f",
        "e_33d1b3dd49e1",
        "e_9c8fb7649713",
        "e_ad6549f71bd0",
        "e_b295c4348c4b",
        "e_d763d32b097c"
      ],
      "unknowns": []
    },
    "conclusion": "cap_retries",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-diagnosis-medium",
  "relevant_evidence_ids": [
    "e_2e7fdc63a03f",
    "e_9c8fb7649713",
    "e_b295c4348c4b",
    "e_d763d32b097c",
    "e_33d1b3dd49e1",
    "e_ad6549f71bd0"
  ],
  "distractor_ids": [
    "e_c09b3193ee51",
    "e_d62eee5aad19",
    "e_179221beb5c4"
  ],
  "claims": [
    {
      "subject": "slowdown",
      "value": "present",
      "supporting_sets": [
        [
          "e_2e7fdc63a03f"
        ]
      ]
    },
    {
      "subject": "retry_setting",
      "value": "raised",
      "supporting_sets": [
        [
          "e_9c8fb7649713"
        ]
      ]
    },
    {
      "subject": "database_queue",
      "value": "normal",
      "supporting_sets": [
        [
          "e_b295c4348c4b"
        ]
      ]
    },
    {
      "subject": "control_cluster",
      "value": "healthy",
      "supporting_sets": [
        [
          "e_d763d32b097c"
        ]
      ]
    },
    {
      "subject": "rollback",
      "value": "restores",
      "supporting_sets": [
        [
          "e_33d1b3dd49e1"
        ]
      ]
    },
    {
      "subject": "request_mix",
      "value": "stable",
      "supporting_sets": [
        [
          "e_ad6549f71bd0"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "cause",
      "value": "retry_amplification",
      "supporting_sets": [
        [
          "e_2e7fdc63a03f",
          "e_33d1b3dd49e1",
          "e_9c8fb7649713",
          "e_b295c4348c4b",
          "e_d763d32b097c"
        ]
      ]
    }
  ],
  "optional_insights": [
    {
      "subject": "candidate",
      "value": "retry",
      "supporting_sets": [
        [
          "e_2e7fdc63a03f",
          "e_9c8fb7649713",
          "e_b295c4348c4b"
        ]
      ]
    }
  ],
  "expected_conclusion": "cap_retries",
  "constraints": [
    "slowdown",
    "retry_setting",
    "database_queue",
    "control_cluster",
    "rollback",
    "request_mix"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_c1ce004cd90b2248f521",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_2e7fdc63a03f": 2,
    "e_9c8fb7649713": 2,
    "e_b295c4348c4b": 2,
    "e_d763d32b097c": 2,
    "e_33d1b3dd49e1": 2,
    "e_ad6549f71bd0": 2
  },
  "decision_supporting_sets": [
    [
      "e_2e7fdc63a03f",
      "e_33d1b3dd49e1",
      "e_9c8fb7649713",
      "e_ad6549f71bd0",
      "e_b295c4348c4b",
      "e_d763d32b097c"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 0,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.6666666666666666,
    "collective_claim_coverage_gain": 0.6666666666666666,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.33333333333333337,
    "marginal_final_support_loss_max": 0.33333333333333337,
    "evidence_unique": 1.0,
    "evidence_redundancy": 0.0,
    "evidence_jaccard": 0.0,
    "claim_unique": 1.0,
    "claim_redundancy": 0.0,
    "claim_jaccard": 0.0,
    "insight_unique": 0,
    "insight_redundancy": 0,
    "insight_jaccard": null,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 0,
    "input_tokens": 4683,
    "output_tokens": 525,
    "total_tokens": 5208,
    "model_calls": 4,
    "latency_ms": 90.27770801912993,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "neutral",
      "worker_1": "neutral",
      "worker_2": "neutral"
    },
    "partitions": {
      "worker_0": [
        "e_d763d32b097c",
        "e_2e7fdc63a03f",
        "e_179221beb5c4"
      ],
      "worker_1": [
        "e_b295c4348c4b",
        "e_d62eee5aad19",
        "e_9c8fb7649713"
      ],
      "worker_2": [
        "e_c09b3193ee51",
        "e_ad6549f71bd0",
        "e_33d1b3dd49e1"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "control_cluster=healthy",
        "slowdown=present"
      ],
      [
        "database_queue=normal",
        "retry_setting=raised"
      ],
      [
        "request_mix=stable",
        "rollback=restores"
      ]
    ],
    "worker_evidence": [
      [
        "e_2e7fdc63a03f",
        "e_d763d32b097c"
      ],
      [
        "e_9c8fb7649713",
        "e_b295c4348c4b"
      ],
      [
        "e_33d1b3dd49e1",
        "e_ad6549f71bd0"
      ]
    ],
    "worker_required_insights": [
      [],
      [],
      []
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 0.6666666666666666,
        "drop": 0.33333333333333337
      },
      {
        "supported_final_coverage_without": 0.6666666666666666,
        "drop": 0.33333333333333337
      },
      {
        "supported_final_coverage_without": 0.6666666666666666,
        "drop": 0.33333333333333337
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "cap_retries",
    "actual_conclusion": "cap_retries"
  }
}
```

Candidate patterns: ['useful unique contribution']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-missing-easy / C2 / repetition 0

Status: succeeded; run: ac239a20e6714bd99579fbed0e2b14e5

### Task

Assess whether a lift can carry a shipment. Check whether the manifest supplies all measurements required by the lifting rule; explicitly identify any information gap instead of substituting an unrelated measurement.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "04156d3cc7de45b6b2162c0c4ca174cc",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "item_mass",
          "value": "not_reported",
          "evidence_ids": [
            "e_9f921c004c6b"
          ]
        },
        {
          "subject": "lifting_rule",
          "value": "mass_required",
          "evidence_ids": [
            "e_ccf7822250eb"
          ]
        },
        {
          "subject": "manifest",
          "value": "complete_inventory",
          "evidence_ids": [
            "e_a699c5508e97"
          ]
        },
        {
          "subject": "rated_capacity",
          "value": "known",
          "evidence_ids": [
            "e_b0eec04ef11c"
          ]
        }
      ],
      "insights": [
        {
          "subject": "information_gap",
          "value": "item_mass",
          "evidence_ids": [
            "e_9f921c004c6b",
            "e_a699c5508e97",
            "e_ccf7822250eb"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_b0eec04ef11c",
          "e_ccf7822250eb"
        ],
        "unknowns": [
          "item_mass"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_9f921c004c6b",
      "e_a699c5508e97",
      "e_b0eec04ef11c",
      "e_ccf7822250eb"
    ],
    "created_at": "2026-09-28T14:58:12.603616Z"
  },
  {
    "id": "3cec2c6690a842eda75e400fa6b849c5",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "item_mass",
          "value": "not_reported",
          "evidence_ids": [
            "e_9f921c004c6b"
          ]
        },
        {
          "subject": "lifting_rule",
          "value": "mass_required",
          "evidence_ids": [
            "e_ccf7822250eb"
          ]
        },
        {
          "subject": "manifest",
          "value": "complete_inventory",
          "evidence_ids": [
            "e_a699c5508e97"
          ]
        },
        {
          "subject": "rated_capacity",
          "value": "known",
          "evidence_ids": [
            "e_b0eec04ef11c"
          ]
        }
      ],
      "insights": [
        {
          "subject": "information_gap",
          "value": "item_mass",
          "evidence_ids": [
            "e_9f921c004c6b",
            "e_a699c5508e97",
            "e_ccf7822250eb"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_b0eec04ef11c",
          "e_ccf7822250eb"
        ],
        "unknowns": [
          "item_mass"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_9f921c004c6b",
      "e_a699c5508e97",
      "e_b0eec04ef11c",
      "e_ccf7822250eb"
    ],
    "created_at": "2026-09-28T14:58:12.621840Z"
  },
  {
    "id": "ccfa1b6a75de48a88d3377c2d4586238",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "item_mass",
          "value": "not_reported",
          "evidence_ids": [
            "e_9f921c004c6b"
          ]
        },
        {
          "subject": "lifting_rule",
          "value": "mass_required",
          "evidence_ids": [
            "e_ccf7822250eb"
          ]
        },
        {
          "subject": "manifest",
          "value": "complete_inventory",
          "evidence_ids": [
            "e_a699c5508e97"
          ]
        },
        {
          "subject": "rated_capacity",
          "value": "known",
          "evidence_ids": [
            "e_b0eec04ef11c"
          ]
        }
      ],
      "insights": [
        {
          "subject": "information_gap",
          "value": "item_mass",
          "evidence_ids": [
            "e_9f921c004c6b",
            "e_a699c5508e97",
            "e_ccf7822250eb"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_b0eec04ef11c",
          "e_ccf7822250eb"
        ],
        "unknowns": [
          "item_mass"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_9f921c004c6b",
      "e_a699c5508e97",
      "e_b0eec04ef11c",
      "e_ccf7822250eb"
    ],
    "created_at": "2026-09-28T14:58:12.642207Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "item_mass",
        "value": "not_reported",
        "evidence_ids": [
          "e_9f921c004c6b"
        ]
      },
      {
        "subject": "lifting_rule",
        "value": "mass_required",
        "evidence_ids": [
          "e_ccf7822250eb"
        ]
      },
      {
        "subject": "manifest",
        "value": "complete_inventory",
        "evidence_ids": [
          "e_a699c5508e97"
        ]
      },
      {
        "subject": "rated_capacity",
        "value": "known",
        "evidence_ids": [
          "e_b0eec04ef11c"
        ]
      }
    ],
    "insights": [
      {
        "subject": "information_gap",
        "value": "item_mass",
        "evidence_ids": [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_ccf7822250eb"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_9f921c004c6b",
        "e_a699c5508e97",
        "e_b0eec04ef11c",
        "e_ccf7822250eb"
      ],
      "unknowns": [
        "item_mass"
      ]
    },
    "conclusion": "undetermined",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-missing-easy",
  "relevant_evidence_ids": [
    "e_b0eec04ef11c",
    "e_9f921c004c6b",
    "e_a699c5508e97",
    "e_ccf7822250eb"
  ],
  "distractor_ids": [
    "e_4d9cada6c23e",
    "e_47fa4bb5c694",
    "e_afdb9fc83747"
  ],
  "claims": [
    {
      "subject": "rated_capacity",
      "value": "known",
      "supporting_sets": [
        [
          "e_b0eec04ef11c"
        ]
      ]
    },
    {
      "subject": "item_mass",
      "value": "not_reported",
      "supporting_sets": [
        [
          "e_9f921c004c6b"
        ]
      ]
    },
    {
      "subject": "manifest",
      "value": "complete_inventory",
      "supporting_sets": [
        [
          "e_a699c5508e97"
        ]
      ]
    },
    {
      "subject": "lifting_rule",
      "value": "mass_required",
      "supporting_sets": [
        [
          "e_ccf7822250eb"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "information_gap",
      "value": "item_mass",
      "supporting_sets": [
        [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_ccf7822250eb"
        ]
      ]
    }
  ],
  "optional_insights": [],
  "expected_conclusion": "undetermined",
  "constraints": [
    "rated_capacity",
    "item_mass",
    "manifest",
    "lifting_rule"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_e9b9ca6bb8fc289ee655",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_b0eec04ef11c": 2,
    "e_9f921c004c6b": 2,
    "e_a699c5508e97": 2,
    "e_ccf7822250eb": 2
  },
  "decision_supporting_sets": [
    [
      "e_9f921c004c6b",
      "e_a699c5508e97",
      "e_b0eec04ef11c",
      "e_ccf7822250eb"
    ]
  ],
  "allowed_uncertainty": [
    "item_mass"
  ],
  "required_unknowns": [
    "item_mass"
  ],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 1,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.0,
    "collective_claim_coverage_gain": 0.0,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.0,
    "marginal_final_support_loss_max": 0.0,
    "evidence_unique": 0.0,
    "evidence_redundancy": 0.6666666666666666,
    "evidence_jaccard": 1.0,
    "claim_unique": 0.0,
    "claim_redundancy": 0.6666666666666666,
    "claim_jaccard": 1.0,
    "insight_unique": 0.0,
    "insight_redundancy": 0.6666666666666666,
    "insight_jaccard": 1.0,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 14,
    "input_tokens": 5159,
    "output_tokens": 658,
    "total_tokens": 5817,
    "model_calls": 4,
    "latency_ms": 89.65924999210984,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "systems",
      "worker_1": "skeptical",
      "worker_2": "analytical"
    },
    "partitions": {
      "worker_0": [
        "e_47fa4bb5c694",
        "e_b0eec04ef11c"
      ],
      "worker_1": [
        "e_afdb9fc83747",
        "e_9f921c004c6b"
      ],
      "worker_2": [
        "e_a699c5508e97",
        "e_4d9cada6c23e",
        "e_ccf7822250eb"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "item_mass=not_reported",
        "lifting_rule=mass_required",
        "manifest=complete_inventory",
        "rated_capacity=known"
      ],
      [
        "item_mass=not_reported",
        "lifting_rule=mass_required",
        "manifest=complete_inventory",
        "rated_capacity=known"
      ],
      [
        "item_mass=not_reported",
        "lifting_rule=mass_required",
        "manifest=complete_inventory",
        "rated_capacity=known"
      ]
    ],
    "worker_evidence": [
      [
        "e_9f921c004c6b",
        "e_a699c5508e97",
        "e_b0eec04ef11c",
        "e_ccf7822250eb"
      ],
      [
        "e_9f921c004c6b",
        "e_a699c5508e97",
        "e_b0eec04ef11c",
        "e_ccf7822250eb"
      ],
      [
        "e_9f921c004c6b",
        "e_a699c5508e97",
        "e_b0eec04ef11c",
        "e_ccf7822250eb"
      ]
    ],
    "worker_required_insights": [
      [
        "information_gap=item_mass"
      ],
      [
        "information_gap=item_mass"
      ],
      [
        "information_gap=item_mass"
      ]
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "undetermined",
    "actual_conclusion": "undetermined"
  }
}
```

Candidate patterns: ['all agents repeat same evidence']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-missing-easy / C3 / repetition 0

Status: succeeded; run: 5778e5dcf5e74758939b369ff0d512de

### Task

Assess whether a lift can carry a shipment. Check whether the manifest supplies all measurements required by the lifting rule; explicitly identify any information gap instead of substituting an unrelated measurement.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "1cfcf177c6f941898791b89aa2ac0e1c",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "rated_capacity",
          "value": "known",
          "evidence_ids": [
            "e_b0eec04ef11c"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_b0eec04ef11c"
        ],
        "unknowns": [
          "item_mass",
          "manifest",
          "lifting_rule"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_b0eec04ef11c"
    ],
    "created_at": "2026-09-28T14:58:12.696488Z"
  },
  {
    "id": "f7eb64b272e44f45816567ce4335a777",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "item_mass",
          "value": "not_reported",
          "evidence_ids": [
            "e_9f921c004c6b"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_9f921c004c6b"
        ],
        "unknowns": [
          "rated_capacity",
          "manifest",
          "lifting_rule"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_9f921c004c6b"
    ],
    "created_at": "2026-09-28T14:58:12.714540Z"
  },
  {
    "id": "f267dd65d05e4132805413e16e5d4514",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "lifting_rule",
          "value": "mass_required",
          "evidence_ids": [
            "e_ccf7822250eb"
          ]
        },
        {
          "subject": "manifest",
          "value": "complete_inventory",
          "evidence_ids": [
            "e_a699c5508e97"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_a699c5508e97",
          "e_ccf7822250eb"
        ],
        "unknowns": [
          "rated_capacity",
          "item_mass"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_a699c5508e97",
      "e_ccf7822250eb"
    ],
    "created_at": "2026-09-28T14:58:12.735070Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "item_mass",
        "value": "not_reported",
        "evidence_ids": [
          "e_9f921c004c6b"
        ]
      },
      {
        "subject": "lifting_rule",
        "value": "mass_required",
        "evidence_ids": [
          "e_ccf7822250eb"
        ]
      },
      {
        "subject": "manifest",
        "value": "complete_inventory",
        "evidence_ids": [
          "e_a699c5508e97"
        ]
      },
      {
        "subject": "rated_capacity",
        "value": "known",
        "evidence_ids": [
          "e_b0eec04ef11c"
        ]
      }
    ],
    "insights": [
      {
        "subject": "information_gap",
        "value": "item_mass",
        "evidence_ids": [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_ccf7822250eb"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_9f921c004c6b",
        "e_a699c5508e97",
        "e_b0eec04ef11c",
        "e_ccf7822250eb"
      ],
      "unknowns": [
        "item_mass"
      ]
    },
    "conclusion": "undetermined",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-missing-easy",
  "relevant_evidence_ids": [
    "e_b0eec04ef11c",
    "e_9f921c004c6b",
    "e_a699c5508e97",
    "e_ccf7822250eb"
  ],
  "distractor_ids": [
    "e_4d9cada6c23e",
    "e_47fa4bb5c694",
    "e_afdb9fc83747"
  ],
  "claims": [
    {
      "subject": "rated_capacity",
      "value": "known",
      "supporting_sets": [
        [
          "e_b0eec04ef11c"
        ]
      ]
    },
    {
      "subject": "item_mass",
      "value": "not_reported",
      "supporting_sets": [
        [
          "e_9f921c004c6b"
        ]
      ]
    },
    {
      "subject": "manifest",
      "value": "complete_inventory",
      "supporting_sets": [
        [
          "e_a699c5508e97"
        ]
      ]
    },
    {
      "subject": "lifting_rule",
      "value": "mass_required",
      "supporting_sets": [
        [
          "e_ccf7822250eb"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "information_gap",
      "value": "item_mass",
      "supporting_sets": [
        [
          "e_9f921c004c6b",
          "e_a699c5508e97",
          "e_ccf7822250eb"
        ]
      ]
    }
  ],
  "optional_insights": [],
  "expected_conclusion": "undetermined",
  "constraints": [
    "rated_capacity",
    "item_mass",
    "manifest",
    "lifting_rule"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_e9b9ca6bb8fc289ee655",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_b0eec04ef11c": 2,
    "e_9f921c004c6b": 2,
    "e_a699c5508e97": 2,
    "e_ccf7822250eb": 2
  },
  "decision_supporting_sets": [
    [
      "e_9f921c004c6b",
      "e_a699c5508e97",
      "e_b0eec04ef11c",
      "e_ccf7822250eb"
    ]
  ],
  "allowed_uncertainty": [
    "item_mass"
  ],
  "required_unknowns": [
    "item_mass"
  ],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 0,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.5,
    "collective_claim_coverage_gain": 0.5,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.3333333333333333,
    "marginal_final_support_loss_max": 0.5,
    "evidence_unique": 1.0,
    "evidence_redundancy": 0.0,
    "evidence_jaccard": 0.0,
    "claim_unique": 1.0,
    "claim_redundancy": 0.0,
    "claim_jaccard": 0.0,
    "insight_unique": 0,
    "insight_redundancy": 0,
    "insight_jaccard": null,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 0,
    "input_tokens": 4284,
    "output_tokens": 391,
    "total_tokens": 4675,
    "model_calls": 4,
    "latency_ms": 90.046291006729,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "neutral",
      "worker_1": "neutral",
      "worker_2": "neutral"
    },
    "partitions": {
      "worker_0": [
        "e_47fa4bb5c694",
        "e_b0eec04ef11c"
      ],
      "worker_1": [
        "e_afdb9fc83747",
        "e_9f921c004c6b"
      ],
      "worker_2": [
        "e_a699c5508e97",
        "e_4d9cada6c23e",
        "e_ccf7822250eb"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "rated_capacity=known"
      ],
      [
        "item_mass=not_reported"
      ],
      [
        "lifting_rule=mass_required",
        "manifest=complete_inventory"
      ]
    ],
    "worker_evidence": [
      [
        "e_b0eec04ef11c"
      ],
      [
        "e_9f921c004c6b"
      ],
      [
        "e_a699c5508e97",
        "e_ccf7822250eb"
      ]
    ],
    "worker_required_insights": [
      [],
      [],
      []
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 0.75,
        "drop": 0.25
      },
      {
        "supported_final_coverage_without": 0.75,
        "drop": 0.25
      },
      {
        "supported_final_coverage_without": 0.5,
        "drop": 0.5
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "undetermined",
    "actual_conclusion": "undetermined"
  }
}
```

Candidate patterns: ['useful unique contribution']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-synthesis-easy / C2 / repetition 0

Status: succeeded; run: d381e20df9144483a37d9453f765df04

### Task

A cooperative must decide whether to release a stored batch. Combine independent origin, inspection and cold-chain records; an attractive label alone is not a release criterion.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "439bc89379fe4047afe1f70dadf77b9d",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "cold_chain",
          "value": "intact",
          "evidence_ids": [
            "e_2790a67d08aa"
          ]
        },
        {
          "subject": "inspection",
          "value": "pass",
          "evidence_ids": [
            "e_45bef06ab0f2"
          ]
        },
        {
          "subject": "origin",
          "value": "verified",
          "evidence_ids": [
            "e_9344ac0c4e4e"
          ]
        },
        {
          "subject": "recipient",
          "value": "registered",
          "evidence_ids": [
            "e_e365284caa2a"
          ]
        }
      ],
      "insights": [
        {
          "subject": "release_basis",
          "value": "complete",
          "evidence_ids": [
            "e_2790a67d08aa",
            "e_45bef06ab0f2",
            "e_9344ac0c4e4e"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e",
          "e_e365284caa2a"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2790a67d08aa",
      "e_45bef06ab0f2",
      "e_9344ac0c4e4e",
      "e_e365284caa2a"
    ],
    "created_at": "2026-09-28T14:58:11.853991Z"
  },
  {
    "id": "aa29c98c24764c0ea7ec34b2e35863eb",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "cold_chain",
          "value": "intact",
          "evidence_ids": [
            "e_2790a67d08aa"
          ]
        },
        {
          "subject": "inspection",
          "value": "pass",
          "evidence_ids": [
            "e_45bef06ab0f2"
          ]
        },
        {
          "subject": "origin",
          "value": "verified",
          "evidence_ids": [
            "e_9344ac0c4e4e"
          ]
        },
        {
          "subject": "recipient",
          "value": "registered",
          "evidence_ids": [
            "e_e365284caa2a"
          ]
        }
      ],
      "insights": [
        {
          "subject": "release_basis",
          "value": "complete",
          "evidence_ids": [
            "e_2790a67d08aa",
            "e_45bef06ab0f2",
            "e_9344ac0c4e4e"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e",
          "e_e365284caa2a"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2790a67d08aa",
      "e_45bef06ab0f2",
      "e_9344ac0c4e4e",
      "e_e365284caa2a"
    ],
    "created_at": "2026-09-28T14:58:11.872827Z"
  },
  {
    "id": "e447643d5e7d446a9f74a7b288102b4e",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "cold_chain",
          "value": "intact",
          "evidence_ids": [
            "e_2790a67d08aa"
          ]
        },
        {
          "subject": "inspection",
          "value": "pass",
          "evidence_ids": [
            "e_45bef06ab0f2"
          ]
        },
        {
          "subject": "origin",
          "value": "verified",
          "evidence_ids": [
            "e_9344ac0c4e4e"
          ]
        },
        {
          "subject": "recipient",
          "value": "registered",
          "evidence_ids": [
            "e_e365284caa2a"
          ]
        }
      ],
      "insights": [
        {
          "subject": "release_basis",
          "value": "complete",
          "evidence_ids": [
            "e_2790a67d08aa",
            "e_45bef06ab0f2",
            "e_9344ac0c4e4e"
          ]
        }
      ],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e",
          "e_e365284caa2a"
        ],
        "unknowns": []
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2790a67d08aa",
      "e_45bef06ab0f2",
      "e_9344ac0c4e4e",
      "e_e365284caa2a"
    ],
    "created_at": "2026-09-28T14:58:11.893104Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "cold_chain",
        "value": "intact",
        "evidence_ids": [
          "e_2790a67d08aa"
        ]
      },
      {
        "subject": "inspection",
        "value": "pass",
        "evidence_ids": [
          "e_45bef06ab0f2"
        ]
      },
      {
        "subject": "origin",
        "value": "verified",
        "evidence_ids": [
          "e_9344ac0c4e4e"
        ]
      },
      {
        "subject": "recipient",
        "value": "registered",
        "evidence_ids": [
          "e_e365284caa2a"
        ]
      }
    ],
    "insights": [
      {
        "subject": "release_basis",
        "value": "complete",
        "evidence_ids": [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_2790a67d08aa",
        "e_45bef06ab0f2",
        "e_9344ac0c4e4e",
        "e_e365284caa2a"
      ],
      "unknowns": []
    },
    "conclusion": "release_batch",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-synthesis-easy",
  "relevant_evidence_ids": [
    "e_9344ac0c4e4e",
    "e_45bef06ab0f2",
    "e_2790a67d08aa",
    "e_e365284caa2a"
  ],
  "distractor_ids": [
    "e_0e97f105fe27",
    "e_91be7aafc057",
    "e_2c409eca7714"
  ],
  "claims": [
    {
      "subject": "origin",
      "value": "verified",
      "supporting_sets": [
        [
          "e_9344ac0c4e4e"
        ]
      ]
    },
    {
      "subject": "inspection",
      "value": "pass",
      "supporting_sets": [
        [
          "e_45bef06ab0f2"
        ]
      ]
    },
    {
      "subject": "cold_chain",
      "value": "intact",
      "supporting_sets": [
        [
          "e_2790a67d08aa"
        ]
      ]
    },
    {
      "subject": "recipient",
      "value": "registered",
      "supporting_sets": [
        [
          "e_e365284caa2a"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "release_basis",
      "value": "complete",
      "supporting_sets": [
        [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e"
        ]
      ]
    }
  ],
  "optional_insights": [],
  "expected_conclusion": "release_batch",
  "constraints": [
    "origin",
    "inspection",
    "cold_chain",
    "recipient"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_cbd363cb2ff48dc99177",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_9344ac0c4e4e": 2,
    "e_45bef06ab0f2": 2,
    "e_2790a67d08aa": 2,
    "e_e365284caa2a": 2
  },
  "decision_supporting_sets": [
    [
      "e_2790a67d08aa",
      "e_45bef06ab0f2",
      "e_9344ac0c4e4e",
      "e_e365284caa2a"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 1,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.0,
    "collective_claim_coverage_gain": 0.0,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.0,
    "marginal_final_support_loss_max": 0.0,
    "evidence_unique": 0.0,
    "evidence_redundancy": 0.6666666666666666,
    "evidence_jaccard": 1.0,
    "claim_unique": 0.0,
    "claim_redundancy": 0.6666666666666666,
    "claim_jaccard": 1.0,
    "insight_unique": 0.0,
    "insight_redundancy": 0.6666666666666666,
    "insight_jaccard": 1.0,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 14,
    "input_tokens": 5016,
    "output_tokens": 617,
    "total_tokens": 5633,
    "model_calls": 4,
    "latency_ms": 91.86270798090845,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "systems",
      "worker_1": "skeptical",
      "worker_2": "analytical"
    },
    "partitions": {
      "worker_0": [
        "e_2c409eca7714",
        "e_45bef06ab0f2"
      ],
      "worker_1": [
        "e_91be7aafc057",
        "e_9344ac0c4e4e",
        "e_2790a67d08aa"
      ],
      "worker_2": [
        "e_0e97f105fe27",
        "e_e365284caa2a"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "cold_chain=intact",
        "inspection=pass",
        "origin=verified",
        "recipient=registered"
      ],
      [
        "cold_chain=intact",
        "inspection=pass",
        "origin=verified",
        "recipient=registered"
      ],
      [
        "cold_chain=intact",
        "inspection=pass",
        "origin=verified",
        "recipient=registered"
      ]
    ],
    "worker_evidence": [
      [
        "e_2790a67d08aa",
        "e_45bef06ab0f2",
        "e_9344ac0c4e4e",
        "e_e365284caa2a"
      ],
      [
        "e_2790a67d08aa",
        "e_45bef06ab0f2",
        "e_9344ac0c4e4e",
        "e_e365284caa2a"
      ],
      [
        "e_2790a67d08aa",
        "e_45bef06ab0f2",
        "e_9344ac0c4e4e",
        "e_e365284caa2a"
      ]
    ],
    "worker_required_insights": [
      [
        "release_basis=complete"
      ],
      [
        "release_basis=complete"
      ],
      [
        "release_basis=complete"
      ]
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "release_batch",
    "actual_conclusion": "release_batch"
  }
}
```

Candidate patterns: ['all agents repeat same evidence']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

## v2-synthesis-easy / C3 / repetition 0

Status: succeeded; run: bf7c4d77c1bc4d17aea825e4953b458d

### Task

A cooperative must decide whether to release a stored batch. Combine independent origin, inspection and cold-chain records; an attractive label alone is not a release criterion.

### Agent outputs / Evidence IDs used

```json
[
  {
    "id": "72de79d3146f4968a919d15fb683202c",
    "name": "worker_0",
    "version": 1,
    "producer": "worker_0",
    "node_id": "worker_0",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "inspection",
          "value": "pass",
          "evidence_ids": [
            "e_45bef06ab0f2"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_45bef06ab0f2"
        ],
        "unknowns": [
          "origin",
          "cold_chain",
          "recipient"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_45bef06ab0f2"
    ],
    "created_at": "2026-09-28T14:58:11.946963Z"
  },
  {
    "id": "5e9d1d0b5eb544d58b1628a94b42bf5f",
    "name": "worker_1",
    "version": 1,
    "producer": "worker_1",
    "node_id": "worker_1",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "cold_chain",
          "value": "intact",
          "evidence_ids": [
            "e_2790a67d08aa"
          ]
        },
        {
          "subject": "origin",
          "value": "verified",
          "evidence_ids": [
            "e_9344ac0c4e4e"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_2790a67d08aa",
          "e_9344ac0c4e4e"
        ],
        "unknowns": [
          "inspection",
          "recipient"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_2790a67d08aa",
      "e_9344ac0c4e4e"
    ],
    "created_at": "2026-09-28T14:58:11.964923Z"
  },
  {
    "id": "42a880873f4d4891b47d50fed0bf3b4e",
    "name": "worker_2",
    "version": 1,
    "producer": "worker_2",
    "node_id": "worker_2",
    "schema_id": "worker.v1",
    "payload": {
      "claims": [
        {
          "subject": "recipient",
          "value": "registered",
          "evidence_ids": [
            "e_e365284caa2a"
          ]
        }
      ],
      "insights": [],
      "uncertainty": {
        "confidence": null,
        "assumptions": [],
        "evidence_ids": [
          "e_e365284caa2a"
        ],
        "unknowns": [
          "origin",
          "inspection",
          "cold_chain"
        ]
      }
    },
    "readers": [
      "synthesizer"
    ],
    "evidence_ids": [
      "e_e365284caa2a"
    ],
    "created_at": "2026-09-28T14:58:11.985075Z"
  }
]
```

### Final output

```json
[
  {
    "claims": [
      {
        "subject": "cold_chain",
        "value": "intact",
        "evidence_ids": [
          "e_2790a67d08aa"
        ]
      },
      {
        "subject": "inspection",
        "value": "pass",
        "evidence_ids": [
          "e_45bef06ab0f2"
        ]
      },
      {
        "subject": "origin",
        "value": "verified",
        "evidence_ids": [
          "e_9344ac0c4e4e"
        ]
      },
      {
        "subject": "recipient",
        "value": "registered",
        "evidence_ids": [
          "e_e365284caa2a"
        ]
      }
    ],
    "insights": [
      {
        "subject": "release_basis",
        "value": "complete",
        "evidence_ids": [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e"
        ]
      }
    ],
    "uncertainty": {
      "confidence": null,
      "assumptions": [],
      "evidence_ids": [
        "e_2790a67d08aa",
        "e_45bef06ab0f2",
        "e_9344ac0c4e4e",
        "e_e365284caa2a"
      ],
      "unknowns": []
    },
    "conclusion": "release_batch",
    "decision_summary": "Public rules evaluated over available observations."
  }
]
```

### Gold

```json
{
  "task_id": "v2-synthesis-easy",
  "relevant_evidence_ids": [
    "e_9344ac0c4e4e",
    "e_45bef06ab0f2",
    "e_2790a67d08aa",
    "e_e365284caa2a"
  ],
  "distractor_ids": [
    "e_0e97f105fe27",
    "e_91be7aafc057",
    "e_2c409eca7714"
  ],
  "claims": [
    {
      "subject": "origin",
      "value": "verified",
      "supporting_sets": [
        [
          "e_9344ac0c4e4e"
        ]
      ]
    },
    {
      "subject": "inspection",
      "value": "pass",
      "supporting_sets": [
        [
          "e_45bef06ab0f2"
        ]
      ]
    },
    {
      "subject": "cold_chain",
      "value": "intact",
      "supporting_sets": [
        [
          "e_2790a67d08aa"
        ]
      ]
    },
    {
      "subject": "recipient",
      "value": "registered",
      "supporting_sets": [
        [
          "e_e365284caa2a"
        ]
      ]
    }
  ],
  "required_insights": [
    {
      "subject": "release_basis",
      "value": "complete",
      "supporting_sets": [
        [
          "e_2790a67d08aa",
          "e_45bef06ab0f2",
          "e_9344ac0c4e4e"
        ]
      ]
    }
  ],
  "optional_insights": [],
  "expected_conclusion": "release_batch",
  "constraints": [
    "origin",
    "inspection",
    "cold_chain",
    "recipient"
  ],
  "failure_factors": [],
  "hidden_annotation": "GOLD_ONLY_cbd363cb2ff48dc99177",
  "benchmark_version": "2.0.0",
  "optional_claims": [],
  "weak_evidence_ids": [],
  "evidence_importance": {
    "e_9344ac0c4e4e": 2,
    "e_45bef06ab0f2": 2,
    "e_2790a67d08aa": 2,
    "e_e365284caa2a": 2
  },
  "decision_supporting_sets": [
    [
      "e_2790a67d08aa",
      "e_45bef06ab0f2",
      "e_9344ac0c4e4e",
      "e_e365284caa2a"
    ]
  ],
  "allowed_uncertainty": [],
  "required_unknowns": [],
  "partition_note": "Oracle relevance/importance strata; count difference at most one. Integer document weights may preclude identical importance totals. Assignment diagnostics record every remaining imbalance."
}
```

### Metrics / errors / assignment

```json
{
  "metrics": {
    "task_success": 1,
    "gold_claim_coverage": 1.0,
    "required_insight_coverage": 1.0,
    "worker_evidence_coverage": 1.0,
    "final_evidence_coverage": 1.0,
    "worker_distinct_insights": 0,
    "worker_contradictions": 0,
    "final_contradictions": 0,
    "unsupported_claims": 0,
    "worker_unsupported_claims": 0,
    "agent_failures": 0,
    "collective_evidence_coverage_gain": 0.5,
    "collective_claim_coverage_gain": 0.5,
    "collective_insight_coverage_gain": 0.0,
    "marginal_final_support_loss_mean": 0.3333333333333333,
    "marginal_final_support_loss_max": 0.5,
    "evidence_unique": 1.0,
    "evidence_redundancy": 0.0,
    "evidence_jaccard": 0.0,
    "claim_unique": 1.0,
    "claim_redundancy": 0.0,
    "claim_jaccard": 0.0,
    "insight_unique": 0,
    "insight_redundancy": 0,
    "insight_jaccard": null,
    "context_leaks": 0,
    "result_leaks": 0,
    "gold_leaks": 0,
    "raw_exposure_outside_partition": 0,
    "input_tokens": 4176,
    "output_tokens": 369,
    "total_tokens": 4545,
    "model_calls": 4,
    "latency_ms": 88.49650004412979,
    "cost_usd": null
  },
  "errors": [],
  "assignment": {
    "roles": {
      "worker_0": "neutral",
      "worker_1": "neutral",
      "worker_2": "neutral"
    },
    "partitions": {
      "worker_0": [
        "e_2c409eca7714",
        "e_45bef06ab0f2"
      ],
      "worker_1": [
        "e_91be7aafc057",
        "e_9344ac0c4e4e",
        "e_2790a67d08aa"
      ],
      "worker_2": [
        "e_0e97f105fe27",
        "e_e365284caa2a"
      ]
    },
    "seed": 20260928
  },
  "diagnostics": {
    "missing_claims": [],
    "missing_insights": [],
    "worker_valid_keys": [
      [
        "inspection=pass"
      ],
      [
        "cold_chain=intact",
        "origin=verified"
      ],
      [
        "recipient=registered"
      ]
    ],
    "worker_evidence": [
      [
        "e_45bef06ab0f2"
      ],
      [
        "e_2790a67d08aa",
        "e_9344ac0c4e4e"
      ],
      [
        "e_e365284caa2a"
      ]
    ],
    "worker_required_insights": [
      [],
      [],
      []
    ],
    "marginal_final_claim_support": [
      {
        "supported_final_coverage_without": 0.75,
        "drop": 0.25
      },
      {
        "supported_final_coverage_without": 0.5,
        "drop": 0.5
      },
      {
        "supported_final_coverage_without": 0.75,
        "drop": 0.25
      }
    ],
    "marginal_final_insight_support": [
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 0.0,
        "drop": 1.0
      },
      {
        "supported_final_coverage_without": 1.0,
        "drop": 0.0
      }
    ],
    "marginal_method": "fixed final-output provenance support loss; no re-generation",
    "expected_conclusion": "release_batch",
    "actual_conclusion": "release_batch"
  }
}
```

Candidate patterns: ['useful unique contribution']

Human checks: [ ] missing global context [ ] role bias [ ] partition-induced failure
[ ] synthesis failure [ ] hallucinated bridge [ ] dominant-agent interpretation
Reviewer / evidence / competing explanation / confidence: TODO

