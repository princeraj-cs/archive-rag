import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pypdf import PdfReader

from app.config import get_chroma_persist_dir, get_collection_name
from app.ingest import build_vector_store, delete_document_vectors
from app.manifest import add_entry, get_entry, load_manifest, remove_entry, save_manifest
from app.models import DeleteResponse, DocumentEntry, SourcesResponse
from app.rag_chain import clear_rag_cache

router = APIRouter()
ALLOWED_SUFFIXES = {".pdf", ".txt"}
logger = logging.getLogger(__name__)


def _source_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "source_docs"


def _page_count(path: Path) -> int:
    return len(PdfReader(path).pages) if path.suffix.lower() == ".pdf" else 1


@router.post("/upload", response_model=DocumentEntry)
def upload_document(file: UploadFile = File(...)) -> DocumentEntry:
    filename = Path(file.filename or "").name
    if Path(filename).suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")
    if any(entry.get("filename") == filename for entry in load_manifest()):
        raise HTTPException(
            status_code=409,
            detail="A document with this filename already exists. Delete it before uploading a replacement.",
        )

    document_id = uuid4().hex
    source_dir = _source_dir()
    source_dir.mkdir(parents=True, exist_ok=True)
    persist_dir = get_chroma_persist_dir()
    entry = None

    with tempfile.TemporaryDirectory(dir=source_dir.parent) as temp_dir:
        staged_path = Path(temp_dir) / filename
        with staged_path.open("wb") as output:
            shutil.copyfileobj(file.file, output, length=1024 * 1024)

        entry = {
            "id": document_id,
            "filename": filename,
            "status": "failed",
            "size_bytes": staged_path.stat().st_size,
            "page_count": 0,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        add_entry(entry)

        try:
            entry["page_count"] = _page_count(staged_path)
            build_vector_store(
                str(staged_path),
                persist_dir,
                get_collection_name(),
                document_id,
            )
            shutil.copy2(staged_path, source_dir / filename)
            entry["status"] = "indexed"
            save_manifest(
                [entry if item["id"] == document_id else item for item in load_manifest()]
            )
            clear_rag_cache()
            return DocumentEntry(**entry)
        except Exception as exc:
            try:
                delete_document_vectors(document_id)
            except Exception:
                logger.warning("Could not roll back vectors for %s", document_id, exc_info=True)
            logger.exception("Document indexing failed for %s", filename)
            raise HTTPException(status_code=500, detail="Document indexing failed.") from exc


@router.get("/sources", response_model=SourcesResponse)
def list_sources() -> SourcesResponse:
    return SourcesResponse(sources=[DocumentEntry(**entry) for entry in load_manifest()])


@router.delete("/sources/{document_id}", response_model=DeleteResponse)
def delete_source(document_id: str) -> DeleteResponse:
    entry = get_entry(document_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        if entry.get("status") == "indexed":
            delete_document_vectors(document_id)
        (_source_dir() / Path(entry["filename"]).name).unlink(missing_ok=True)
        remove_entry(document_id)
        clear_rag_cache()
    except Exception as exc:
        logger.exception("Document deletion failed for %s", document_id)
        raise HTTPException(status_code=500, detail="Document deletion failed.") from exc
    return DeleteResponse(status="deleted")
