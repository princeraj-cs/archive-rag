from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app.main import app
from app import manifest
from app.routers import query as query_router


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_rejects_empty_question() -> None:
    response = client.post("/query", json={"question": ""})

    assert response.status_code == 422


def test_query_returns_answer_and_source(monkeypatch) -> None:
    document = Document(
        page_content="The meetup budget is Rs. 8000.",
        metadata={"source": "notes.pdf", "page": 0},
    )
    monkeypatch.setattr(
        query_router,
        "answer_question",
        lambda question, history, enabled_document_ids: (
            "The meetup budget is Rs. 8000.",
            [document],
        ),
    )

    response = client.post("/query", json={"question": "What is the budget?"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The meetup budget is Rs. 8000.",
        "sources": [
            {
                "content": "The meetup budget is Rs. 8000.",
                "source": "notes.pdf",
                "page": 1,
                "url": None,
            }
        ],
    }


def test_query_forwards_conversation_history(monkeypatch) -> None:
    received = {}

    def fake_answer(question, history, enabled_document_ids):
        received["question"] = question
        received["history"] = history
        received["enabled_document_ids"] = enabled_document_ids
        return "Follow-up answer", []

    monkeypatch.setattr(query_router, "answer_question", fake_answer)
    response = client.post(
        "/query",
        json={
            "question": "What about the second one?",
            "history": [
                {"role": "user", "content": "List the first two items."},
                {"role": "assistant", "content": "The first item is A."},
            ],
        },
    )

    assert response.status_code == 200
    assert received["question"] == "What about the second one?"
    assert [message.role for message in received["history"]] == ["user", "assistant"]
    assert received["enabled_document_ids"] is None


def test_upload_rejects_unsupported_file() -> None:
    response = client.post(
        "/upload",
        files={"file": ("notes.docx", b"not supported", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF and TXT files are supported."


def test_manifest_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(manifest, "get_chroma_persist_dir", lambda: tmp_path)
    entry = {"id": "doc-1", "filename": "notes.txt", "status": "indexed"}

    manifest.add_entry(entry)

    assert manifest.get_entry("doc-1") == entry
    assert manifest.remove_entry("doc-1") == entry
    assert manifest.load_manifest() == []
