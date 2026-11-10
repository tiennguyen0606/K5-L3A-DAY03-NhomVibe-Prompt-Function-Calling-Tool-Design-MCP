from __future__ import annotations

import pytest

from tools import TOOL_FUNCTIONS


brief = TOOL_FUNCTIONS["research_brief"]


@pytest.fixture
def sources() -> list[dict[str, str]]:
    return [
        {"title": "AgentBench", "url": "https://arxiv.org/abs/2308.03688",
         "snippet": "AgentBench đánh giá agent trong 8 môi trường. Các nhiệm vụ có tương tác."},
        {"title": "GAIA", "url": "https://arxiv.org/abs/2311.12983",
         "snippet": "GAIA dùng câu hỏi thực tế để đo khả năng sử dụng công cụ."},
    ]


def test_brief_summarizes_source_excerpts_and_numbers_citations(sources) -> None:
    result = brief(topic="Đánh giá AI agent", sources=sources)

    assert result["conclusion"] == (
        "AgentBench đánh giá agent trong 8 môi trường. [1] "
        "GAIA dùng câu hỏi thực tế để đo khả năng sử dụng công cụ. [2]"
    )
    assert result["bullets"][0].endswith("Các nhiệm vụ có tương tác. [1]")
    assert len(result["bullets"]) == 2
    assert result["sources"] == [
        {"title": source["title"], "url": source["url"]} for source in sources
    ]


def test_brief_keeps_first_occurrence_of_duplicate_url(sources) -> None:
    duplicate = {**sources[0], "snippet": "Ghi chú từ một lượt tìm trùng."}
    result = brief(topic="AI agent", sources=[sources[0], duplicate, sources[1]])

    assert len(result["sources"]) == 2
    assert result["bullets"][1].endswith("[2]")
    assert "tìm trùng" not in result["conclusion"]


def test_brief_requires_researched_sources() -> None:
    result = brief(topic="AI agent", sources=[])

    assert result["error"] == "ValueError"
    assert "sources" in result["message"]
    assert "conclusion" not in result


@pytest.mark.parametrize("invalid_source, field", [
    ({"url": "file:///example.pdf"}, "URL"),
    ({"snippet": "  "}, "snippet"),
])
def test_brief_rejects_source_without_valid_url_or_evidence(sources, invalid_source, field) -> None:
    result = brief(topic="AI agent", sources=[{**sources[0], **invalid_source}])

    assert result["error"] == "ValueError"
    assert field in result["message"]
