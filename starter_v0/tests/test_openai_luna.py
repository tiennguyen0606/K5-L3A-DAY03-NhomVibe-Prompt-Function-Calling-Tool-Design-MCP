from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import openai

from providers.openai_provider import OpenAIProvider


def test_luna_requests_compatible_tool_call_parameters(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    function = SimpleNamespace(name="clarify", arguments='{"question":"Bạn muốn đọc bài nào?"}')
    response = SimpleNamespace(choices=[
        SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[SimpleNamespace(function=function)])),
    ])
    client = Mock()
    client.chat.completions.create.return_value = response
    monkeypatch.setattr(openai, "OpenAI", Mock(return_value=client))
    tools = [{"type": "function", "function": {"name": "clarify"}}]

    result = OpenAIProvider().complete(
        [{"role": "user", "content": "Đọc bài này"}], tools, model="gpt-5.6-luna",
    )

    request = client.chat.completions.create.call_args.kwargs
    assert request["model"] == "gpt-5.6-luna"
    assert request["reasoning_effort"] == "none"
    assert "temperature" not in request
    assert request["tools"] == tools
    assert result.tool_calls[0].name == "clarify"
    assert result.tool_calls[0].args == {"question": "Bạn muốn đọc bài nào?"}
