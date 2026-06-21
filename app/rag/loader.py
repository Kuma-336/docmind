import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class DocumentLoader:
    def load(self, file_path: str) -> List[Document]:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ValueError(f"不支持的文件格式: '{ext}'。支持的格式: {supported}")

        logger.info(f"开始加载文件: {path.name}")

        if ext == ".pdf":
            loader = PyPDFLoader(str(path))
        else:
            loader = TextLoader(str(path), encoding="utf-8")

        documents = loader.load()

        loaded_at = datetime.now(timezone.utc).isoformat()
        for doc in documents:
            doc.metadata.update(
                {
                    "file_name": path.name,
                    "file_path": str(path.resolve()),
                    "file_type": ext.lstrip("."),
                    "loaded_at": loaded_at,
                }
            )

        logger.info(f"文件 {path.name} 加载完成，共 {len(documents)} 页/段")
        return documents
