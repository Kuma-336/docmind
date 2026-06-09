from typing import List
from langchain_core.documents import Document


def split_documents(documents: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    """将文档切分为固定大小的 chunks。"""
    # TODO: 阶段二实现 — 使用 RecursiveCharacterTextSplitter
    raise NotImplementedError
