from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import Settings


JSONL_FIELDS = [
    "recorded_at",
    "run_id",
    "task_name",
    "task_file",
    "suite",
    "task_type",
    "difficulty",
    "start_url",
    "instruction",
    "expected_result",
    "success_criteria",
    "status",
    "success",
    "step_count",
    "elapsed_seconds",
    "final_url",
    "final_title",
    "answer",
    "error_message",
    "log_path",
    "first_screenshot",
    "last_screenshot",
    "model_name",
    "browser_mode",
]


def build_evaluation_record(
    summary: dict[str, Any],
    task: dict[str, Any],
    task_file: Path,
    settings: Settings,
) -> dict[str, Any]:
    steps = summary.get("steps", [])
    first_step = steps[0] if steps else {}
    last_step = steps[-1] if steps else {}
    evaluation = task.get("evaluation", {})

    status = summary.get("status", "unknown")
    success = status == "success"

    return {
        "recorded_at": datetime.now().isoformat(timespec="seconds"),
        "run_id": summary.get("run_id"),
        "task_name": summary.get("task_name"),
        "task_file": str(task_file),
        "suite": evaluation.get("suite", "default"),
        "task_type": evaluation.get("task_type", "unknown"),
        "difficulty": evaluation.get("difficulty", "unknown"),
        "start_url": summary.get("start_url"),
        "instruction": summary.get("instruction"),
        "expected_result": evaluation.get("expected_result", ""),
        "success_criteria": evaluation.get("success_criteria", []),
        "status": status,
        "success": success,
        "step_count": len(steps),
        "elapsed_seconds": summary.get("elapsed_seconds"),
        "final_url": summary.get("final_url") or last_step.get("post_action_url") or last_step.get("url"),
        "final_title": summary.get("final_title")
        or last_step.get("post_action_title")
        or last_step.get("title"),
        "answer": summary.get("answer"),
        "error_message": "" if success else summary.get("answer", ""),
        "log_path": summary.get("log_path"),
        "first_screenshot": first_step.get("screenshot_path"),
        "last_screenshot": last_step.get("screenshot_path"),
        "model_name": settings.vlm_model_name,
        "browser_mode": _browser_mode(settings),
    }


def append_evaluation_record(record: dict[str, Any], settings: Settings) -> dict[str, str]:
    jsonl_path = settings.evaluation_dir / "runs.jsonl"
    csv_path = settings.evaluation_dir / "runs.csv"

    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as jsonl_file:
        jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    csv_exists = csv_path.exists()
    with csv_path.open("a", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=JSONL_FIELDS)
        if not csv_exists:
            writer.writeheader()
        writer.writerow(_csv_safe_record(record))

    return {
        "jsonl_path": str(jsonl_path),
        "csv_path": str(csv_path),
    }


def _csv_safe_record(record: dict[str, Any]) -> dict[str, Any]:
    safe_record = {}
    for field in JSONL_FIELDS:
        value = record.get(field)
        if isinstance(value, (list, dict)):
            value = json.dumps(value, ensure_ascii=False)
        safe_record[field] = value
    return safe_record


def _browser_mode(settings: Settings) -> str:
    if settings.browser_cdp_url:
        return "existing_chrome_cdp"
    if settings.browser_channel:
        return f"launch_channel:{settings.browser_channel}"
    return "bundled_chromium"