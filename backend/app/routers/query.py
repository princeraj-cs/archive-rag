from fastapi import APIRouter, HTTPException

from app.models import QueryRequest, QueryResponse, SourceChunk
from app.rag_chain import answer_question

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_documents(request: QueryRequest) -> QueryResponse:
    try:
        answer, documents = answer_question(
            request.question,
            request.history,
            request.enabled_document_ids,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="The document index is not ready.") from exc

    sources = [
        SourceChunk(
            content=document.page_content,
            source=document.metadata.get("source", "unknown"),
            page=(document.metadata.get("page", 0) + 1)
            if document.metadata.get("page") is not None
            else None,
            url=document.metadata.get("url"),
        )
        for document in documents
    ]
    return QueryResponse(answer=answer, sources=sources)
