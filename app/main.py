from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from app.config import get_settings
    from app.evaluation import append_evaluation_record, build_evaluation_record, generate_trace_report
    from app.task_generator import TaskGenerator, save_generated_task
else:
    from .config import get_settings
    from .evaluation import append_evaluation_record, build_evaluation_record, generate_trace_report
    from .task_generator import TaskGenerator, save_generated_task


def load_task(task_file: Path) -> dict[str, Any]:
    return json.loads(task_file.read_text(encoding="utf-8"))


def run_task(task_file: Path) -> dict[str, Any]:
    task = load_task(task_file)
    settings = get_settings(require_api_key=True)
    if __package__ in {None, ""}:
        from app.agent import BrowserAgent
    else:
        from .agent import BrowserAgent

    agent = BrowserAgent(settings)
    summary = agent.run(
        start_url=task["start_url"],
        task_instruction=task["instruction"],
        task_name=task.get("name", task_file.stem),
        max_steps=task.get("max_steps"),
    )
    evaluation_record = build_evaluation_record(summary, task, task_file, settings)
    report_path = generate_trace_report(summary, evaluation_record, settings)
    evaluation_record["report_path"] = str(report_path)
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


def run_command(command: str) -> dict[str, Any]:
    settings = get_settings(require_api_key=True)
    task = TaskGenerator(settings).generate(command)
    task_file = save_generated_task(task, settings.output_dir / "generated_tasks")

    if __package__ in {None, ""}:
        from app.agent import BrowserAgent
    else:
        from .agent import BrowserAgent

    agent = BrowserAgent(settings)
    summary = agent.run(
        start_url=task["start_url"],
        task_instruction=task["instruction"],
        task_name=task.get("name", task_file.stem),
        max_steps=task.get("max_steps"),
    )
    evaluation_record = build_evaluation_record(summary, task, task_file, settings)
    report_path = generate_trace_report(summary, evaluation_record, settings)
    evaluation_record["report_path"] = str(report_path)
    evaluation_paths = append_evaluation_record(evaluation_record, settings)
    summary["generated_task_file"] = str(task_file)
    summary["generated_task"] = task
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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--task-file", help="Path to a JSON task file.")
    source.add_argument("--command", help="Natural language command to convert and run.")
    args = parser.parse_args()

    if args.command:
        summary = run_command(args.command)
    else:
        summary = run_task(Path(args.task_file))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
