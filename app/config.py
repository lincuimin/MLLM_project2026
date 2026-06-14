from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "outputs"
SCREENSHOT_DIR = OUTPUT_DIR / "screenshots"
LOG_DIR = OUTPUT_DIR / "logs"
EVALUATION_DIR = OUTPUT_DIR / "evaluations"
REPORT_DIR = OUTPUT_DIR / "reports"


@dataclass(frozen=True)
class Settings:
    vlm_api_key: str
    vlm_api_url: str
    vlm_model_name: str
    request_timeout_seconds: int
    max_steps: int
    browser_headless: bool
    browser_slow_mo_ms: int
    browser_channel: str
    browser_cdp_url: str
    browser_close_page_on_finish: bool
    viewport_width: int
    viewport_height: int
    observation_max_elements: int
    output_dir: Path
    screenshot_dir: Path
    log_dir: Path
    evaluation_dir: Path
    report_dir: Path


def load_env_file(env_path: Path | None = None) -> None:
    env_path = env_path or PROJECT_ROOT / ".env.example"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def get_settings(require_api_key: bool = True) -> Settings:
    load_env_file()

    api_key = os.getenv("VLM_API_KEY", "")
    if require_api_key and not api_key:
        raise RuntimeError(
            "未找到 VLM_API_KEY。请在 .env.example 中填入自己的模型 API Key。"
        )

    settings = Settings(
        vlm_api_key=api_key,
        vlm_api_url=os.getenv(
            "VLM_API_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        ),
        vlm_model_name=os.getenv("VLM_MODEL_NAME", "qwen3.5-omni-plus-2026-03-15"),
        request_timeout_seconds=_env_int("VLM_REQUEST_TIMEOUT_SECONDS", 40),
        max_steps=_env_int("AGENT_MAX_STEPS", 8),
        browser_headless=_env_bool("BROWSER_HEADLESS", False),
        browser_slow_mo_ms=_env_int("BROWSER_SLOW_MO_MS", 400),
        browser_channel=os.getenv("BROWSER_CHANNEL", "").strip(),
        browser_cdp_url=os.getenv("BROWSER_CDP_URL", "").strip(),
        browser_close_page_on_finish=_env_bool("BROWSER_CLOSE_PAGE_ON_FINISH", True),
        viewport_width=_env_int("BROWSER_VIEWPORT_WIDTH", 1280),
        viewport_height=_env_int("BROWSER_VIEWPORT_HEIGHT", 800),
        observation_max_elements=_env_int("OBSERVATION_MAX_ELEMENTS", 80),
        output_dir=OUTPUT_DIR,
        screenshot_dir=SCREENSHOT_DIR,
        log_dir=LOG_DIR,
        evaluation_dir=EVALUATION_DIR,
        report_dir=REPORT_DIR,
    )

    ensure_output_dirs(settings)
    return settings


def ensure_output_dirs(settings: Settings) -> None:
    settings.output_dir.mkdir(exist_ok=True)
    settings.screenshot_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    settings.evaluation_dir.mkdir(parents=True, exist_ok=True)
    settings.report_dir.mkdir(parents=True, exist_ok=True)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}
