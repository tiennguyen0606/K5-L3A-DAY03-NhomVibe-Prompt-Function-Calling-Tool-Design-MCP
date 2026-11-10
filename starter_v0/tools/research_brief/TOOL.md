---
name: research_brief
track: core
kind: local_formatter
provider: local Python
requires_env: []
inputs: [topic, sources]
outputs: [topic, conclusion, bullets, sources]
side_effect: false
---
# research_brief

Gói các kết quả đã nghiên cứu thành bản tóm tắt có nguồn. Dùng sau
`lookup`, `fetch`, `papers`, `paper_text` hoặc khi người dùng đã đưa ghi chú
kèm link. Nếu chưa có tài liệu, dùng tool tìm hoặc đọc phù hợp trước.

Truyền chủ đề và 1–6 nguồn theo thứ tự ưu tiên. Mỗi nguồn có `title`, `url`
HTTP(S) và `snippet` chứa ý liên quan đã thu thập. Với output của tool tìm
hoặc đọc, lấy ý liên quan từ trường `summary` để tạo `snippet`. Không truyền
nguồn lỗi hoặc thiếu nội dung.

Tool chạy local. Nó lấy các ý ngắn trực tiếp từ snippet, gộp URL trùng và
trả về `conclusion`, `bullets` cùng `sources`. Ký hiệu `[n]` trỏ tới nguồn thứ
`n` trong danh sách. Trợ lý có thể diễn đạt lại cho rõ, giữ nguyên ý và
dẫn nguồn. Tool trả dictionary lỗi khi đầu vào không hợp lệ.
