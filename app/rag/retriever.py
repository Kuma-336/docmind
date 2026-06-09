from typing import List
from langchain_core.documents import Document


def retrieve(query: str, top_k: int) -> List[Document]:
    """从 ChromaDB 检索与 query 最相关的 top_k 个文档片段。"""
    # TODO: 阶段二实现 — 初始化 Chroma vectorstore 并调用 similarity_search
    raise NotImplementedError
