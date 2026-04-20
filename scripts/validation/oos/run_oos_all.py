"""Master runner for all out-of-sample validation families."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validation.oos.common import RESULTS_DIR

FAMILY_RUNNERS = [
    "scripts.validation.oos.run_oos_linear",
    "scripts.validation.oos.run_oos_iv",
    "scripts.validation.oos.run_oos_glm",
    "scripts.validation.oos.run_oos_did",
    "scripts.validation.oos.run_oos_rd",
]


def run_all() -> dict:
    overall = {
        "families": [],
        "total_cases": 0,
        "total_passed": 0,
        "total_blocked": 0,
    }

    for module_name in FAMILY_RUNNERS:
        print(f"\n=== Running {module_name} ===")
        try:
            __import__(module_name)
        except Exception as exc:
            print(f"FAILED to import/run {module_name}: {exc}")
            overall["families"].append({
                "family": module_name.split(".")[-1].replace("run_oos_", ""),
                "error": str(exc),
            })

    # Collect summary JSONs
    for summary_file in sorted(RESULTS_DIR.glob("*_summary.json")):
        content = json.loads(summary_file.read_text(encoding="utf-8"))
        overall["families"].append(content)
        overall["total_cases"] += content.get("cases", 0)
        overall["total_passed"] += content.get("passed", 0)
        overall["total_blocked"] += content.get("blocked", 0)

    # Write master summary
    master_path = RESULTS_DIR / "oos_master_summary.json"
    master_path.write_text(json.dumps(overall, indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown render
    md_lines = [
        "# Out-of-Sample Validation Master Summary",
        "",
        f"- Total cases: {overall['total_cases']}",
        f"- Passed: {overall['total_passed']}",
        f"- Blocked: {overall['total_blocked']}",
        "",
        "## By Family",
        "",
        "| Family | Cases | Passed | Blocked |",
        "| --- | --- | --- | --- |",
    ]
    for fam in overall["families"]:
        if "error" in fam:
            md_lines.append(f"| {fam.get('family', 'unknown')} | ERROR | - | - |")
        else:
            md_lines.append(f"| {fam['family']} | {fam['cases']} | {fam['passed']} | {fam['blocked']} |")

    md_lines.extend(["", "## Case Detail"])
    for fam in overall["families"]:
        if "error" in fam:
            continue
        for r in fam.get("reports", []):
            md_lines.append(f"- `{r['case_id']}` ({r['command']}) — **{r['status']}**")

    md_path = RESULTS_DIR / "oos_master_summary.md"
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"\nMaster summary written to {master_path}")
    print(f"Master markdown written to {md_path}")
    return overall


if __name__ == "__main__":
    result = run_all()
    print(f"\nOOS validation complete: {result['total_passed']}/{result['total_cases']} passed.")
    sys.exit(0 if result["total_blocked"] == 0 else 1)
