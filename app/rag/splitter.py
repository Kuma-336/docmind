import logging
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

logger = logging.getLogger(__name__)


class TextSplitter:
    def __init__(self):
        settings = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def split(self, documents: List[Document]) -> List[Document]:
        logger.info(f"开始切分，输入文档数: {len(documents)}")

        all_chunks: List[Document] = []
        for doc in documents:
            doc_chunks = self._splitter.split_documents([doc])
            total = len(doc_chunks)
            for idx, chunk in enumerate(doc_chunks):
                chunk.metadata = {
                    **doc.metadata,
                    "chunk_index": idx,
                    "chunk_total": total,
                }
                all_chunks.append(chunk)

        logger.info(f"切分完成，输出 chunk 数: {len(all_chunks)}")
        return all_chunks
