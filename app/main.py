from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.agent import BrowserAgent
    from app.config import get_settings
    from app.evaluation import append_evaluation_record, build_evaluation_record
else:
    from .agent import BrowserAgent
    from .config import get_settings
    from .evaluation import append_evaluation_record, build_evaluation_record


def load_task(task_file: Path) -> dict[str, Any]:
    return json.loads(task_file.read_text(encoding="utf-8"))


def run_task(task_file: Path) -> dict[str, Any]:
    task = load_task(task_file)
    settings = get_settings(require_api_key=True)
    agent = BrowserAgent(settings)
    summary = agent.run(
        start_url=task["start_url"],
        task_instruction=task["instruction"],
        task_name=task.get("name", task_file.stem),
        max_steps=task.get("max_steps"),
    )
    evaluation_record = build_evaluation_record(summary, task, task_file, settings)
    evaluation_paths = append_evaluation_record(evaluation_record, settings)
    summary["evaluation"] = {
        "record": evaluation_record,
        **evaluation_paths,
    }
    Path(summary["log_path"]).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a browser automation task.")
    parser.add_argument("--task-file", required=True, help="Path to a JSON task file.")
    args = parser.parse_args()

    summary = run_task(Path(args.task_file))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
