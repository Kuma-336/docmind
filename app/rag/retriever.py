import logging
from typing import List, Optional

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.config import get_settings
from app.rag.embedder import get_embedder

logger = logging.getLogger(__name__)

_instance: "VectorStoreManager | None" = None


class VectorStoreManager:
    def __init__(self):
        settings = get_settings()
        embedder = get_embedder()
        self._vectorstore = Chroma(
            collection_name="docmind",
            persist_directory=settings.CHROMA_PERSIST_DIR,
            embedding_function=embedder.embeddings,
        )
        logger.info(f"VectorStoreManager 初始化，persist_dir={settings.CHROMA_PERSIST_DIR}")

    def add_documents(self, documents: List[Document], file_id: str) -> int:
        for doc in documents:
            doc.metadata["file_id"] = file_id
        self._vectorstore.add_documents(documents)
        logger.info(f"写入 {len(documents)} 个 chunk，file_id={file_id}")
        return len(documents)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        settings = get_settings()
        if top_k is None:
            top_k = settings.RETRIEVER_TOP_K
        threshold = settings.RETRIEVER_SCORE_THRESHOLD
        scored = self._vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
        results = [doc for doc, score in scored if score >= threshold]
        logger.info(
            f"检索 '{query[:30]}' 返回 {len(results)} 条结果"
            f"（阈值={threshold}，候选={len(scored)}条，"
            f"分数范围=[{min((s for _, s in scored), default=0):.3f}, {max((s for _, s in scored), default=0):.3f}]）"
        )
        return results

    def delete_by_file_id(self, file_id: str) -> None:
        collection = self._vectorstore._collection
        result = collection.get(where={"file_id": file_id})
        ids = result.get("ids", [])
        if ids:
            self._vectorstore.delete(ids=ids)
            logger.info(f"删除 {len(ids)} 个 chunk，file_id={file_id}")
        else:
            logger.info(f"未找到 file_id={file_id} 的 chunk，无需删除")


def get_vector_store() -> VectorStoreManager:
    global _instance
    if _instance is None:
        _instance = VectorStoreManager()
    return _instance
