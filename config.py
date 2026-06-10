from dataclasses import dataclass
import os

from app.config import get_settings, load_env_file


@dataclass(frozen=True)
class VLMConfig:
    api_key: str
    api_url: str
    model_name: str


def get_vlm_config(default_model: str = "qwen3.5-omni-plus-2026-03-15") -> VLMConfig:
    load_env_file()
    settings = get_settings(require_api_key=True)
    return VLMConfig(
        api_key=settings.vlm_api_key,
        api_url=settings.vlm_api_url,
        model_name=os.getenv("VLM_MODEL_NAME", default_model),
    )
