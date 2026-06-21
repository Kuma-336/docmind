import logging
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import get_settings

logger = logging.getLogger(__name__)

_instance: "EmbeddingManager | None" = None


class EmbeddingManager:
    def __init__(self):
        settings = get_settings()
        # 首次运行会从 HuggingFace Hub 下载模型（约 90MB），之后本地缓存
        self._embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info(f"EmbeddingManager 初始化，model={settings.EMBEDDING_MODEL}")

    @property
    def embeddings(self) -> HuggingFaceEmbeddings:
        return self._embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._embeddings.embed_query(text)


def get_embedder() -> EmbeddingManager:
    global _instance
    if _instance is None:
        _instance = EmbeddingManager()
    return _instance
