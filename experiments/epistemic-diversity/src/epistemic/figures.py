"""Small dependency-free, publication-editable SVG plots of observed records."""

from html import escape
from pathlib import Path
from typing import Any

from epistemic.paths import read_json

COLORS = ["#536878", "#6879b0", "#437db0", "#16887b", "#a36b38"]


def text(x: float, y: float, value: str, size: int = 16) -> str:
    return f'<text x="{x}" y="{y}" font-size="{size}">{escape(value)}</text>'


def save(path: Path, title: str, body: str, subtitle: str, height: int = 550) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 {height}">'
        '<rect width="1100" height="100%" fill="#fff"/>'
        '<g font-family="sans-serif" fill="#172b3a">'
        + text(30, 38, title, 24)
        + text(30, 70, subtitle, 16)
        + body
        + "</g></svg>\n"
    )


def bars(report: dict[str, Any], metrics: list[tuple[str, str]], path: Path, title: str) -> None:
    body = ""
    summaries = report["summaries"]
    width = 1040 / len(metrics)
    for col, (metric, label) in enumerate(metrics):
        x = 30 + col * width
        body += text(x, 116, label, 16)
        values = [summaries[c][metric]["mean"] for c in sorted(summaries)]
        maximum = max((v for v in values if v is not None), default=1) or 1
        if metric in {
            "task_success",
            "gold_claim_coverage",
            "worker_evidence_coverage",
            "evidence_unique",
            "evidence_redundancy",
        }:
            maximum = 1
        for row, (condition, value) in enumerate(zip(sorted(summaries), values, strict=True)):
            y = 158 + row * 65
            body += text(x, y, condition)
            if value is None:
                body += text(x + 40, y, "N/A")
                continue
            length = value / maximum * (width - 135)
            body += (
                f'<rect x="{x + 38}" y="{y - 20}" width="{length}" '
                f'height="26" fill="{COLORS[row]}"/>'
            )
            body += text(x + 44 + length, y, f"{value:.3f}" if value < 100 else f"{value:.1f}", 13)
        body += text(x, 490, f"Scale: 0 to {maximum:.3g}; means over tasks", 12)
    subtitle = (
        f"{report['metadata']['interpretation']} | n={report['tasks']} tasks, "
        f"{report['runs']} runs | descriptive means; paired CIs in analysis.json"
    )
    save(path, title, body, subtitle)


def generate(analysis_path: Path, output_dir: Path) -> None:
    report = read_json(analysis_path)
    if not report["runs"]:
        raise ValueError("Figures require executed observations")
    body = ""
    rows = [
        ("C0 Single", "Full evidence → 1 neutral worker → Final answer"),
        ("C1 Homogeneous shared", "Full evidence → 3 neutral workers → Artifacts → Synthesizer"),
        ("C2 Role diverse shared", "Full evidence → 3 different roles → Artifacts → Synthesizer"),
        (
            "C3 Epistemic diverse",
            "3 disjoint partitions → 3 neutral workers → Artifacts → Synthesizer",
        ),
        (
            "C4 Role + epistemic",
            "3 disjoint partitions → 3 shuffled roles → Artifacts → Synthesizer",
        ),
    ]
    for i, (label, flow) in enumerate(rows):
        y = 120 + i * 72
        body += (
            f'<rect x="30" y="{y - 26}" width="1040" height="58" rx="6" '
            f'fill="{COLORS[i]}" opacity=".12"/>'
        )
        body += text(45, y, label, 17) + text(300, y, flow, 16)
    body += text(
        30,
        515,
        "Same model & parameters. C1–C4 share one synthesizer; no raw evidence reaches it.",
        16,
    )
    save(
        output_dir / "figure1_conditions.svg",
        "1 · Experimental conditions",
        body,
        "Design diagram — not an empirical result",
    )
    bars(
        report,
        [("task_success", "Task success"), ("gold_claim_coverage", "Gold claim coverage")],
        output_dir / "figure2_performance.svg",
        "2 · Task performance",
    )
    bars(
        report,
        [
            ("worker_evidence_coverage", "Evidence coverage"),
            ("evidence_unique", "Unique valid evidence"),
            ("evidence_redundancy", "Evidence redundancy"),
        ],
        output_dir / "figure3_diversity.svg",
        "3 · Information recovery and structural overlap",
    )
    bars(
        report,
        [
            ("total_tokens", "Tokens / run (mock: estimate)"),
            ("latency_ms", "Wall latency / run (ms)"),
            ("model_calls", "Provider calls / run"),
        ],
        output_dir / "figure4_resources.svg",
        "4 · Resource trade-offs (not equal total-token budgets)",
    )
    bars(
        report,
        [
            ("context_leaks", "Unauthorized context hits"),
            ("result_leaks", "Unauthorized output hits"),
            ("raw_exposure_outside_partition", "Authorized extra exposure"),
        ],
        output_dir / "figure5_leakage.svg",
        "5 · ACL violations versus structural raw exposure (different concepts)",
    )
    if "collective_evidence_coverage_gain" in next(iter(report["summaries"].values())):
        bars(
            report,
            [
                ("collective_evidence_coverage_gain", "Evidence coverage gain"),
                ("collective_claim_coverage_gain", "Gold fact coverage gain"),
                ("marginal_final_support_loss_mean", "Mean marginal support loss"),
            ],
            output_dir / "figure6_collective.svg",
            "6 · Collective recovery and fixed-output provenance (not regeneration)",
        )
        bars(
            report,
            [
                ("insight_unique", "Unique required insights"),
                ("insight_redundancy", "Required insight redundancy"),
                ("claim_redundancy", "Valid gold fact redundancy"),
            ],
            output_dir / "figure7_useful_diversity.svg",
            "7 · Useful uniqueness and redundancy (canonical sets)",
        )
