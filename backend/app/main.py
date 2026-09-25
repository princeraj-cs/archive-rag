from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import query, upload

app = FastAPI(title="RAG Q&A API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(upload.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
