from __future__ import annotations

import csv
import html
import json
import os
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
    "failure_type",
    "error_analysis",
    "log_path",
    "report_path",
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
    failure_type = "" if success else classify_failure(summary)
    error_analysis = "" if success else build_error_analysis(summary, failure_type)

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
        "failure_type": failure_type,
        "error_analysis": error_analysis,
        "log_path": summary.get("log_path"),
        "report_path": "",
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


def classify_failure(summary: dict[str, Any]) -> str:
    if summary.get("status") == "success":
        return ""

    answer = str(summary.get("answer") or "")
    steps = summary.get("steps", [])
    last_step = steps[-1] if steps else {}
    last_message = str(last_step.get("message") or "")
    last_decision = last_step.get("decision") or {}

    combined = f"{answer}\n{last_message}".lower()

    execution_markers = [
        "client error",
        "too many requests",
        "forbidden",
        "timeout",
        "page.evaluate",
        "execution context was destroyed",
        "most likely because of a navigation",
        "动作执行失败",
        "browser",
        "playwright",
        "net::",
        "http",
    ]
    if any(marker in combined for marker in execution_markers):
        return "执行失败"

    recognition_markers = [
        "当前页面没有 element_id",
        "没有 element_id",
        "动作缺少有效的 element_id",
        "模型输出不是 json",
        "模型没有输出 json",
        "不支持的动作",
    ]
    if any(marker in combined for marker in recognition_markers):
        return "识别失败"

    if "超过最大步数" in answer:
        if _has_repeated_actions(steps) or _has_stagnant_url(steps):
            return "规划失败"
        return "规划失败"

    action_name = str(last_decision.get("action", "")).lower()
    if action_name and action_name not in {"click", "type", "press", "scroll", "wait", "finish"}:
        return "识别失败"

    return "规划失败"


def build_error_analysis(summary: dict[str, Any], failure_type: str) -> str:
    answer = str(summary.get("answer") or "未知错误")
    steps = summary.get("steps", [])
    last_step = steps[-1] if steps else {}
    final_url = summary.get("final_url") or last_step.get("post_action_url") or ""

    if failure_type == "执行失败":
        if "Too Many Requests" in answer or "429" in answer:
            return "模型 API 触发限流，浏览器任务未能继续执行。建议降低并发/调用频率，或增加 429 重试和退避等待。"
        if "Forbidden" in answer or "403" in answer:
            return "模型 API 返回 403，通常是密钥、权限、额度或模型访问配置问题。建议检查 .env.example 中的 API Key、模型名和服务权限。"
        if "Execution context was destroyed" in answer:
            return "页面正在导航时采集元素，Playwright 的 JS 上下文被销毁。建议在动作后等待页面稳定，并对页面观察增加重试。"
        return f"动作执行或外部服务调用失败。最后页面: {final_url}。原始错误: {answer}"

    if failure_type == "识别失败":
        return "模型输出的动作无法和当前页面元素稳定对应，可能是元素编号识别错误、输出 JSON 格式错误，或选择了当前页面不存在的 element_id。建议强化动作 JSON 约束并优化可操作元素提取。"

    if failure_type == "规划失败":
        repeated = "存在重复动作或页面停留不前，" if _has_repeated_actions(steps) or _has_stagnant_url(steps) else ""
        return f"{repeated}模型没有在最大步数内完成任务。建议提高 max_steps，或在任务 instruction 中明确完成条件和关键路径。"

    return answer


def generate_trace_report(
    summary: dict[str, Any],
    evaluation_record: dict[str, Any],
    settings: Settings,
) -> Path:
    report_path = settings.report_dir / f"{summary.get('run_id', 'run')}.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_trace_report(summary, evaluation_record, report_path),
        encoding="utf-8",
    )
    return report_path


