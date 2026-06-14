from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def collect_observation(page: Any, screenshot_path: Path, max_elements: int = 80) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            elements = _collect_interactive_elements(page, max_elements=max_elements)
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            _capture_annotated_screenshot(page, elements, screenshot_path)

            return {
                "url": page.url,
                "title": page.title(),
                "viewport": _viewport_size(page),
                "screenshot_path": str(screenshot_path),
                "screenshot_type": "annotated",
                "elements": elements,
            }
        except Exception as exc:
            last_error = exc
            if not _is_navigation_context_error(exc) or attempt == 2:
                break
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                page.wait_for_timeout(1000)
            time.sleep(0.2)

    if last_error:
        raise last_error
    raise RuntimeError("页面观察失败")


def compact_observation_for_prompt(observation: dict[str, Any]) -> dict[str, Any]:
    compact_elements = []
    for element in observation["elements"]:
        compact_elements.append(
            {
                "id": element["id"],
                "tag": element["tag"],
                "role": element.get("role"),
                "type": element.get("type"),
                "is_editable": element.get("is_editable"),
                "text": element.get("text"),
                "placeholder": element.get("placeholder"),
                "aria_label": element.get("aria_label"),
                "name": element.get("name"),
                "bbox": element.get("bbox"),
                "center": element.get("center"),
            }
        )

    return {
        "url": observation["url"],
        "title": observation["title"],
        "elements": compact_elements,
    }


def _capture_annotated_screenshot(page: Any, elements: list[dict[str, Any]], screenshot_path: Path) -> None:
    _draw_element_overlay(page, elements)
    try:
        page.screenshot(path=str(screenshot_path), full_page=False)
    finally:
        try:
            _clear_element_overlay(page)
        except Exception:
            pass


def _is_navigation_context_error(exc: Exception) -> bool:
    message = str(exc)
    return (
        "Execution context was destroyed" in message
        or "Cannot find context with specified id" in message
        or "most likely because of a navigation" in message
    )


def _viewport_size(page: Any) -> dict[str, int]:
    viewport = page.viewport_size
    if viewport:
        return {"width": viewport["width"], "height": viewport["height"]}

    return page.evaluate(
        """
        () => ({
          width: window.innerWidth,
          height: window.innerHeight
        })
        """
    )


def _collect_interactive_elements(page: Any, max_elements: int) -> list[dict[str, Any]]:
    return page.evaluate(
        """
        (maxElements) => {
          const selector = [
            'a[href]',
            'button',
            'input:not([type="hidden"])',
            'textarea',
            'select',
            'summary',
            '[contenteditable="true"]',
            '[role="button"]',
            '[role="link"]',
            '[role="textbox"]',
            '[role="combobox"]',
            '[role="menuitem"]',
            '[role="option"]',
            '[onclick]',
            '[tabindex]:not([tabindex="-1"])'
          ].join(',');

          const candidates = Array.from(document.querySelectorAll(selector));
          const seen = new Set();

          function isVisible(el) {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return (
              rect.width >= 4 &&
              rect.height >= 4 &&
              rect.bottom >= 0 &&
              rect.right >= 0 &&
              rect.top <= window.innerHeight &&
              rect.left <= window.innerWidth &&
              style.display !== 'none' &&
              style.visibility !== 'hidden' &&
              Number(style.opacity || '1') > 0
            );
          }

          function clean(value) {
            return String(value || '').replace(/\\s+/g, ' ').trim().slice(0, 140);
          }

          function labelText(el) {
            const labels = [];
            if (el.id) {
              document.querySelectorAll(`label[for="${CSS.escape(el.id)}"]`).forEach(label => {
                labels.push(label.innerText);
              });
            }
            if (el.closest('label')) {
              labels.push(el.closest('label').innerText);
            }
            return clean(labels.join(' '));
          }

          function labelOf(el) {
            return clean(
              el.getAttribute('aria-label') ||
              el.getAttribute('placeholder') ||
              labelText(el) ||
              el.innerText ||
              el.value ||
              el.getAttribute('title') ||
              el.name ||
              el.id
            );
          }

          function isEditable(el) {
            const tag = el.tagName.toLowerCase();
            const role = clean(el.getAttribute('role')).toLowerCase();
            const type = clean(el.getAttribute('type')).toLowerCase();
            return (
              tag === 'textarea' ||
              tag === 'select' ||
              el.isContentEditable ||
              role === 'textbox' ||
              role === 'combobox' ||
              (tag === 'input' && !['button', 'checkbox', 'radio', 'submit', 'reset', 'file'].includes(type))
            );
          }

          function isDisabled(el) {
            return Boolean(el.disabled) || clean(el.getAttribute('aria-disabled')).toLowerCase() === 'true';
          }

          const elements = [];
          for (const el of candidates) {
            if (elements.length >= maxElements) break;
            if (seen.has(el) || !isVisible(el) || isDisabled(el)) continue;
            seen.add(el);

            const rect = el.getBoundingClientRect();
            const agentId = `agent-el-${elements.length + 1}`;
            el.setAttribute('data-agent-id', agentId);
            const text = labelOf(el);

            elements.push({
              id: elements.length + 1,
              selector: `[data-agent-id="${agentId}"]`,
              tag: el.tagName.toLowerCase(),
              role: clean(el.getAttribute('role')),
              type: clean(el.getAttribute('type')),
              text,
              placeholder: clean(el.getAttribute('placeholder')),
              aria_label: clean(el.getAttribute('aria-label')),
              name: clean(el.getAttribute('name')),
              id_attr: clean(el.getAttribute('id')),
              href: clean(el.getAttribute('href')),
              is_editable: isEditable(el),
              overlay_label: `#${elements.length + 1}`,
              bbox: {
                x: Math.round(rect.x),
                y: Math.round(rect.y),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
              },
              x: Math.round(rect.x),
              y: Math.round(rect.y),
              width: Math.round(rect.width),
              height: Math.round(rect.height),
              center: {
                x: Math.round(rect.x + rect.width / 2),
                y: Math.round(rect.y + rect.height / 2)
              }
            });
          }

          return elements;
        }
        """,
        max_elements,
    )


