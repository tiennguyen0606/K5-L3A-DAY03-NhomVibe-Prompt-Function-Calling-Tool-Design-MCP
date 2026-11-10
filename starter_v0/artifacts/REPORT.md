# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

Baseline `v0` dùng Groq / `qwen/qwen3.8-27b`. Prompt và danh sách tool được
lưu theo bản gốc của commit `2469cd3` trong `artifacts/baselines/v0/`. Lần
chạy này để trống cấu hình Telegram vì base eval có tình huống thử yêu cầu
đăng bài. Chạy từ `starter_v0/` để tái lập baseline:

```bash
python run_eval.py --provider groq --model qwen/qwen3.8-27b --version v0 --suite base --eval-cases data/eval_base.json --system-prompt artifacts/baselines/v0/system_prompt.md --tools artifacts/baselines/v0/tools.yaml
```

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi với prompt và khai báo tool gốc | — | 71.4% | [Run JSON](../runs/v0_B_base_groq_20261110T105633299378.json) |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

**Kết quả v0:** 10/14 case được chấm đạt (71.4%), trên 20 case chạy. Routing 85.7%, arguments 71.4%, multi-turn 80.0%. Có 6 lỗi provider bị loại khỏi mẫu số điểm.

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R01_user_tweets_routing | provider_error | — | APIConnectionError | Kiểm tra lỗi API/model |
| R02_search_tweets_routing | provider_error | — | Groq từ chối lời gọi tool do định dạng hoặc tham số không hợp lệ. | Kiểm tra lỗi API/model |
| R03_web_news_routing | wrong_tool / wrong_arg_value | lookup({"max_results":8,"query":"AI news today highlights","timeframe":"day","topic":"news"}) | query: expected 'AI', got 'AI news today highlights' | Chưa sửa ở v0 |
| R08_out_of_scope | provider_error | — | APITimeoutError | Kiểm tra lỗi API/model |
| R10_missing_handle | missing_info / missing_tool_call | timeline({"limit":5,"screenname":"sama"}) | missing tool call clarify; extra tool call timeline | Chưa sửa ở v0 |
| R11_missing_url | missing_info / missing_tool_call | fetch({"url":"https://www.bloomberg.com/news/articles/2024-01-15/ai-advances-transform-industry"}) | missing tool call clarify; extra tool call fetch | Chưa sửa ở v0 |
| R12_confirm_before_send | provider_error | — | APITimeoutError | Kiểm tra lỗi API/model |
| R13_parallel_web_and_tweets | provider_error | — | Groq từ chối lời gọi tool do định dạng hoặc tham số không hợp lệ. | Kiểm tra lỗi API/model |
| M02_carryover_timeframe | wrong_arg_value / wrong_arg_value | lookup({"max_results":5,"query":"robotics news today","timeframe":"day","topic":"news"}) | query: expected 'robotics', got 'robotics news today' | Chưa sửa ở v0 |
| M03_correction_handle | provider_error | — | APITimeoutError | Kiểm tra lỗi API/model |

[CSV đủ 20 case](../analysis/v0_base_cases.csv). Run ghi nhận 1 lỗi khi thực thi tool; điểm routing và arguments do runner tính từ tool call, độc lập với việc tool có lấy được dữ liệu hay không.

**Thử lại lỗi mạng.** [Run bổ sung](../runs/v0-retry_B_base_groq_20261110T105817153621.json) chấm được cả 4 case, trong đó 3 case đạt. Case R12 gọi `send` và thiếu bước hỏi xác nhận `clarify`. Hai case khác trong run gốc vẫn bị Groq từ chối lời gọi tool. Gộp độ phủ của hai lần chạy có 13/18 case đạt trên số case chấm được. Bảng trên ghi điểm của run đầy đủ ban đầu.

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output |  |  |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
