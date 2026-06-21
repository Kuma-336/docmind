from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "DocMind"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""          # 留空时使用官方地址；填 DeepSeek/其他兼容接口
    OPENAI_MODEL: str = "deepseek-chat"

    # 本地 HuggingFace 嵌入模型（不消耗 API 额度）
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"

    TAVILY_API_KEY: str = ""

    CHROMA_PERSIST_DIR: str = "./data/chroma"
    UPLOAD_DIR: str = "./data/uploads"

    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RETRIEVER_TOP_K: int = 5
    RETRIEVER_SCORE_THRESHOLD: float = 0.5  # 相关度低于此值的结果将被过滤（0~1，越大越严格）

    MAX_UPLOAD_SIZE_MB: int = 20
    SESSION_DB_PATH: str = "./data/sessions.db"
    SESSION_HISTORY_LIMIT: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
