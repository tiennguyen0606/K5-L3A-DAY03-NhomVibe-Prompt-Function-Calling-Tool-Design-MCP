from __future__ import annotations

from unittest.mock import Mock

import pytest

from chat import run_model_tool_loop
from providers.base import ModelResponse, ToolCall
from providers.groq_provider import fallback_after_tool_rejection
from tools import TOOL_FUNCTIONS


class GroqBadRequest(Exception):
    status_code = 400

    def __init__(self, code: str) -> None:
        self.code = code


def test_tool_rejection_retries_same_round_without_repeating_search(monkeypatch) -> None:
    search = Mock(return_value={"items": [
        {"title": "AgentBench", "url": "https://arxiv.org/abs/2308.03688", "summary": "Eight environments."}
    ]})
    monkeypatch.setitem(TOOL_FUNCTIONS, "papers", search)
    provider = Mock(default_model="qwen/qwen3.8-27b")
    provider.complete.side_effect = [
        ModelResponse(tool_calls=[ToolCall("papers", {"query": "AgentBench"})]),
        GroqBadRequest("tool_use_failed"),
        ModelResponse(tool_calls=[ToolCall("research_brief", {
            "topic": "AgentBench",
            "sources": [{"title": "AgentBench", "url": "https://arxiv.org/abs/2308.03688",
                         "snippet": "Eight environments."}],
        })]),
        ModelResponse(text="Kết luận có nguồn."),
    ]
    attempts = []
    complete = provider.complete

    def record(messages, *args, **kwargs):
        attempts.append((list(messages), kwargs["model"]))
        return complete(messages, *args, **kwargs)

    provider.complete = record
    events = []
    result = run_model_tool_loop(
        provider=provider, messages=[{"role": "user", "content": "Tìm và tóm tắt AgentBench."}],
        tools=[], model=None, max_tool_rounds=4, on_event=events.append,
        retry_model_on_error=fallback_after_tool_rejection,
    )

    assert result["status"] == "answered"
    assert [event["tool"] for event in result["tool_events"]] == ["papers", "research_brief"]
    search.assert_called_once_with(query="AgentBench")
    assert attempts[1][0] == attempts[2][0]
    assert attempts[2][1] == attempts[3][1] == "openai/gpt-oss-20b"
    assert [event["round"] for event in events if event["type"] == "model_retry"] == [2]


@pytest.mark.parametrize("codes, calls", [
    (["invalid_request_error"], 1),
    (["tool_use_failed", "tool_use_failed"], 2),
])
def test_fallback_does_not_repeat_bad_requests_indefinitely(codes, calls) -> None:
    provider = Mock(default_model="qwen/qwen3.8-27b")
    provider.complete.side_effect = [GroqBadRequest(code) for code in codes]

    with pytest.raises(GroqBadRequest):
        run_model_tool_loop(
            provider=provider, messages=[], tools=[], model=None, max_tool_rounds=4,
            retry_model_on_error=fallback_after_tool_rejection,
        )

    assert provider.complete.call_count == calls
