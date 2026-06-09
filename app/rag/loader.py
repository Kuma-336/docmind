from pathlib import Path
from typing import List
from langchain_core.documents import Document


def load_document(file_path: str | Path) -> List[Document]:
    """加载文档，支持 PDF 和纯文本格式。"""
    # TODO: 阶段二实现 — 使用 PyPDFLoader / TextLoader
    raise NotImplementedError
