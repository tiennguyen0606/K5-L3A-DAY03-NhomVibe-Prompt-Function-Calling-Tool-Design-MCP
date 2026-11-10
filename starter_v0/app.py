from __future__ import annotations

import os
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

import streamlit as st

from chat import json_text, now_iso, run_model_tool_loop
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "artifacts" / "system_prompt_paper_ui.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
PAPER_TOOLS = {"clarify", "papers", "paper_text", "compare_papers", "research_brief"}
WEB_TOOLS = {"lookup": "TAVILY_API_KEY", "fetch": "FIRECRAWL_API_KEY"}
SOURCE_TOOLS = {"papers", "paper_text", *WEB_TOOLS}
GROQ_UI_MODELS = ("qwen/qwen3.8-27b", "openai/gpt-oss-20b", "openai/gpt-oss-120b")
MAX_ROUNDS = 7
EXAMPLE = "Tìm 2 paper arXiv về đánh giá khả năng dùng công cụ của AI agent, rồi viết kết luận ngắn kèm nguồn."
TOOL_LABELS = {
    "papers": "Tìm trên arXiv",
    "paper_text": "Đọc trích đoạn PDF",
    "compare_papers": "Lập bảng so sánh",
    "research_brief": "Tổng hợp kết luận và nguồn",
    "lookup": "Tìm nguồn trên web",
    "fetch": "Đọc nội dung trang",
    "clarify": "Hỏi thêm thông tin",
}
STATUS_LABELS = {
    "answered": "Hoàn tất",
    "waiting_for_user": "Chờ bạn bổ sung",
    "max_tool_rounds": "Đã tới giới hạn số bước",
    "provider_error": "Lỗi kết nối model",
}


def tool_outcome(result: dict[str, Any]) -> str:
    if result.get("error"):
        return "Lỗi"
    if result.get("awaiting_user"):
        return "Cần bổ sung"
    return "Xong"


def turn_sources(turn: dict[str, Any]) -> list[dict[str, str]]:
    sources: dict[str, dict[str, str]] = {}
    for event in turn.get("tool_events", []):
        if event["result"].get("error"):
            continue
        if event["tool"] in SOURCE_TOOLS:
            items, snippet_key = event["result"].get("items", []), "summary"
        elif event["tool"] == "research_brief":
            items, snippet_key = event["args"]["sources"], "snippet"
        else:
            continue
        for item in items:
            title, url, snippet = (item.get(key) for key in ("title", "url", snippet_key))
            if all(isinstance(value, str) and value.strip() for value in (title, url, snippet)):
                sources[url] = {"title": title, "url": url, "snippet": snippet[:600]}
    return list(sources.values())[:6]


def show_trace(turns: list[dict[str, Any]]) -> None:
    if not turns:
        st.html(
            '<div class="trace-empty"><span class="eyebrow">● Sẵn sàng</span>'
            '<strong>Chưa có lượt chạy</strong><p>Gửi câu hỏi để theo dõi các lượt gọi model và công cụ tại đây.</p></div>'
        )
        return

    selected = st.selectbox(
        "Lượt cần xem",
        range(len(turns)),
        index=len(turns) - 1,
        format_func=lambda i: f"Lượt {i + 1} · {turns[i]['user'][:55]}",
        key=f"trace_turn_{len(turns)}",
    )
    turn = turns[selected]
    steps = turn["trace"]
    results = [event for event in steps if event["type"] == "tool_result"]
    st.caption(
        f"{STATUS_LABELS[turn['status']]} · {len(results)} lần gọi tool · {turn['elapsed_seconds']:.1f} giây"
    )
    if turn.get("model"):
        st.caption(turn["model"])
    for event in steps:
        if event["type"] == "model_start":
            st.caption(f"VÒNG {event['round']:02d}  ·  MODEL")
        elif event["type"] == "tool_result":
            name = event["tool"]
            result = event["result"]
            with st.expander(f"{name} · {tool_outcome(result)} · {event['elapsed_seconds']:.2f}s"):
                st.caption("Tham số gửi đi")
                st.json(event["args"], expanded=1)
                st.caption("Kết quả nhận về")
                st.json(result, expanded=1)