def _render_trace_report(
    summary: dict[str, Any],
    evaluation_record: dict[str, Any],
    report_path: Path,
) -> str:
    status = summary.get("status", "unknown")
    failure_type = evaluation_record.get("failure_type") or "无"
    error_analysis = evaluation_record.get("error_analysis") or "无"
    steps_html = "\n".join(
        _render_step(step, report_path)
        for step in summary.get("steps", [])
    )
    if not steps_html:
        steps_html = "<p class=\"empty\">没有记录到操作步骤。</p>"

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{_esc(summary.get("run_id", "trace report"))}</title>
  <style>
    body {{ margin: 0; font-family: Arial, "Microsoft YaHei", sans-serif; color: #172033; background: #f6f7f9; }}
    header {{ padding: 24px 32px; background: #172033; color: #fff; }}
    main {{ padding: 24px 32px; max-width: 1180px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    .summary, .step {{ background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 16px; margin-bottom: 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 18px; }}
    .label {{ color: #5d6b82; font-size: 13px; }}
    .value {{ margin-top: 2px; word-break: break-word; }}
    .badge {{ display: inline-block; padding: 3px 8px; border-radius: 999px; background: #e9eef7; font-size: 13px; }}
    .badge.failed {{ background: #fde8e8; color: #9b1c1c; }}
    .badge.success {{ background: #def7ec; color: #03543f; }}
    img {{ max-width: 100%; border: 1px solid #d8dee8; border-radius: 6px; background: #fff; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #101828; color: #eef2ff; padding: 12px; border-radius: 6px; overflow: auto; }}
    .step-head {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 12px; }}
    .empty {{ color: #5d6b82; }}
  </style>
</head>
<body>
  <header>
    <h1>{_esc(summary.get("run_id", "trace report"))}</h1>
    <div>任务：{_esc(summary.get("task_name", ""))}</div>
  </header>
  <main>
    <section class="summary">
      <h2>运行摘要</h2>
      <div class="grid">
        <div><div class="label">状态</div><div class="value"><span class="badge {_esc(status)}">{_esc(status)}</span></div></div>
        <div><div class="label">失败类型</div><div class="value">{_esc(failure_type)}</div></div>
        <div><div class="label">最终 URL</div><div class="value">{_esc(summary.get("final_url", ""))}</div></div>
        <div><div class="label">最终标题</div><div class="value">{_esc(summary.get("final_title", ""))}</div></div>
        <div><div class="label">步数</div><div class="value">{len(summary.get("steps", []))}</div></div>
        <div><div class="label">耗时</div><div class="value">{_esc(summary.get("elapsed_seconds", ""))} 秒</div></div>
      </div>
    </section>
    <section class="summary">
      <h2>错误分析</h2>
      <p>{_esc(error_analysis)}</p>
      <pre>{_esc(summary.get("answer", ""))}</pre>
    </section>
    <section>
      <h2>操作轨迹</h2>
      {steps_html}
    </section>
  </main>
</body>
</html>
"""


def _render_step(step: dict[str, Any], report_path: Path) -> str:
    screenshot = step.get("screenshot_path")
    image_src = ""
    if screenshot:
        try:
            image_src = os.path.relpath(
                Path(screenshot).resolve(),
                report_path.parent.resolve(),
            )
        except ValueError:
            image_src = Path(screenshot).resolve().as_uri()

    decision = json.dumps(step.get("decision", {}), ensure_ascii=False, indent=2)
    action = json.dumps(step.get("action", {}), ensure_ascii=False, indent=2)
    image_html = f'<img src="{_esc(image_src)}" alt="step {step.get("step")} screenshot">' if image_src else ""

    return f"""<article class="step">
  <div class="step-head">
    <h2>Step {_esc(step.get("step", ""))}</h2>
    <span class="badge">{_esc("success" if step.get("success") else "failed")}</span>
  </div>
  <div class="grid">
    <div><div class="label">动作前 URL</div><div class="value">{_esc(step.get("url", ""))}</div></div>
    <div><div class="label">动作后 URL</div><div class="value">{_esc(step.get("post_action_url", ""))}</div></div>
    <div><div class="label">页面标题</div><div class="value">{_esc(step.get("title", ""))}</div></div>
    <div><div class="label">执行结果</div><div class="value">{_esc(step.get("message", ""))}</div></div>
  </div>
  <h2>截图</h2>
  {image_html}
  <h2>模型决策</h2>
  <pre>{_esc(decision)}</pre>
  <h2>执行动作</h2>
  <pre>{_esc(action)}</pre>
</article>"""


def _has_repeated_actions(steps: list[dict[str, Any]]) -> bool:
    if len(steps) < 3:
        return False
    signatures = [
        (
            step.get("action", {}).get("action"),
            step.get("action", {}).get("element_id"),
            step.get("action", {}).get("key"),
            step.get("action", {}).get("text"),
            step.get("url"),
        )
        for step in steps
    ]
    for index in range(len(signatures) - 2):
        if signatures[index] == signatures[index + 1] == signatures[index + 2]:
            return True
    return False


def _has_stagnant_url(steps: list[dict[str, Any]]) -> bool:
    if len(steps) < 4:
        return False
    recent = steps[-4:]
    urls = [step.get("post_action_url") or step.get("url") for step in recent]
    return len(set(urls)) == 1


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


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
