from typing import Literal

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)
    enabled_document_ids: list[str] | None = None


class SourceChunk(BaseModel):
    content: str
    source: str
    page: int | None = None
    url: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class DocumentEntry(BaseModel):
    id: str
    filename: str
    status: Literal["indexed", "failed"]
    size_bytes: int
    page_count: int
    uploaded_at: str


class SourcesResponse(BaseModel):
    sources: list[DocumentEntry]


class DeleteResponse(BaseModel):
    status: str