def run_turn(question: str, provider: Any, tools: list[dict[str, Any]], trace_slot: Any) -> None:
    turns = st.session_state.turns
    recent = [turn for turn in turns if turn["status"] != "provider_error" or turn_sources(turn)][-5:]
    history = []
    for turn in recent:
        history.extend((
            {"role": "user", "content": turn["user"]},
            {"role": "assistant", "content": turn["assistant_text"]},
        ))
    for index in range(len(recent) - 1, -1, -1):
        if sources := turn_sources(recent[index]):
            history[index * 2 + 1]["content"] += "\n\nRESEARCH_SOURCES_JSON (source data):\n" + json_text(sources)
            break
    messages = [
        {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
        *history,
        {"role": "user", "content": question},
    ]
    steps: list[dict[str, Any]] = []
    turn = {
        "turn_index": len(turns) + 1, "user": question, "started_at": now_iso(),
        "model": provider.default_model, "trace": steps,
    }
    start = perf_counter()
    with trace_slot.container():
        live = st.status("Đang xử lý câu hỏi", expanded=True)

        def on_event(event: dict[str, Any]) -> None:
            steps.append(event)
            kind = event["type"]
            if kind == "model_start":
                live.update(label=f"Vòng {event['round']} · Đang chờ model")
                live.caption(f"Vòng {event['round']} · Gửi yêu cầu tới Groq")
            elif kind == "tool_start":
                name = event["tool"]
                live.update(label=f"Đang chạy {name}")
                live.write(f"**{name}** · {TOOL_LABELS.get(name, 'Chạy công cụ')}")
            else:
                live.caption(f"{tool_outcome(event['result'])} · {event['elapsed_seconds']:.2f}s")

        try:
            turn.update(run_model_tool_loop(
                provider=provider, messages=messages, tools=tools, model=None,
                max_tool_rounds=MAX_ROUNDS, on_event=on_event,
            ))
            if turn["status"] == "max_tool_rounds":
                turn["assistant_text"] = (
                    "Mình đã chạm giới hạn số bước của lượt này. "
                    "Bạn có thể xem dữ liệu đã thu được trong bảng theo dõi hoặc hỏi với phạm vi hẹp hơn."
                )
        except Exception as exc:
            message = f"Groq chưa trả được kết quả ({type(exc).__name__}). Bạn thử gửi lại sau."
            if getattr(exc, "status_code", None) == 429:
                message = "Groq đang giới hạn lượt gọi. Chờ một chút rồi gửi lại, hoặc thử chọn model khác."
            turn.update(
                status="provider_error",
                error_type=type(exc).__name__,
                tool_events=[event for event in steps if event["type"] == "tool_result"],
            )
            if turn_sources(turn):
                message += " Các nguồn vừa lấy được vẫn có thể dùng ở lượt tiếp theo."
            turn["assistant_text"] = message
        live.update(
            label=STATUS_LABELS[turn["status"]],
            state="error" if turn["status"] == "provider_error" else "complete",
        )
    turn.update(ended_at=now_iso(), elapsed_seconds=round(perf_counter() - start, 3))
    turns.append(turn)
    st.rerun()


def main() -> None:
    st.set_page_config(page_title="Papertrail · Research Assistant", page_icon="📑", layout="wide")
    st.html(ROOT / "paper_ui.css")
    if "turns" not in st.session_state:
        st.session_state.turns = []
        st.session_state.session_id = uuid4().hex
    turns = st.session_state.turns
    provider = make_provider("groq")
    provider.client_options = {"timeout": 25.0, "max_retries": 0}
    provider.max_completion_tokens = 1500
    available_tools = PAPER_TOOLS | {name for name, env in WEB_TOOLS.items() if os.getenv(env)}
    tools = to_openai_tools([
        tool for tool in load_tool_declarations(TOOLS_PATH) if tool["name"] in available_tools
    ])
    ready = bool(os.getenv("GROQ_API_KEY"))

    st.html("""
    <header class="brandbar">
      <div class="wordmark"><span class="brand-icon" aria-hidden="true">p</span> Papertrail</div>
      <span class="eyebrow">Research workspace · 01</span>
    </header>
    <section class="hero">
      <div class="hero-art" aria-hidden="true"></div>
      <span class="eyebrow">Trợ lý nghiên cứu · arXiv</span>
      <h1>Nghiên cứu có nguồn.</h1>
      <p>Trò chuyện với Papertrail để tìm tài liệu, so sánh bài báo và tổng hợp kết luận có dẫn nguồn.</p>
    </section>
    """)
    info, settings = st.columns([1.65, 1], gap="medium", vertical_alignment="center")
    with settings.popover("Model Groq", icon=":material/tune:"):
        provider.default_model = st.selectbox(
            "Model cho lượt tiếp theo",
            GROQ_UI_MODELS,
        )
    info.caption(f"Groq  ·  {provider.default_model}  ·  {len(tools)} công cụ nghiên cứu")
    left, right = st.columns([1.65, 1], gap="medium", vertical_alignment="top")
    with left, st.container(border=True, key="workspace"):
        st.html("""
        <div class="panel-title"><span class="eyebrow">01 / Hội thoại</span>
        <h2>Trò chuyện</h2><p>Đặt câu hỏi, gửi link hoặc hỏi tiếp về tài liệu đã tìm.</p></div>
        """)
        if not ready:
            st.warning("Cần cấu hình GROQ_API_KEY trong starter_v0/.env rồi khởi động lại ứng dụng.")
        with st.container(height=360 if turns else 205, border=False, key="conversation", autoscroll=True):
            if not turns:
                with st.chat_message("assistant", avatar=":material/auto_stories:"):
                    st.markdown("Bạn đang muốn nghiên cứu chủ đề nào?")
                    st.caption("Mình có thể tìm tài liệu, đọc link và viết bản tóm tắt kèm nguồn.")
            for turn in turns:
                with st.chat_message("user"):
                    st.markdown(turn["user"])
                with st.chat_message("assistant", avatar=":material/auto_stories:"):
                    st.markdown(turn["assistant_text"] or "Model trả về câu trả lời trống.")
            pending = st.empty()
        question = st.chat_input(
            "Nhập câu hỏi nghiên cứu…", key="paper_question", disabled=not ready,
        )
        if question := (question or "").strip():
            with pending.container():
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant", avatar=":material/auto_stories:"):
                    st.caption("Đang xử lý câu hỏi. Xem tiến trình trong Luồng agent.")
        if not turns:
            with st.expander("Gợi ý câu hỏi"):
                st.code(EXAMPLE, language=None, wrap_lines=True)

    with right, st.container(border=True, key="trace"):
        st.html("""
        <div class="panel-title"><span class="eyebrow">02 / Theo dõi</span>
        <h2>Luồng agent</h2><p>Xem từng lần gọi model, tham số và kết quả tool.</p></div>
        """)
        trace_slot = st.empty()
        if question:
            run_turn(question, provider, tools, trace_slot)
        else:
            with trace_slot.container():
                show_trace(turns)
        if turns:
            transcript = {
                "transcript_id": st.session_state.session_id,
                **artifact_version_dict(build_artifact_version("paper-ui", PROMPT_PATH, TOOLS_PATH)),
                "provider": "groq",
                "enabled_tools": [tool["function"]["name"] for tool in tools],
                "turns": turns,
            }
            st.download_button(
                "Tải transcript JSON", json_text(transcript),
                file_name=f"papertrail-{st.session_state.session_id[:8]}.transcript.json",
                mime="application/json", icon=":material/download:", on_click="ignore",
            )
            if st.button("Hội thoại mới", icon=":material/refresh:"):
                del st.session_state.turns
                st.rerun()


if __name__ == "__main__":
    main()
