from typing import List
from pydantic import BaseModel


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    agent_path: List[str] = []
    session_id: str


class UploadResponse(BaseModel):
    file_id: str
    filename: str
    chunk_count: int
    status: str
