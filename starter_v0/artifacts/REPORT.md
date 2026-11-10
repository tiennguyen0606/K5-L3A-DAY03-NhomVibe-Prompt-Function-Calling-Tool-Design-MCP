# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Nhóm Vibe
- Members: Nguyễn Hữu Tiến, Hồ Anh Dũng, Giáp Mạnh Tuyên
- Provider/model: OpenAI GPT-5.6 Luna (`gpt-5.6-luna`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Papertrail** là chatbot nghiên cứu có dẫn nguồn. Người dùng có thể tìm tài
liệu về nhiều chủ đề, đọc một trang web hoặc paper arXiv, dùng lại nguồn ở
lượt sau và nhận bản tóm tắt hoặc bảng so sánh. Bảng **Luồng agent** hiển thị
tool đang chạy, tham số, kết quả và cho tải transcript JSON.

**Link dùng thử:** [Papertrail demo](https://generated-collections-eye-gmbh.trycloudflare.com/).
Nhập mã demo do nhóm cung cấp. Đã thử qua trình duyệt và nhận phản hồi
từ Luna. Link tạm thời hoạt động khi máy demo còn chạy Streamlit và tunnel.
Để chạy lại trên máy nhóm, xem [hướng dẫn](../../README.md#chạy-giao-diện-papertrail).

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại khi thiếu thông tin cần thiết | Không |
| `lookup` | Tìm thông tin theo chủ đề trên web | Không |
| `fetch` | Đọc nội dung của một URL xác định | Không |
| `papers` | Tìm paper trên arXiv | Không |
| `paper_text` | Đọc trích đoạn PDF arXiv theo ID hoặc URL | Không |
| `compare_papers` | Tạo bảng so sánh từ ghi chú và link paper đã có | Có |
| `research_brief` | Tổng hợp kết luận, ý chính và danh sách nguồn từ tài liệu đã có | Có |

Đây là 7 tool dùng trong giao diện demo. Bộ base eval dùng cấu hình tích hợp
12 tool, có thêm các tác vụ theo dõi X, định dạng bản tin và kiểm tra xác nhận
trước khi gửi.

## A3. Câu hỏi mẫu để thử

1. “Tìm 2 nguồn web về tác dụng giảm nhiệt của cây xanh đô thị. Cho mình tiêu đề, link và một ghi chú ngắn cho mỗi nguồn.”
2. “Dùng lại hai nguồn ở câu trước để viết kết luận ngắn, vài ý chính và danh sách nguồn.”
3. “Tìm 2 paper arXiv về đánh giá khả năng dùng công cụ của AI agent.”
4. “Tóm tắt bài viết này giúp mình.” Agent cần hỏi lại URL nếu người dùng chưa gửi link.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Chuỗi so sánh dùng OpenAI GPT-5.6 Luna và 20 case cố định trong base eval. Mỗi vòng thay một artifact và giữ cùng danh sách 10 tool starter. Các cấu hình được lưu trong [baselines](baselines/) và gắn mã băm trong [version log](version_log.csv). Trong lúc chạy, cấu hình gửi Telegram để trống.

| Version | Changed artifact | Hypothesis | Case accuracy trước | Case accuracy sau | Routing | Multi-turn | Run file |
|---|---|---|---:|---:|---:|---:|---|
| v0 | baseline | Đo Luna bằng prompt và khai báo tool gốc | — | 65% (13/20) | 90% | 66.7% | [JSON](../runs/v0_B_base_openai_20261110T112711387427.json) |
| v1 | system_prompt.md | Kiểm tra điều kiện tiên quyết để hỏi lại đúng lúc | 65% | 55% (11/20) | 80% | 33.3% | [JSON](../runs/v1_B_base_openai_20261110T112845872228.json) |
| v2 | tools.yaml | Làm rõ khi dùng từng tool và quy ước tham số | 55% | 95% (19/20) | 100% | 100.0% | [JSON](../runs/v2_B_base_openai_20261110T113027839538.json) |
| v3 | system_prompt.md | Ưu tiên xác nhận trước khi gửi và quyết định theo lượt hiện tại | 95% | 100% (20/20) | 100% | 100.0% | [JSON](../runs/v3_B_base_openai_20261110T113228956753.json) |

v1 sửa hai case tự đoán thông tin nhưng làm model hỏi lại quá nhiều. v2 khắc phục lỗi tham số và dùng ngữ cảnh, còn lỗi xác nhận đăng bài. v3 sửa đúng lỗi còn lại.

[CSV phân tích theo case, v0–v3](../analysis/luna_base_runs.csv).

**Kiểm tra tích hợp.** Cấu hình hiện tại gồm prompt v3 và đủ 12 tool, trong đó
có `compare_papers` và `research_brief`. Chạy lại cùng bộ base bằng Luna đạt
**20/20**, không có lỗi provider. [Run JSON](../runs/v3-integrated_B_base_openai_20261110T113359904783.json).

## B2. Failure Analysis

### Baseline Luna

| Case | Kết quả thực tế ở v0 | Cách xử lý | Kết quả v3 |
|---|---|---|---|
| R03, R13, M02, M06 | Gọi lookup đúng nhưng thêm từ chỉ thời gian hoặc mở rộng query. | v2 tách chủ đề khỏi topic và timeframe. | Đạt 4/4 |
| R10, R11 | Gọi timeline hoặc fetch dù thiếu tài khoản hoặc URL. | v1 yêu cầu clarify khi thiếu đầu vào; v2 phân biệt với câu đã đủ thông tin. | Đạt 2/2 |
| R12 | Gọi clarify với response_type=text khi cần xác nhận yes_no. | v3 ưu tiên xác nhận ý định đăng trước khi thu thập phần còn thiếu. | Đạt |

## B3. Team Eval Cases

GPT-5.6 Luna đạt **10/10** với cấu hình v3 tích hợp. Bộ gồm 5 single-turn
và 5 multi-turn. Điểm đo tool và tham số ở lượt cần chấm. Với case tìm rồi
tổng hợp, bộ chấm kiểm tra bước đầu; transcript ở phần B4 ghi luồng thực tế.
[Run JSON](../runs/v3-integrated_B_group_openai_20261110T113759081708.json) ·
[CSV theo case](../analysis/luna_group_cases.csv) · [Bộ câu hỏi](../data/eval_group.json)

| Case ID | Lượt | Hành vi cần kiểm tra | Tool kỳ vọng | Kết quả |
|---|---|---|---|---|
| G_PAPER_COMPARE_FROM_NOTES | Đơn | Dùng ghi chú đã có và đúng bộ cột | `compare_papers` | PASS |
| G_RESEARCH_BRIEF_FROM_SOURCES | Nhiều | Tổng hợp từ hai nguồn ở lượt trước | `research_brief` | PASS |
| G_SEARCH_BEFORE_RESEARCH_BRIEF | Đơn | Tìm 2 paper trước khi tổng hợp | `papers` | PASS |
| G_WEB_NEWS_TIME_WINDOW | Đơn | Tìm tin tuần này với giới hạn 3 kết quả | `lookup` | PASS |
| G_MISSING_ARTICLE_URL | Đơn | Hỏi URL khi chưa xác định được bài | `clarify` | PASS |
| G_READ_ARXIV_PAGE_LIMIT | Đơn | Đọc đúng ID arXiv, giới hạn một trang | `paper_text` | PASS |
| G_COMPARE_REVISED_CRITERIA | Nhiều | Dùng tiêu chí mới thay cho tiêu chí cũ | `compare_papers` | PASS |
| G_FETCH_AFTER_CLARIFICATION | Nhiều | Đọc đúng URL vừa bổ sung | `fetch` | PASS |
| G_BRIEF_TOPIC_FROM_HISTORY | Nhiều | Giữ chủ đề và ghi chú ở lượt trước | `research_brief` | PASS |
| G_CANCEL_PUBLISHING | Nhiều | Tôn trọng yêu cầu hủy đăng | Không gọi tool | PASS |

## B4. Live Chat Evidence

Một phiên `chat.py` chạy thật trên GPT-5.6 Luna, với prompt v3 và 12 tool đã
tích hợp. Cả 3 lượt đều trả lời thành công. [Transcript JSON](../transcripts/v3-demo_openai_20261110T113846357084.transcript.json)

| Lượt | Yêu cầu | Tool đã gọi | Bằng chứng |
|---|---|---|---|
| 1 | Tìm hai nguồn về tác dụng giảm nhiệt của cây xanh đô thị | `lookup` × 2 | Trả tiêu đề, link và ghi chú cho hai nguồn từ kết quả tìm. |
| 2 | Dùng lại hai nguồn ở lượt 1 để tạo bản tổng hợp | `research_brief` | Có kết luận, hai ý chính và hai nguồn. Đối chiếu thủ công phát hiện một URL bị chèn thêm dấu gạch nối trong phần đường dẫn. |
| 3 | So sánh AgentBench và GAIA từ ghi chú có sẵn | `compare_papers` | Bảng có hai bài, cột mục tiêu và phương pháp, kèm đúng hai link arXiv. |

Sau khi thêm hướng dẫn sao chép URL nguyên văn, nhóm chạy một lượt đối
chiếu với hai URL chính xác. Cả tham số của `research_brief` và câu trả lời
đều giữ đúng hai URL trong lần thử này. [Transcript đối chiếu](../transcripts/v3-demo-source-check_openai_20261110T114514737977.transcript.json).

## B5. Kiểm thử và bằng chứng bổ sung

| Hạng mục | Bằng chứng | Kết quả | Giới hạn |
|---|---|---|---|
| UI Streamlit | [app.py](../app.py) | Chat nhiều lượt, theo dõi tool và tải transcript JSON | Phiên chia sẻ dùng mã demo. |
| Unit test | [compare_papers](../tests/test_tools_todo.py) · [research_brief](../tests/test_research_brief.py) | 85 pass, 14 skip; 4 test cho bảng so sánh và 5 lượt test cho bản tổng hợp | 14 stub của starter thuộc phần challenge. |
| arXiv | [Group run](../runs/v3-integrated_B_group_openai_20261110T113759081708.json) | `papers` và `paper_text` được chọn đúng và có kết quả tool. | Lượng nội dung đọc phụ thuộc trang và ký tự người dùng yêu cầu. |
| Xác nhận gửi | [Base run](../runs/v3-integrated_B_base_openai_20261110T113359904783.json) · [Group run](../runs/v3-integrated_B_group_openai_20261110T113759081708.json) | R12 hỏi xác nhận; G_CANCEL_PUBLISHING tôn trọng yêu cầu hủy. | Đo hành vi xác nhận và hủy trong eval. |

Unit test kiểm tra URL không hợp lệ, thiếu snippet và việc bỏ nguồn trùng.
Eval routing có thể đạt dù một tool trả lỗi khi thực thi, nên nhóm kiểm tra
cả `tool_results` trong JSON.

## B6. Reflection

- Prompt quyết định khi nào hỏi lại, xử lý yêu cầu mới dựa trên ngữ cảnh nào
  và khi nào cần xác nhận trước một hành động ghi. v1 cho thấy hỏi lại quá
  rộng có thể giảm điểm dù đã sửa lỗi tự đoán.
- Khai báo tool làm rõ ranh giới giữa tìm web, tìm bài trên X và đọc URL.
  Việc tách chủ đề, loại tin và khoảng thời gian thành các tham số riêng
  giúp v2 cải thiện rõ nhất.
- Đối chiếu transcript với kết quả tìm phát hiện một URL bị sửa đường dẫn
  khi model tái sử dụng nguồn. Bộ chấm tự động chỉ xác nhận tool và tham số
  ở lượt cần chấm, nên độ đầy đủ và chính xác của dẫn nguồn cần xem thủ công.
- Một hướng cải thiện tiếp là đánh giá chất lượng bằng chứng theo từng ý
  trong bản tổng hợp và xử lý ổn định khi nguồn trả lỗi hoặc thiếu dữ liệu.

## B7. Small Local Model Challenge (bonus)

Các kết quả trong báo cáo này dùng model cloud. Mục Ollama là bonus riêng.
