from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://interview:interview@localhost:5432/interview_assistant"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    minio_endpoint: str = "http://localhost:9000"
    model_config_path: str = "runtime/model_config.json"
    rag_collection_name: str = "interview_knowledge_base"
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 120
    rag_embedding_dimension: int = 384
    rag_use_qdrant: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
