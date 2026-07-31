# Reflection - Trần Văn Tài

- Mã học viên: `2A202601339`
- Họ tên: Trần Văn Tài
- GitHub: `codecuatai` / `CodeCuaTai` / `ashura102938475`
- Phần phụ trách theo lịch sử commit: Thiết kế hệ thống và bản mẫu (System Design & Prototype), phát triển Frontend (React PDF Viewer, Chat & Citation navigation UX, HTML presentation slide generation), tích hợp Frontend-Backend.

## Dấu vết commit (kiểm chứng được bằng `git log`)

| Commit | Thời điểm | Nội dung |
|---|---|---|
| `8c6c6fa` | 30/07 15:42 | `feat(frontend)`: clickable citation chips navigate to source page |
| `fd85a80` | 30/07 18:20 | `fix(frontend)`: improve chat panel interactions |
| `ddd888a` | 30/07 19:15 | `style(frontend)`: polish chat panel visuals |
| `60b898d` | 30/07 20:00 | Merge pull request #7 (`feat/ui-citation-navigation`) |
| `6123880` | 30/07 20:30 | Merge pull request #8 (`feat/chat-panel-scroll-cleanup`) |
| `7b27c7a` | 31/07 01:45 | `fix`: resolve duplicate document switch messages in chat |
| `b778fc8` | 31/07 02:10 | `feat`: improve chat panel controls and resizable view |
| `8439b02` | 31/07 02:30 | Merge pull request #10 (`codex/fix-doc-switch-message`) |
| `29dbf38` | 31/07 03:00 | `fix`: shrink Chuyển TA button - muted style, smaller size, right-aligned |
| `4a2a594` | 31/07 03:15 | Merge pull request #11 (`fix/chuyen-ta-button-size`) |
| `1749802` | 31/07 04:00 | `fix`: scope clarification buttons re-send original query instead of hardcoded strings |
| `fe978e3` | 31/07 04:30 | Merge pull request #13 (`feat/scope-clarify-intent`) |
| Local Work | 31/07 10:13 | Chuyển đổi PDF presentation thành bản trình chiếu HTML tương tác đơn [slide/slide.html](../slide/slide.html) |

---

## 1. Phần tôi trực tiếp làm

Tôi phụ trách vai trò **System Design & Prototype / Frontend Lead**, chịu trách nhiệm trực tiếp thiết kế và triển khai toàn bộ lớp giao diện người dùng (User Interface) và luồng tương tác giữa học viên với hệ thống VLearn Smart Contextual Companion.

### A. Cơ chế Trích dẫn có thể Nhấp (Clickable Citation Navigation - `8c6c6fa`)
Trong sản phẩm AI Tutor cho học tập, câu trả lời không chỉ cần đúng mà phải **kiểm chứng được ngay lập tức**. Tôi triển khai tính năng khi backend trả về câu trả lời có chứa citation chip (ví dụ: `[Trang 3]`), người dùng nhấp vào thẻ này thì bộ xem PDF ở khung bên trái ([`App.jsx`](../codebase/frontend/src/App.jsx)) sẽ ngay lập tức tự động nhảy tới trang 3 của tài liệu slide hiện tại. Với các câu hỏi mở tra cứu từ nguồn ngoài, tôi thiết kế các nút liên kết trực tiếp tới Google Search và Google Scholar để học viên mở minh minh bạch nguồn tham khảo.

### B. Thiết kế Chat Panel & Trải nghiệm Tương tác (`fd85a80`, `ddd888a`, `b778fc8`)
- **Khung Chat linh hoạt:** Thiết kế ô trò chuyện có thể thu gọn hoặc mở rộng (resizable/collapsible panel), giúp học viên khi cần ôn tập slide có thể thu nhỏ ô chat để tập trung đọc toàn màn hình, và mở rộng khi cần hỏi chi tiết.
- **Bôi đen văn bản để hỏi AI (Selected Text Scope):** Xử lý sự kiện bôi đen một đoạn văn bản bất kỳ trên slide PDF để hệ thống tự động nhận diện phạm vi `selected_text` và gửi câu hỏi trực tiếp cho Tutor.
- **Cuộn mượt & Markdown Rendering:** Tự động cuộn xuống tin nhắn mới nhất, hiển thị đẹp mắt các đoạn định dạng Markdown, danh sách ý chính và các gợi ý hành động.

### C. Xây dựng bản Slide Trình chiếu HTML Tương tác (`slide/slide.html`)
- Tôi thực hiện trích xuất và chuyển đổi toàn bộ nội dung từ file PDF thuyết trình `Blue Purple Modern Illustration Artificial Intelligence Presentation.pdf` thành duy nhất 1 file trình chiếu HTML5 hoàn chỉnh tại [`slide/slide.html`](../slide/slide.html).
- Slide được thiết kế theo chủ đề AI Modern Blue-Purple chuẩn mực 16:9, bao gồm đầy đủ 8 slide: Trang bìa & danh sách nhóm, Bài toán Tutor nhìn hẹp & Thống kê 1,261 Q&A, User Job & Pain, Sơ đồ Pipeline 5 bước, Demo Prototype Flow, Biểu đồ Donut Chart SVG Đánh giá Golden Set, Impact & Next Step, và Bảng so sánh 2 bên (Current System vs Proposal).
- Tích hợp đầy đủ phím tắt điều hướng (`←`, `→`, `Space`), Modal xem tổng quan Grid (`O`), và chế độ Fullscreen (`F`).

