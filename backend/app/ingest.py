from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_chroma_persist_dir, get_collection_name, get_settings


def _embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )


def build_vector_store(
    file_path: str,
    persist_dir: Path,
    collection_name: str,
    document_id: str,
) -> Chroma:
    settings = get_settings()
    source_path = Path(file_path)
    persist_dir.mkdir(parents=True, exist_ok=True)
    loader = (
        PyPDFLoader(str(source_path))
        if source_path.suffix.lower() == ".pdf"
        else TextLoader(str(source_path), encoding="utf-8")
    )
    documents = loader.load()

    if not documents:
        raise ValueError("No PDF or TXT documents were found to index.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata.update(
            {
                "source": source_path.name,
                "document_id": document_id,
            }
        )
    embeddings = _embeddings()
    vector_store = Chroma(
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
        collection_name=collection_name,
    )
    vector_store.add_documents(chunks)
    return vector_store


def load_vector_store() -> Chroma:
    return Chroma(
        persist_directory=str(get_chroma_persist_dir()),
        embedding_function=_embeddings(),
        collection_name=get_collection_name(),
    )


def has_vector_store() -> bool:
    try:
        return load_vector_store()._collection.count() > 0
    except Exception:
        return False


def delete_document_vectors(document_id: str) -> None:
    load_vector_store().delete(where={"document_id": document_id})
