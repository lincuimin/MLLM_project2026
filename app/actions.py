from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ALLOWED_ACTIONS = {"click", "type", "press", "scroll", "wait", "finish"}


@dataclass
class ActionResult:
    success: bool
    message: str
    should_finish: bool = False
    answer: str | None = None


def normalize_action(raw_action: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_action, dict):
        return {"action": "error", "reason": "模型输出不是 JSON 对象"}

    action = str(raw_action.get("action", "")).strip().lower()
    if action == "stop":
        action = "finish"
    if action == "input":
        action = "type"

    if "element_id" not in raw_action:
        for alias in ("elementId", "target_id", "targetId", "id"):
            if alias in raw_action:
                raw_action["element_id"] = raw_action[alias]
                break

    normalized = dict(raw_action)
    normalized["action"] = action
    return normalized


def execute_action(page: Any, action: dict[str, Any], elements: list[dict[str, Any]]) -> ActionResult:
    action_name = action.get("action")

    if action_name == "finish":
        answer = str(action.get("answer") or action.get("reason") or "任务已完成")
        return ActionResult(True, "模型判断任务结束", should_finish=True, answer=answer)

    if action_name not in ALLOWED_ACTIONS:
        return ActionResult(False, f"不支持的动作: {action_name}")

    try:
        if action_name == "click":
            element = _find_element(elements, action.get("element_id"))
            _click_element(page, element)
            return ActionResult(True, f"点击元素 #{element['id']}: {_element_label(element)}")

        if action_name == "type":
            element = _find_element(elements, action.get("element_id"))
            text = str(action.get("text", ""))
            if not text:
                return ActionResult(False, "type 动作缺少 text")

            locator = page.locator(element["selector"]).first
            try:
                locator.click(timeout=8000)
                locator.fill(text, timeout=8000)
            except Exception:
                _click_element(page, element)
                page.keyboard.press("Control+A")
                page.keyboard.insert_text(text)
            return ActionResult(True, f"向元素 #{element['id']} 输入: {text}")

        if action_name == "press":
            key = str(action.get("key", "Enter"))
            page.keyboard.press(key)
            return ActionResult(True, f"按下键盘: {key}")

        if action_name == "scroll":
            direction = str(action.get("direction", "down")).lower()
            distance = int(action.get("distance", 700))
            delta_y = -abs(distance) if direction == "up" else abs(distance)
            page.mouse.wheel(0, delta_y)
            return ActionResult(True, f"页面滚动: {direction}")

        if action_name == "wait":
            seconds = float(action.get("seconds", 1))
            seconds = min(max(seconds, 0.2), 5.0)
            page.wait_for_timeout(int(seconds * 1000))
            return ActionResult(True, f"等待 {seconds:.1f} 秒")

    except Exception as exc:
        return ActionResult(False, f"动作执行失败: {exc}")

    return ActionResult(False, f"动作未执行: {action_name}")


def _find_element(elements: list[dict[str, Any]], element_id: Any) -> dict[str, Any]:
    try:
        wanted_id = int(element_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("动作缺少有效的 element_id") from exc

    for element in elements:
        if element["id"] == wanted_id:
            return element

    raise ValueError(f"当前页面没有 element_id={wanted_id} 的可操作元素")


def _click_element(page: Any, element: dict[str, Any]) -> None:
    try:
        page.locator(element["selector"]).first.click(timeout=8000)
        return
    except Exception:
        center = element.get("center")
        if not center:
            raise

        page.mouse.click(center["x"], center["y"])


def _element_label(element: dict[str, Any]) -> str:
    return (
        element.get("text")
        or element.get("aria_label")
        or element.get("placeholder")
        or element.get("tag")
        or "未命名元素"
    )
