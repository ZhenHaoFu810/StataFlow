"""Tests for validation manifest and evidence summary generation."""

from pathlib import Path

from scripts.validation.collect_validation_summary import build_summary, write_summary_artifacts
from scripts.validation.manifest import COMMANDS, EVIDENCE_CASES, REAL_DATA_COMMANDS, VALIDATED_COMMANDS


def test_every_validated_command_has_manifest_entries():
    manifest_commands = {case.command for case in EVIDENCE_CASES}
    assert set(VALIDATED_COMMANDS) == manifest_commands
    assert set(COMMANDS) >= manifest_commands


def test_every_validated_command_has_real_data_evidence():
    assert set(VALIDATED_COMMANDS) == set(REAL_DATA_COMMANDS)


def test_summary_builder_exposes_overview_and_rows():
    summary = build_summary()
    assert summary["strict_alignment_standard"] == "field_level_strict"
    assert summary["command_count"] == len(VALIDATED_COMMANDS)
    assert any(row["command"] == "reghdfe" for row in summary["commands"])
    assert any(case["case_id"] == "v1_regress_real_grunfeld" for case in summary["evidence_cases"])


def test_write_summary_artifacts(tmp_path: Path):
    json_path, md_path = write_summary_artifacts(tmp_path)
    assert json_path.exists()
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "# Validation Summary" in content
    assert "Strict alignment standard" in content
    assert "reghdfe" in content
