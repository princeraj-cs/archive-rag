# Archive

**A local, source-grounded Q&A workspace for the documents that matter.**

Archive lets you upload PDF and TXT files, index them locally, and ask questions with answers that keep their source trail attached. It combines a FastAPI backend, a React/Vite interface, OpenAI models, and a persistent Chroma vector store.

## What it does

- Upload and index PDF or TXT documents from the browser.
- Select which indexed documents should be used for a question.
- Retrieve relevant document chunks and show their source and page metadata.
- Preserve recent conversation history for follow-up questions.
- Fall back to Wikipedia or general knowledge when enabled and the documents do not cover a question.
- Keep the vector index and document manifest on disk for local development.

## How it works

```text
Browser (React + Vite)
				|
				v
FastAPI API  --->  OpenAI embeddings  --->  ChromaDB
				|
				+------>  Retrieval + context-only answer generation
				|
				+------>  Optional Wikipedia fallback
```

Uploaded files are split into overlapping chunks, embedded, and stored in Chroma. Each question retrieves the most relevant chunks from the selected documents. The answer includes the retrieved chunks as citations so the response can be checked against the source material.

## Requirements

- Python 3.11 or newer
- Node.js 18 or newer and npm
- An OpenAI API key

## Getting started

Run the backend and frontend in separate terminals.

### 1. Configure the backend

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

Install dependencies and create the environment file:

```bash
python -m pip install -r requirements.txt
copy .env.example .env
```

On macOS/Linux, use `cp .env.example .env` instead of `copy`.

Open `backend/.env` and set `OPENAI_API_KEY` to your key.

### 2. Start the API

Keep the working directory at `backend`:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. A quick health check is available at `http://localhost:8000/health`.

### 3. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`. Upload a document, select it in the sidebar, and ask a question.

To use a different API URL, set `VITE_API_URL` before starting the frontend:

```powershell
$env:VITE_API_URL = "http://localhost:8000"
npm run dev
```

## Configuration

Backend settings are read from `backend/.env`:

| Variable                  | Default                  | Purpose                                                  |
| ------------------------- | ------------------------ | -------------------------------------------------------- |
| `OPENAI_API_KEY`          | Required                 | OpenAI authentication                                    |
| `CHAT_MODEL`              | `gpt-4o-mini`            | Chat and fallback model                                  |
| `EMBEDDING_MODEL`         | `text-embedding-3-small` | Document embedding model                                 |
| `CHROMA_PERSIST_DIR`      | `./chroma_db`            | Persistent vector-store directory, relative to `backend` |
| `CHROMA_COLLECTION_NAME`  | `rag_documents`          | Chroma collection name                                   |
| `CHUNK_SIZE`              | `800`                    | Maximum characters per document chunk                    |
| `CHUNK_OVERLAP`           | `100`                    | Overlap between adjacent chunks                          |
| `RELEVANCE_THRESHOLD`     | `-0.5`                   | Minimum retrieval relevance score                        |
| `ALLOW_GENERAL_KNOWLEDGE` | `true`                   | Allow answers outside uploaded documents                 |
| `WIKIPEDIA_ENABLED`       | `true`                   | Use Wikipedia for the general-knowledge fallback         |

Set both fallback options to `false` to require every answer to come from the selected documents.

## API

| Method   | Endpoint                 | Description                                           |
| -------- | ------------------------ | ----------------------------------------------------- |
| `GET`    | `/health`                | Returns API health status                             |
| `POST`   | `/upload`                | Upload and index one PDF or TXT file                  |
| `GET`    | `/sources`               | List indexed documents                                |
| `DELETE` | `/sources/{document_id}` | Delete a document and its vectors                     |
| `POST`   | `/query`                 | Ask a question with optional history and document IDs |

FastAPI also exposes interactive API documentation at `http://localhost:8000/docs` while the backend is running.

## Tests and evaluation

Run the API tests from the `backend` directory:

```bash
python -m pytest tests -q
```

Run the lightweight evaluation suite from the same directory:

```bash
python -m eval.run_eval
```

Evaluation cases are stored in `backend/eval/test_questions.json`. Add questions and expected answer fragments from your own documents as the evaluation set grows. The runner expects each case to produce at least one source.

## Project layout

```text
backend/
	app/
		main.py              FastAPI application
		routers/             Upload and query endpoints
		ingest.py            Document loading, chunking, and vector storage
		rag_chain.py         Retrieval and answer generation
		wikipedia_tool.py    Optional Wikipedia fallback
	data/source_docs/      Uploaded source files
	eval/                  Evaluation runner and questions
	tests/                 API and manifest tests
frontend/
	src/
		App.jsx              Workspace layout and document controls
		components/          Chat and citation UI
		api/client.js        Backend requests
		store/chatStore.js   Local chat state
```

## Runtime data

By default, uploaded documents are stored in `backend/data/source_docs/`. Chroma vectors and the document manifest are stored in `backend/chroma_db/`. These directories are local application state and can be removed when you want to rebuild the index from scratch.

## Notes

- Only `.pdf` and `.txt` uploads are accepted.
- A filename cannot be uploaded twice until the existing document is deleted.
- CORS is currently configured for the local Vite origin `http://localhost:5173`.
