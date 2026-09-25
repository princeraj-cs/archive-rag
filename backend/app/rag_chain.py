from functools import lru_cache
import json

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI
from pydantic import Field

from app.config import get_settings
from app.ingest import has_vector_store, load_vector_store
from app.models import HistoryMessage
from app.wikipedia_tool import wikipedia_search

REFUSAL = "I don't have enough information in the provided documents to answer that."
GENERAL_FALLBACK_PREFIX = "The provided documents do not cover this directly."

RAG_SYSTEM_PROMPT = (
    "You answer questions using ONLY the context provided below, which comes from "
    "the user's uploaded documents. Conversation history is provided separately for "
    "resolving references (e.g. 'it', 'that one') — do not treat prior answers as "
    "additional context to draw facts from; only the Context section below is a valid "
    "source of facts.\n\n"
    "Rules:\n"
    "1. Base your answer strictly on the Context below. Do not use outside knowledge.\n"
    "2. Use the most relevant context even when it is brief or incomplete — a short "
    "relevant passage is still usable.\n"
    "3. If the context only partially answers the question, answer what it supports "
    "and briefly state what's missing. Do not fill gaps with assumptions.\n"
    f"4. If the retrieved context contains no information useful for answering the "
    f"question, respond with EXACTLY this text and nothing else: {REFUSAL}\n"
    "5. Do not soften, rephrase, or add to the refusal text in rule 4 — it must match "
    "exactly, with no leading or trailing commentary.\n"
    "6. Do not fabricate document names, page numbers, or quotes not present in the "
    "context.\n"
    "7. When context chunks conflict, point out the conflict rather than silently "
    "picking one.\n"
    "8. Be concise. Do not open with phrases like 'Based on the provided context...'.\n\n"
    "Context:\n{context}"
)

class ThresholdRetriever(BaseRetriever):
    vector_store: object
    relevance_threshold: float
    enabled_document_ids: list[str] = Field(default_factory=list)
    k: int = 4

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        search_filter = None
        if self.enabled_document_ids:
            search_filter = {"document_id": {"$in": self.enabled_document_ids}}
        scored_documents = self.vector_store.similarity_search_with_relevance_scores(
            query,
            k=self.k,
            filter=search_filter,
        )
        return [
            document
            for document, score in scored_documents
            if score >= self.relevance_threshold
        ]


@lru_cache
def get_rag_chain(enabled_document_ids: tuple[str, ...] = ()):
    settings = get_settings()
    vector_store = load_vector_store()
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                RAG_SYSTEM_PROMPT,
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Question: {input}"),
        ]
    )
    model = ChatOpenAI(
        model=settings.chat_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
    document_chain = create_stuff_documents_chain(model, prompt)
    retriever = ThresholdRetriever(
        vector_store=vector_store,
        relevance_threshold=settings.relevance_threshold,
        enabled_document_ids=list(enabled_document_ids),
    )
    return create_retrieval_chain(retriever, document_chain)


def clear_rag_cache() -> None:
    get_rag_chain.cache_clear()


def _to_langchain_history(history: list[HistoryMessage]) -> list[HumanMessage | AIMessage]:
    return [
        HumanMessage(content=message.content)
        if message.role == "user"
        else AIMessage(content=message.content)
        for message in history[-8:]
    ]


@lru_cache
def get_general_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.chat_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )


def _standalone_question(question: str, history: list[HistoryMessage]) -> str:
    if not history:
        return question
    response = get_general_model().invoke(
        [
            SystemMessage(
                content=(
                    "Rewrite the latest user question as a standalone search query. "
                    "Use the conversation only to resolve references such as 'it', "
                    "'that one', or 'the second item'. Return only the rewritten query."
                )
            ),
            *_to_langchain_history(history),
            HumanMessage(content=question),
        ]
    )
    return response.content.strip() or question


def _answer_with_wikipedia(question: str) -> tuple[str, list[Document]] | None:
    tool_model = get_general_model().bind_tools([wikipedia_search])
    messages = [
        SystemMessage(
            content=(
                "You are a general knowledge assistant. You must use the Wikipedia "
                "tool before answering. Clearly distinguish Wikipedia information "
                "from the user's uploaded documents."
            )
        ),
        HumanMessage(content=question),
    ]
    tool_request = tool_model.invoke(messages)
    if not tool_request.tool_calls:
        return None

    tool_messages = []
    wikipedia_documents = []
    for call in tool_request.tool_calls:
        tool_result = wikipedia_search.invoke(call["args"])
        payload = json.loads(tool_result)
        if payload.get("found"):
            wikipedia_documents.append(
                Document(
                    page_content=payload["extract"],
                    metadata={
                        "source": f"Wikipedia: {payload['title']}",
                        "title": payload["title"],
                        "url": payload["url"],
                    },
                )
            )
        tool_messages.append(
            ToolMessage(content=tool_result, tool_call_id=call["id"])
        )

    final_answer = tool_model.invoke(messages + [tool_request] + tool_messages)
    return final_answer.content, wikipedia_documents


def _answer_outside_documents(question: str) -> tuple[str, list[Document]]:
    settings = get_settings()
    if settings.wikipedia_enabled:
        wikipedia_result = _answer_with_wikipedia(question)
        if wikipedia_result:
            answer, documents = wikipedia_result
            return f"{GENERAL_FALLBACK_PREFIX} {answer}", documents

    fallback_prompt = (
        f"{GENERAL_FALLBACK_PREFIX} Answer the user's question using general knowledge "
        "if you can. Do not claim that this answer came from the uploaded documents. "
        "Be concise and clearly distinguish general knowledge from document evidence.\n\n"
        f"Question: {question}"
    )
    answer = get_general_model().invoke(fallback_prompt).content
    return f"{GENERAL_FALLBACK_PREFIX} {answer}", []


def answer_question(
    question: str,
    history: list[HistoryMessage] | None = None,
    enabled_document_ids: list[str] | None = None,
) -> tuple[str, list[Document]]:
    history = history or []
    if enabled_document_ids == []:
        return REFUSAL, []
    if not has_vector_store():
        if get_settings().allow_general_knowledge:
            return _answer_outside_documents(question)
        return REFUSAL, []

    selected_ids = tuple(sorted(enabled_document_ids or []))
    result = get_rag_chain(selected_ids).invoke(
        {
            "input": _standalone_question(question, history),
            "chat_history": _to_langchain_history(history),
        }
    )
    documents = result.get("context", [])
    answer = result["answer"]

    if not documents or answer.strip() == REFUSAL:
        if get_settings().allow_general_knowledge:
            return _answer_outside_documents(question)
        return REFUSAL, []  # no documents shown alongside a refusal

    return answer, documents
