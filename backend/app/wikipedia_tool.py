import json
import re

from langchain_core.documents import Document
from langchain_core.tools import tool
import wikipedia

def _search_title(question: str) -> str:
    return re.sub(
        r"^(what is|what are|who is|who are|tell me about|can you explain)\s+",
        "",
        question.strip().rstrip("?"),
        flags=re.IGNORECASE,
    ) or question.strip()


def search_wikipedia(question: str) -> Document | None:
    search_query = _search_title(question)
    wikipedia.set_lang("en")
    try:
        titles = wikipedia.search(search_query, results=1)
        if not titles:
            return None
        page = wikipedia.page(titles[0], auto_suggest=False)
    except Exception:
        return None

    return Document(
        page_content=page.summary.strip(),
        metadata={
            "source": f"Wikipedia: {page.title}",
            "url": page.url,
            "title": page.title,
        },
    )


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia and return a concise article extract with its citation URL."""
    document = search_wikipedia(query)
    if document is None:
        return json.dumps({"found": False, "message": "No useful Wikipedia article was found."})
    return json.dumps(
        {
            "found": True,
            "title": document.metadata["title"],
            "url": document.metadata["url"],
            "extract": document.page_content,
        }
    )
