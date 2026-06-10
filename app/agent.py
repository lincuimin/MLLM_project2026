from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .actions import execute_action, normalize_action
from .browser_env import BrowserEnv
from .config import Settings
from .observation import collect_observation, compact_observation_for_prompt
from .vlm_client import VLMClient


class BrowserAgent:
    def __init__(self, settings: Settings, vlm_client: VLMClient | None = None):
        self.settings = settings
        self.vlm_client = vlm_client or VLMClient(settings)

    def run(
        self,
        start_url: str,
        task_instruction: str,
        task_name: str = "browser_task",
        max_steps: int | None = None,
    ) -> dict[str, Any]:
        run_id = self._create_run_id(task_name)
        screenshot_dir = self.settings.screenshot_dir / run_id
        log_path = self.settings.log_dir / f"{run_id}.json"
        max_steps = max_steps or self.settings.max_steps

        summary: dict[str, Any] = {
            "run_id": run_id,
            "task_name": task_name,
            "start_url": start_url,
            "instruction": task_instruction,
            "status": "running",
            "answer": None,
            "final_url": None,
            "final_title": None,
            "steps": [],
            "log_path": str(log_path),
            "browser": {
                "mode": self._browser_mode(),
                "headless": self.settings.browser_headless,
                "channel": self.settings.browser_channel,
                "cdp": bool(self.settings.browser_cdp_url),
            },
        }

        started_at = time.time()
        try:
            with BrowserEnv(self.settings) as browser:
                browser.goto(start_url)

                for step_index in range(1, max_steps + 1):
                    screenshot_path = screenshot_dir / f"step_{step_index:02d}.png"
                    observation = collect_observation(
                        browser.page,
                        screenshot_path,
                        max_elements=self.settings.observation_max_elements,
                    )
                    compact_observation = compact_observation_for_prompt(observation)

                    decision = self.vlm_client.decide(
                        task_instruction=task_instruction,
                        observation=observation,
                        history=summary["steps"],
                    )
                    action = normalize_action(decision)
                    result = execute_action(browser.page, action, observation["elements"])

                    if result.success and not result.should_finish:
                        browser.page.wait_for_timeout(1000)

                    post_action_state = self._read_page_state(browser.page)
                    step_record = {
                        "step": step_index,
                        "url": observation["url"],
                        "title": observation["title"],
                        "post_action_url": post_action_state["url"],
                        "post_action_title": post_action_state["title"],
                        "screenshot_path": observation["screenshot_path"],
                        "screenshot_type": observation["screenshot_type"],
                        "viewport": observation["viewport"],
                        "element_count": len(observation["elements"]),
                        "elements": compact_observation["elements"],
                        "decision": decision,
                        "action": action,
                        "success": result.success,
                        "message": result.message,
                    }
                    summary["steps"].append(step_record)
                    summary["final_url"] = post_action_state["url"]
                    summary["final_title"] = post_action_state["title"]
                    self._write_log(log_path, summary)

                    if result.should_finish:
                        summary["status"] = "success"
                        summary["answer"] = result.answer
                        break

                    if not result.success:
                        summary["status"] = "failed"
                        summary["answer"] = result.message
                        break

                if summary["status"] == "running":
                    summary["status"] = "failed"
                    summary["answer"] = f"超过最大步数 {max_steps}，任务未完成"

        except Exception as exc:
            summary["status"] = "failed"
            summary["answer"] = str(exc)

        summary["elapsed_seconds"] = round(time.time() - started_at, 2)
        self._write_log(log_path, summary)
        return summary

    @staticmethod
    def _create_run_id(task_name: str) -> str:
        clean_name = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in task_name)
        return f"{time.strftime('%Y%m%d_%H%M%S')}_{clean_name[:40]}"

    @staticmethod
    def _read_page_state(page: Any) -> dict[str, str | None]:
        try:
            title = page.title()
        except Exception:
            title = None

        try:
            url = page.url
        except Exception:
            url = None

        return {"url": url, "title": title}

    def _browser_mode(self) -> str:
        if self.settings.browser_cdp_url:
            return "existing_chrome_cdp"
        if self.settings.browser_channel:
            return f"launch_channel:{self.settings.browser_channel}"
        return "bundled_chromium"

    @staticmethod
    def _write_log(log_path: Path, summary: dict[str, Any]) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
