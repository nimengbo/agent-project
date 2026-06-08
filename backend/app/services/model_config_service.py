from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class ModelConfig(BaseModel):
    api_key: str = Field(default="", repr=False)
    base_url: str = "https://api.deepseek.com"
    chat_model: str = "deepseek-chat"
    reasoner_model: str = "deepseek-reasoner"


class PublicModelConfig(BaseModel):
    configured: bool
    base_url: str
    chat_model: str
    reasoner_model: str
    api_key_preview: Optional[str] = None


class ModelConfigService:
    def __init__(self, config_path: str | None = None) -> None:
        self.path = self._resolve_config_path(config_path or settings.model_config_path)

    def _resolve_config_path(self, config_path: str) -> Path:
        path = Path(config_path)
        if path.is_absolute():
            return path
        return BACKEND_ROOT / path

    def load(self) -> ModelConfig:
        if not self.path.exists():
            return ModelConfig()
        return ModelConfig.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(self, config: ModelConfig) -> PublicModelConfig:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
        return self.public(config)

    def public(self, config: ModelConfig | None = None) -> PublicModelConfig:
        current = config or self.load()
        preview = None
        if current.api_key:
            preview = f"{current.api_key[:4]}...{current.api_key[-4:]}" if len(current.api_key) > 8 else "已配置"
        return PublicModelConfig(
            configured=bool(current.api_key and current.base_url),
            base_url=current.base_url,
            chat_model=current.chat_model,
            reasoner_model=current.reasoner_model,
            api_key_preview=preview,
        )


model_config_service = ModelConfigService()