---

## 2. AI đã hỗ trợ tôi như thế nào

Tôi sử dụng AI agent chủ yếu trong quá trình phát triển Frontend, sinh mã bố cục CSS, viết mã SVG cho biểu đồ, và xử lý các thao tác tích hợp giữa Frontend React và Backend FastAPI.

**Cách tôi kiểm chứng đầu ra:**
1. **Kiểm tra tương tác UI thực tế:** Không tin vào mã AI sinh ra cho đến khi chạy thử trực tiếp trên trình duyệt. Tôi kiểm tra từng tình huống nhấp vào citation chip `[Trang X]`, thử nghiệm bôi đen đoạn văn trên slide PDF để đảm bảo state `selectedText` được truyền đúng qua API.
2. **Kiểm tra tính tinh gọn của Giao diện:** Khi AI đề xuất thêm các đoạn tin nhắn hệ thống hoặc nút bấm lớn, tôi trực tiếp chạy thử trên màn hình thật để đánh giá trải nghiệm học viên. Nếu giao diện bị che khuất hoặc gây rối mắt, tôi chủ động gọt bỏ và tối ưu lại (như đợt sửa nút Chuyển TA ở commit `29dbf38`).
3. **Kiểm tra cú pháp & khả năng tương thích:** Chạy script kiểm tra HTML parser tự động đối với file `slide/slide.html` để đảm bảo file chạy độc lập mượt mà không bị lỗi thẻ hoặc xung đột CSS.

---

## 3. Một lần tôi phải đổi cách làm

**Sự cố / Feedback:**
Ở phiên bản đầu tiên, mỗi khi học viên thực hiện thao tác chuyển trang hoặc bấm chọn nút làm rõ phạm vi (scope clarification), hệ thống tự động bơm vào ô chat các đoạn tin nhắn thông báo rác ("Dưới đây là tóm tắt Trang 1..."). Việc này khiến ô chat bị ngập tin nhắn lặp lại, che mất câu trả lời quan trọng phía trên. Đồng thời, nút "Chuyển TA" hiển thị quá to và sặc sỡ, khiến người dùng nhầm tưởng đây là lựa chọn bắt buộc.

**Đổi quyết định:**
- **Loại bỏ tin nhắn chat rác (`06edbbf`):** Tôi quyết định gỡ bỏ hoàn toàn việc gửi tin nhắn chuyển tài liệu tự động vào ô chat log. Thay vào đó, tôi thiết kế một dòng Subtitle hiển thị vị trí trang hiện tại (Live Location Subtitle) nằm cố định bên dưới thanh tiêu đề, vừa minh bạch vị trí vừa giữ sạch lịch sử chat.
- **Tinh chỉnh nút Chuyển TA (`29dbf38`):** Thu nhỏ nút Chuyển TA về style muted, kích thước nhỏ và chuyển về vị trí góc phải bên dưới câu trả lời.
- **Fix nút Clarification (`1749802`):** Thay vì các nút chọn scope gửi về một chuỗi văn bản tóm tắt cứng, tôi điều chỉnh để khi học viên bấm nút, hệ thống sẽ gửi lại đúng câu hỏi gốc ban đầu kèm phạm vi đã được làm rõ.

---

## 4. Nếu có thêm một tuần

1. **Ưu tiên 1 — Visual Text Highlighting trên PDF Viewer:**
   - Hiện tại nhấp trích dẫn đã nhảy đúng trang PDF, nhưng nếu có thêm 1 tuần, tôi sẽ phát triển lớp hiển thị vùng highlight màu vàng trực tiếp lên các dòng văn bản được trích dẫn trên slide để học viên đối chiếu nhanh hơn nữa.

2. **Ưu tiên 2 — Tối ưu hóa giao diện Responsive cho thiết bị di động:**
   - Hoàn thiện chế độ hiển thị trên màn hình nhỏ (Mobile/Tablet) với ô chat dạng slide-up sheet từ dưới lên, giúp học viên học trên tablet hoặc điện thoại vẫn có trải nghiệm mượt mà.

3. **Ưu tiên 3 — Nâng cấp hiệu ứng cho bản trình chiếu HTML Slide (`slide/slide.html`):**
   - Bổ sung hiệu ứng chuyển slide 3D mượt mà, hỗ trợ chế độ Presenter View (xem ghi chú người diễn thuyết) để phục vụ cho buổi demo và chấm thi trực tiếp của nhóm.
