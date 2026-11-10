---
name: compare_papers
track: core
kind: local_formatter
provider: local Python
requires_env: []
inputs: [items, criteria]
outputs: [paper_count, criteria, markdown]
side_effect: false
---
# compare_papers

Builds a Markdown comparison table for 2–5 papers from notes the agent has
already gathered. Each paper needs a title and a distinct HTTP(S) source URL.

Pass short, evidence-backed notes under `objective`, `method`, `findings`, and
`limitations`. Use `criteria` to choose and order the columns, or omit it for
all four. Leave unverified fields empty or omit them. The table marks these
cells as “Chưa đủ thông tin”. Invalid arguments return an error dictionary.

For a literature review, use `papers` to find candidates, `paper_text` to read
the relevant excerpts, then `compare_papers` once the notes are ready. The model
can propose research directions from that evidence and cite the papers it used.
If users already provide the notes and URLs, call `compare_papers` directly.
The tool only formats the input, so extraction and evidence assessment belong
to the model. A table entry does not imply that the whole paper was read.

Demo: “Tìm 2 bài arXiv về đánh giá AI agent. So sánh phương pháp và hạn chế có
bằng chứng, rồi gợi ý một câu hỏi nghiên cứu tiếp theo kèm nguồn.”
