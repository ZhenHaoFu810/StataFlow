"""Generate JSON/Markdown evidence summaries from the validation manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validation.manifest import (
    COMMAND_STATUSES,
    DATASETS,
    EVIDENCE_CASES,
    REAL_DATA_COMMANDS,
    VALIDATED_COMMANDS,
    serialise_datasets,
    serialise_evidence_cases,
)


def build_summary() -> dict[str, object]:
    dataset_rows = serialise_datasets()
    evidence_rows = serialise_evidence_cases()

    commands = []
    for command in VALIDATED_COMMANDS:
        command_cases = [case for case in evidence_rows if case["command"] == command]
        commands.append(
            {
                "command": command,
                "status": COMMAND_STATUSES[command],
                "synthetic_cases": len([case for case in command_cases if case["validation_line"] == "synthetic"]),
                "real_data_cases": len([case for case in command_cases if case["validation_line"] == "real_data"]),
                "datasets": sorted({case["dataset_key"] for case in command_cases if case["dataset_key"] != "synthetic"}),
            }
        )

    return {
        "strict_alignment_standard": "field_level_strict",
        "target_stata_version": "17",
        "command_count": len(VALIDATED_COMMANDS),
        "dataset_count": len(DATASETS),
        "validated_real_data_command_count": len(REAL_DATA_COMMANDS),
        "commands": commands,
        "datasets": dataset_rows,
        "evidence_cases": evidence_rows,
    }


def _render_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Validation Summary",
        "",
        f"- Strict alignment standard: `{summary['strict_alignment_standard']}`",
        f"- Target Stata version: `{summary['target_stata_version']}`",
        f"- Commands with evidence rows: `{summary['command_count']}`",
        f"- Registered public datasets: `{summary['dataset_count']}`",
        f"- Commands with real-data evidence: `{summary['validated_real_data_command_count']}`",
        "",
        "## Command Coverage",
        "",
        "| Command | Status | Synthetic cases | Real-data cases | Datasets |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary["commands"]:
        datasets = ", ".join(row["datasets"]) if row["datasets"] else "-"
        lines.append(
            f"| `{row['command']}` | `{row['status']}` | {row['synthetic_cases']} | {row['real_data_cases']} | {datasets} |"
        )

    lines.extend(
        [
            "",
            "## Dataset Registry Snapshot",
            "",
            "| Dataset | Family | Local path | Status | Commands |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in summary["datasets"]:
        commands = ", ".join(row["commands"])
        lines.append(
            f"| `{row['key']}` | {row['family']} | `{row['local_path']}` | `{row['status']}` | {commands} |"
        )

    return "\n".join(lines) + "\n"


def write_summary_artifacts(output_dir: Path | str) -> tuple[Path, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summary = build_summary()
    json_path = output_path / "evidence-summary.json"
    md_path = output_path / "evidence-summary.md"

    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_render_markdown(summary), encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    repo_output = Path("research/results/validation")
    json_path, md_path = write_summary_artifacts(repo_output)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
