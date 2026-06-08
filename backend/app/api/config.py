from fastapi import APIRouter

from app.services.model_config_service import ModelConfig, PublicModelConfig, model_config_service

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/model", response_model=PublicModelConfig)
def get_model_config() -> PublicModelConfig:
    return model_config_service.public()


@router.post("/model", response_model=PublicModelConfig)
def save_model_config(config: ModelConfig) -> PublicModelConfig:
    return model_config_service.save(config)
