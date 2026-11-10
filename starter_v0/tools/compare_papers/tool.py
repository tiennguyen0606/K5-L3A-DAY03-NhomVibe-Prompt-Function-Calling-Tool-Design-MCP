from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urlsplit

from tools._shared import err


CRITERIA = {
    "objective": "Mục tiêu",
    "method": "Phương pháp",
    "findings": "Kết quả chính",
    "limitations": "Hạn chế",
}
MISSING = "Chưa đủ thông tin"


def _cell(text: str) -> str:
    return re.sub(r"([\\|`*_[\]<>])", r"\\\1", " ".join(text.split()))


def compare_papers(
    items: list[dict[str, str]] | None = None,
    criteria: list[str] | None = None,
) -> dict[str, Any]:
    """Build a cited comparison table from details already extracted from papers."""
    if criteria is None:
        criteria = list(CRITERIA)
    try:
        if not isinstance(criteria, list) or not criteria or any(
            not isinstance(field, str) or field not in CRITERIA for field in criteria
        ):
            raise ValueError("criteria must be a non-empty list of supported fields")
        if len(set(criteria)) != len(criteria):
            raise ValueError("criteria must not contain duplicate fields")
        if not isinstance(items, list) or not 2 <= len(items) <= 5:
            raise ValueError("items must contain between 2 and 5 papers")

        header = ["Bài báo", *(CRITERIA[field] for field in criteria)]
        rows = [header, ["---"] * len(header)]
        seen_urls: set[str] = set()
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Paper {index} must be an object")
            title, url = item.get("title"), item.get("url")
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"Paper {index} needs a title")
            if not isinstance(url, str):
                raise ValueError(f"Paper {index} needs an HTTP(S) source URL")
            url = url.strip()
            parsed_url = urlsplit(url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
                raise ValueError(f"Paper {index} needs an HTTP(S) source URL")
            if url in seen_urls:
                raise ValueError(f"Paper {index} has a duplicate source URL")
            seen_urls.add(url)

            source = quote(url, safe=":/?#[]@!$&'*+,;=%")
            row = [f"[{_cell(title)}]({source})"]
            for field in criteria:
                value = item.get(field, "")
                if not isinstance(value, str):
                    raise ValueError(f"Paper {index}: {field} must be text")
                row.append(_cell(value) or MISSING)
            rows.append(row)
    except ValueError as exc:
        return err("compare_papers", exc)

    return {
        "tool": "compare_papers",
        "paper_count": len(seen_urls),
        "criteria": criteria,
        "markdown": "\n".join("| " + " | ".join(row) + " |" for row in rows),
    }
