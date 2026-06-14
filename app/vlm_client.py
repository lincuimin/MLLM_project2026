from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

import requests

from .config import Settings
from .observation import compact_observation_for_prompt


class VLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def decide(
        self,
        task_instruction: str,
        observation: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        prompt = self._build_prompt(task_instruction, observation, history)
        payload = {
            "model": self.settings.vlm_model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self._image_data_url(observation["screenshot_path"])
                            },
                        },
                    ],
                }
            ],
            "max_tokens": 500,
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
        return self._extract_json(content)

    def _build_prompt(
        self,
        task_instruction: str,
        observation: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> str:
        compact_observation = compact_observation_for_prompt(observation)
        recent_history = history[-5:]

        return f"""
你是一个浏览器自动化 Agent，需要根据用户任务、网页截图和可操作元素列表选择下一步动作。
截图中已经用彩色方框标出了可操作元素，并用 #1、#2 这样的编号对应元素列表中的 id。

用户任务:
{task_instruction}

当前页面信息:
{json.dumps(compact_observation, ensure_ascii=False, indent=2)}

最近执行历史:
{json.dumps(recent_history, ensure_ascii=False, indent=2)}

只能输出一个 JSON 对象，不要输出 Markdown，不要解释。

可用动作:
1. 点击元素: {{"action": "click", "element_id": 1}}
2. 输入文本: {{"action": "type", "element_id": 1, "text": "要输入的文本"}}
3. 按键: {{"action": "press", "key": "Enter"}}
4. 滚动: {{"action": "scroll", "direction": "down"}}
5. 等待: {{"action": "wait", "seconds": 1}}
6. 完成任务: {{"action": "finish", "answer": "最终结果或完成说明"}}

规则:
- 必须优先使用元素列表中的 element_id，不要自己编造页面坐标。
- 如果搜索框、按钮或链接出现在截图上，请选择对应编号。
- 如果当前视口没有目标元素，可以输出 scroll 或 wait。
- 只有任务已经完成时才输出 finish。
""".strip()

    @staticmethod
    def _image_data_url(image_path: str) -> str:
        image_bytes = Path(image_path).read_bytes()
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?", "", content, flags=re.IGNORECASE).strip()
            content = re.sub(r"```$", "", content).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", content):
            try:
                parsed, _ = decoder.raw_decode(content[match.start() :])
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, dict):
                return parsed

        return {"action": "error", "reason": "模型没有输出 JSON"}