def _draw_element_overlay(page: Any, elements: list[dict[str, Any]]) -> None:
    page.evaluate(
        """
        (elements) => {
          const oldOverlay = document.getElementById('__agent_element_overlay__');
          if (oldOverlay) oldOverlay.remove();

          const overlay = document.createElement('div');
          overlay.id = '__agent_element_overlay__';
          overlay.style.position = 'fixed';
          overlay.style.left = '0';
          overlay.style.top = '0';
          overlay.style.width = '100vw';
          overlay.style.height = '100vh';
          overlay.style.pointerEvents = 'none';
          overlay.style.zIndex = '2147483647';
          overlay.style.fontFamily = 'Arial, sans-serif';

          const colors = {
            editable: '#0f766e',
            link: '#2563eb',
            button: '#dc2626',
            other: '#7c3aed'
          };

          function colorFor(element) {
            if (element.is_editable) return colors.editable;
            if (element.tag === 'a' || element.role === 'link') return colors.link;
            if (element.tag === 'button' || element.role === 'button') return colors.button;
            return colors.other;
          }

          for (const element of elements) {
            const target = document.querySelector(element.selector);
            if (!target) continue;

            const rect = target.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) continue;

            const color = colorFor(element);
            const box = document.createElement('div');
            box.style.position = 'fixed';
            box.style.left = `${Math.max(0, rect.left)}px`;
            box.style.top = `${Math.max(0, rect.top)}px`;
            box.style.width = `${Math.max(1, rect.width)}px`;
            box.style.height = `${Math.max(1, rect.height)}px`;
            box.style.border = `2px solid ${color}`;
            box.style.boxShadow = '0 0 0 1px white, 0 0 0 3px rgba(0,0,0,0.25)';
            box.style.boxSizing = 'border-box';
            box.style.borderRadius = '3px';

            const label = document.createElement('div');
            label.textContent = `#${element.id}`;
            label.style.position = 'fixed';
            label.style.left = `${Math.max(0, rect.left)}px`;
            label.style.top = `${Math.max(0, rect.top - 20)}px`;
            label.style.padding = '2px 5px';
            label.style.borderRadius = '4px';
            label.style.background = color;
            label.style.color = '#fff';
            label.style.fontSize = '12px';
            label.style.fontWeight = '700';
            label.style.lineHeight = '14px';
            label.style.boxShadow = '0 1px 3px rgba(0,0,0,0.35)';

            overlay.appendChild(box);
            overlay.appendChild(label);
          }

          document.documentElement.appendChild(overlay);
        }
        """,
        elements,
    )


def _clear_element_overlay(page: Any) -> None:
    page.evaluate(
        """
        () => {
          const overlay = document.getElementById('__agent_element_overlay__');
          if (overlay) overlay.remove();
        }
        """
    )
