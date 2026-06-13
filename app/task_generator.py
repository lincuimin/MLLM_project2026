from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from .config import PROJECT_ROOT, Settings
from .vlm_client import VLMClient


TASK_TEMPLATE_PATH = PROJECT_ROOT / "tasks" / "task_template.json"


class TaskGenerationError(RuntimeError):
    pass


class TaskGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, user_command: str) -> dict[str, Any]:
        prompt = self._build_prompt(user_command)
        payload = {
            "model": self.settings.vlm_model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": 800,
            "temperature": 0.0,
        }

        response = requests.post(
            self.settings.vlm_api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.vlm_api_key}",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        task = VLMClient._extract_json(content)
        if task.get("action") == "error":
            raise TaskGenerationError(task.get("reason", "模型没有输出合法任务 JSON"))

        return self._normalize_task(task, user_command)

    def _build_prompt(self, user_command: str) -> str:
        template = json.loads(TASK_TEMPLATE_PATH.read_text(encoding="utf-8"))
        return f"""
你是一个WebAgent任务生成器。

请把用户输入转换成标准JSON。

只输出合法JSON，不要输出Markdown，不要解释。

目标JSON必须符合这个结构:
{json.dumps(template, ensure_ascii=False, indent=2)}

字段要求:
- name: 英文小写、数字和下划线，简短描述任务。
- start_url: 必须是 http 或 https URL。
  - 如果用户输入里有网址，优先使用用户给的网址。
  - 如果用户输入里没有网址，你需要根据任务目标自己推断最合适的网站首页或功能页。
  - 优先选择目标领域的常用网站或权威网站，不要默认使用搜索引擎。
  - 例子: 搜索开源项目用 https://github.com/；搜索电影信息用 https://movie.douban.com/explore；查询中国城市天气用 https://www.weather.com.cn/。
- instruction: 用中文写清楚 Agent 要在网页中完成什么，以及什么情况下可以 finish。
- max_steps: 简单搜索任务通常为 6，复杂任务为 8 到 12。
- evaluation.suite: 默认 basic_web_tasks。
- evaluation.task_type: 可选 search、query、navigation、form、unknown。
- evaluation.difficulty: 可选 easy、medium、hard。
- evaluation.expected_result: 描述理想最终页面或最终回答。
- evaluation.success_criteria: 给出 3 到 4 条可复核成功标准。
- evaluation.notes: 没有特别说明可以省略。

用户输入:
{user_command}
""".strip()

    def _normalize_task(self, task: dict[str, Any], user_command: str) -> dict[str, Any]:
        required_fields = ["name", "start_url", "instruction", "evaluation"]
        missing = [field for field in required_fields if field not in task]
        if missing:
            raise TaskGenerationError(f"生成的任务缺少字段: {', '.join(missing)}")

        start_url = self._normalize_url(str(task["start_url"]).strip())
        if not self._is_valid_url(start_url):
            extracted_url = self._extract_url(user_command)
            start_url = extracted_url or self._infer_start_url(user_command)
            if not self._is_valid_url(start_url):
                raise TaskGenerationError("无法从用户命令或模型输出中得到有效 start_url")

        evaluation = task.get("evaluation")
        if not isinstance(evaluation, dict):
            evaluation = {}

        task["name"] = self._safe_task_name(str(task.get("name") or "generated_task"))
        task["start_url"] = start_url
        task["instruction"] = str(task["instruction"]).strip()
        task["max_steps"] = self._safe_max_steps(task.get("max_steps"))
        task["evaluation"] = {
            "suite": str(evaluation.get("suite") or "basic_web_tasks"),
            "task_type": str(evaluation.get("task_type") or "unknown"),
            "difficulty": str(evaluation.get("difficulty") or "medium"),
            "expected_result": str(evaluation.get("expected_result") or task["instruction"]),
            "success_criteria": self._safe_success_criteria(evaluation.get("success_criteria")),
        }
        if evaluation.get("notes"):
            task["evaluation"]["notes"] = str(evaluation["notes"])

        return task

    @staticmethod
    def _extract_url(text: str) -> str | None:
        match = re.search(r"https?://[^\s，。；;]+", text)
        return match.group(0) if match else None

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return url
        if not re.match(r"^https?://", url, flags=re.IGNORECASE):
            url = f"https://{url}"
        return url

    @staticmethod
    def _is_valid_url(url: str | None) -> bool:
        if not url:
            return False
        parsed_url = urlparse(url)
        return parsed_url.scheme in {"http", "https"} and bool(parsed_url.netloc)

    @staticmethod
    def _infer_start_url(user_command: str) -> str:
        command = user_command.lower()
        keyword_urls = [
            (("github", "仓库", "开源", "代码", "repo", "repository"), "https://github.com/"),
            (("豆瓣", "电影", "影评", "评分", "movie"), "https://movie.douban.com/explore"),
            (("天气", "气温", "降雨", "weather"), "https://www.weather.com.cn/"),
            (("知乎", "问答", "回答"), "https://www.zhihu.com/"),
            (("微博", "热搜"), "https://weibo.com/"),
            (("哔哩哔哩", "b站", "bilibili", "视频"), "https://www.bilibili.com/"),
            (("淘宝", "商品", "购物"), "https://www.taobao.com/"),
            (("京东", "jd.com"), "https://www.jd.com/"),
        ]

        for keywords, start_url in keyword_urls:
            if any(keyword in command for keyword in keywords):
                return start_url
        return "https://www.baidu.com/"

    @staticmethod
    def _safe_task_name(name: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
        return normalized or "generated_task"

    @staticmethod
    def _safe_max_steps(value: Any) -> int:
        try:
            max_steps = int(value)
        except (TypeError, ValueError):
            return 8
        return min(max(max_steps, 1), 20)

    @staticmethod
    def _safe_success_criteria(value: Any) -> list[str]:
        if isinstance(value, list):
            criteria = [str(item).strip() for item in value if str(item).strip()]
        else:
            criteria = []

        if criteria:
            return criteria
        return [
            "页面达到目标状态",
            "模型输出 finish",
            "最终状态为 success",
        ]


def save_generated_task(task: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    task_path = output_dir / f"{task['name']}.json"
    task_path.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
    return task_path
