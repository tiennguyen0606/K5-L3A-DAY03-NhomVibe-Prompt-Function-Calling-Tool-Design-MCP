from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from tools._shared import err


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty text")
    return " ".join(value.split())


def _excerpt(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    prefix = text[: limit - 1]
    return (prefix.rsplit(" ", 1)[0] or prefix) + "…"


def research_brief(
    topic: str = "",
    sources: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Summarize already-collected source snippets with numbered references."""
    try:
        topic = _required_text(topic, "topic")
        if not isinstance(sources, list) or not 1 <= len(sources) <= 6:
            raise ValueError("sources must contain between 1 and 6 researched sources")
        references: list[dict[str, str]] = []
        bullets: list[str] = []
        conclusion: list[str] = []
        seen_urls: set[str] = set()
        seen_claims: set[str] = set()
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                raise ValueError(f"Source {index} must be an object")
            title = _required_text(source.get("title"), f"Source {index} title")
            url = _required_text(source.get("url"), f"Source {index} url")
            snippet = _required_text(source.get("snippet"), f"Source {index} snippet")
            parsed_url = urlsplit(url)
            if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname or " " in url:
                raise ValueError(f"Source {index} needs an HTTP(S) source URL")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            references.append({"title": title, "url": url})
            citation = f"[{len(references)}]"
            bullets.append(f"{_excerpt(snippet, 320)} {citation}")
            lead = re.split(r"(?<=[.!?])\s+", snippet, maxsplit=1)[0]
            if len(conclusion) < 2 and lead.casefold() not in seen_claims:
                conclusion.append(f"{_excerpt(lead, 180)} {citation}")
                seen_claims.add(lead.casefold())
    except ValueError as exc:
        return err("research_brief", exc)

    return {
        "tool": "research_brief",
        "topic": topic,
        "conclusion": " ".join(conclusion),
        "bullets": bullets,
        "sources": references,
    }
