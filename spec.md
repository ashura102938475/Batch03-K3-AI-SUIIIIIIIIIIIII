# AI SPEC — VLearn Smart Contextual Companion · Nhóm Batch03-K3-AI-SUIIIIIIIIIIIII
Hướng: [x] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở  
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

---

## §1. User & Job

- **Job executor + workflow:**  
  **Học viên K3 đang học hoặc ôn lại tài liệu trên VLearn** (đặc biệt trong flow: đọc slide bài giảng, ôn tập trước quiz/lab, hoặc xem lại nội dung buổi học đã qua).  
  *Workflow:* Học viên mở VLearn -> xem slide/tài liệu -> cần nắm nhanh ý chính hoặc giải thích đoạn chưa hiểu -> hỏi VLearn Tutor ở panel bên phải -> xem câu trả lời kèm trích dẫn để học tiếp hoặc ghi chú.

- **Core JTBD:**  
  > Nắm nhanh nội dung chính của một slide, một tài liệu hoặc một buổi học để biết phần nào cần học, cần note, hoặc cần hỏi thêm.  
  *(Job này hoàn toàn tồn tại độc lập với AI: học viên vốn đã phải tự lật từng trang slide, xem lại video, hỏi bạn học hoặc nhờ TA).*

- **Problem statement:**  
  > Học viên đang hỏi/tóm tắt nội dung học liệu trên VLearn nhưng Tutor hiện tại thường chỉ hiểu đoạn bôi đen hoặc trang đang mở, không nhận ra phạm vi rộng hơn (tài liệu hoặc buổi học). Điều này khiến câu trả lời thiếu context, citation rỗng (46.2%) hoặc báo "không tìm thấy / không truy cập được" (55.8% lượt summary broad-scope); học viên phải tự lật lại tài liệu, hỏi lặp lại nhiều lần hoặc chuyển sang công cụ khác.

- **Evidence (chuẩn B — Data Mining & Turn IDs từ `data/vlearn-pack/chatlog/`):**  
  - **Quy mô data:** `1,261` lượt hỏi-đáp student-tutor, `369` users, `585` conversations.
  - **Số liệu mining chính:**
    - `156/1,261` lượt hỏi (`12.4%`) có nhu cầu summary / tổng hợp / ý chính / keyword / note (đến từ 111 users).
    - `62` lượt hỏi summary ở phạm vi broad-scope (toàn bài, toàn buổi, file tài liệu, slide day).
    - `87/156` lượt summary (`55.8%`) nhận câu trả lời kiểu *"không tìm thấy / không truy cập được / rất tiếc"*.
    - `101/156` lượt summary (`64.7%`) có citation rỗng (`citations == []`).
    - Tổng thể toàn bộ chatlog: `582/1,261` lượt Tutor trả về citation rỗng (`46.2%`).
    - Với các câu hỏi summary có thông tin trang context trong prompt: chỉ `16/155` lượt (`10.3%`) cite đúng trang context; `100/155` lượt (`64.5%`) không cite bất kỳ nguồn nào.
    - Rating tín hiệu phụ: Summary có rating: `10/14` downvote (`71.4%`); No-access reply có rating: `20/20` downvote (`100%`); Citation rỗng: `29/41` downvote (`70.7%`).
  - **≥5 ví dụ nguyên văn ngắn + Turn ID minh họa:**
    1. **`T0408`** (Broad summary fail): Student: *"tóm tắt các chủ đề chính của slide day05..."* -> Tutor: *"không thể tìm thấy file/nội dung chi tiết"*.
    2. **`T1164`** (Scope limit fail): Student: *"tóm tắt cho t tất cả từ trang 1 đến trang 44 bài này học về gì"* -> Tutor: *"không thể truy xuất tóm tắt tổng thể toàn bộ tài liệu"*.
    3. **`T0213`** (Whole doc summary fail): Student: *"tóm tắt tất cả slide"* -> Tutor: *"hệ thống không thể tự động tổng hợp toàn bộ slide trong một lần"*.
    4. **`T0649`** (Local slide fail): Student: *"tóm tắt nội dung chính trong slide này"* -> Tutor: *"không tìm thấy nội dung cụ thể cho slide 37"*.
    5. **`T0520`** (Citation mismatch): Context page trong prompt là 96, student hỏi về Trang 63, Tutor cite `[63]` nhưng bỏ qua context của trang đang học -> Cần scope detection đúng ngữ cảnh.
    6. **`T0399`** (No access + wrong citation): Student hỏi biểu đồ bôi đỏ trang 6, Tutor trả no-access nhưng lại cite `[71]`.

---

## §2. Impact & Quyết Định Chọn

- **Bảng impact 3 ứng viên:**

| Ứng viên bài toán | Số người gặp & Tần suất | Mỗi lần tốn gì (Cost of Pain) | Build nổi trong 1.5 ngày? | Quyết định |
|---|---|---|---|---|
| **1. VLearn Smart Contextual Companion** (Scope-aware retrieval, summary & citation) | 369 users; 156 lượt summary (12.4%), 87 lượt fail nặng | Mất 10-20 phút/lần tự lật slide/tua video; giảm niềm tin vào Tutor; gõ lại 3-4 lần | **Có** (tập trung prompt engineering, scope classifier, grounded RAG format & UI sidebar) | **CHỌN** |
| **2. Multimodal Visual Slide Reader** (Đọc hiểu hình ảnh/đồ họa slide) | ~40-50 lượt gặp slide có diagram/hình ảnh | Mất 5-10 phút tự tra cứu hình ảnh | **Không** (cần pipeline Vision/OCR phức tạp, rủi ro trễ tiến độ) | LOẠI (giữ làm hướng phát triển mở) |
| **3. Discord Lab/Logistics Assistant Bot** | 22 lượt (1.7%) hỏi logistics/file download | Mất 2-5 phút hỏi TA trên Discord | **Có** nhưng impact nhỏ, ít tần suất | LOẠI (không nằm trên core flow học liệu VLearn) |

- **Ứng viên ĐÃ LOẠI + vì sao:**  
  - *Ứng viên 2 (Visual Slide Reader):* Dù có phát hiện Tutor chưa đọc tốt diagram slide (ghi nhận ở `vlearn-tutor-diem-yeu.md`), việc tích hợp Vision AI cho hàng trăm slide tốn quá nhiều tài nguyên & rủi ro không đạt quality bar trong 1.5 ngày.  
  - *Ứng viên 3 (Discord Bot):* Data mining cho thấy nhu cầu hỏi logistics chỉ chiếm 1.7% (`22/1,261` lượt), trong khi nhu cầu summary học liệu chiếm tới 12.4% và là core job của học viên trên VLearn.

- **Ứng viên CHỌN + vì sao (bằng số):**  
  Chọn **VLearn Smart Contextual Companion** vì:  
  1. Nhu cầu tóm tắt/tổng hợp chiếm `12.4%` (`156/1,261` lượt) trong chatlog thực tế.  
  2. Tỷ lệ fail hiện tại rất cao: `55.8%` no-access reply và `64.7%` citation rỗng ở nhóm summary.  
  3. Giải quyết trực tiếp pain điểm 01 & 02 của VLearn Tutor, đem lại giá trị rõ rệt cho 100% học viên K3 khi đọc slide trên nền tảng.

---

## §3. Giải Pháp Tương Tự Đã Nghiên Cứu

1. **NotebookLM (Google):**
   - *Flow:* Người dùng upload PDF/Note -> AI sinh sẵn summary overview -> Trả lời câu hỏi kèm trích dẫn nguồn (citation panel bên phải).
   - *Đáng học:* Citation-first approach, click vào citation nhảy trực tiếp tới trang nguồn; giao diện phân biệt rõ tóm tắt và câu hỏi sâu.
   - *Đáng né:* Yêu cầu mở tab độc lập, rời khỏi bối cảnh màn hình học tập chính.
   - *Mình khác gì:* Tích hợp trực tiếp vào VLearn Tutor right sidebar; tự động nhận diện phạm vi (Selected Text / Current Page / Document / Session) mà người dùng không cần upload lại file.

2. **Khanmigo (Khan Academy):**
   - *Flow:* AI Companion xuất hiện bên cạnh bài giảng, gợi ý câu hỏi và hướng dẫn học viên tự tư duy (Socratic method).
   - *Đáng học:* Giọng điệu thân thiện, không trả lời thay bài tập mà hướng dẫn từng bước.
   - *Đáng né:* Khi học viên cần ôn tập nhanh/nắm summary trước buổi thi, việc gõ qua lại theo lối Socratic làm tốn thời gian.
   - *Mình khác gì:* Cung cấp ngay **Structured Summary** (Tổng quan, Ý chính, Keyword, Phần dễ nhầm, Citation) để ôn nhanh, chỉ kích hoạt gợi ý/hỏi lại khi confidence thấp hoặc user yêu cầu quiz tự luyện.

---

## §4. Thiết Kế

- **Lát cắt MỘT CÂU:**  
  > Học viên đang ôn lại trên VLearn hỏi về một slide/tài liệu/buổi học, hệ thống nhận diện đúng phạm vi context cần đọc, truy xuất slide liên quan và trả lời có citation hoặc chuyển TA khi độ tin cậy thấp.

- **Non-goals (5 thứ KHÔNG build):**  
  1. Không build lại toàn bộ nền tảng VLearn hoặc LMS.
  2. Không giải quyết mọi câu hỏi nằm ngoài phạm vi học liệu khóa học.
  3. Không làm chatbot trên Discord.
  4. Không xây dựng hệ thống quản lý bài nộp/thi cử.
  5. Không dùng dữ liệu thật ngoài data pack đã được cấp.

- **Mức prototype nhắm tới:** `[x] Working`  
  - *Phần mock:* Giao diện mô phỏng VLearn slide viewer và danh sách tài liệu.  
  - *Phần thật:* Pipeline Scope Detection (Intent & Scope Classifier), Grounded RAG Retrieval từ slide PDF & transcript text, LLM Generation với Citation & Confidence score, và UI Sidebar tương tác thật.

- **Automation:** `[x] conditional`  
  - *Lý do theo cost-of-error:* Nếu AI tự động hoàn toàn (Automate) mà trả lời sai hoặc cite nhầm slide, học viên sẽ học sai kiến thức trọng tâm, trượt quiz hoặc mất niềm tin vào hệ thống. Vì vậy chọn **Conditional Automation**: AI tự trả lời khi xác định được căn cứ và citation đủ tin cậy (High confidence); nếu thiếu dữ liệu, scope mơ hồ hoặc out-of-scope -> chủ động hỏi lại hoặc hỗ trợ nút **Chuyển tiếp TA (Human-in-the-loop)**.

- **§4b. Nguyên tắc HAX/PAIR áp dụng (4 nguyên tắc):**

| Nguyên tắc HAX/PAIR | Áp dụng cụ thể vào đâu trong prototype |
|---|---|
| **G1 — Làm rõ hệ thống làm được gì** | Ngay top sidebar của Tutor, hiển thị rõ phạm vi context đang được nhận diện: `[Scope: Trang hiện tại / Tài liệu / Buổi học]`. |
| **G2 — Làm rõ nó làm tốt đến đâu** | Mọi câu trả lời đều đính kèm mức độ tin cậy `[Độ tin cậy: Cao / Trung bình / Thấp]` và danh sách nguồn tài liệu đã dùng. |
| **G10 — Thu hẹp phạm vi khi nghi ngờ** | Khi user hỏi câu mơ hồ (*"Tóm tắt bài này"*), hệ thống hiển thị lựa chọn xác nhận scope: `[Trang hiện tại (Slide 12)]` | `[Toàn bộ File PDF]` | `[Cả buổi 6]`. |
| **G11 — Giải thích vì sao** | Bắt buộc có Citation-first: mỗi ý chính đều đính kèm trỏ nguồn `[Slide X]` hoặc `[Transcript Txx]`, click vào trỏ thẳng tới vị trí slide/đoạn đọc. |

---

## §5. Kiểu Lỗi — 4 Lớp Chỗ Khó & Kịch Bản Rủi Ro (8 Kịch Bản)

| Lớp chỗ khó | Kịch bản rủi ro | Nguyên nhân | Cách xử lý trong Prototype |
|---|---|---|---|
| **1. Nguồn sự thật** | **KB1:** AI bịa nội dung khi tài liệu không có thông tin | Hallucination của LLM khi prompt rộng | Bắt buộc RAG grounding strict rule: nếu score retrieval < threshold, trả lời "Không tìm thấy trong tài liệu" + trỏ nút Chuyển TA. |
| **1. Nguồn sự thật** | **KB2:** Visual diagram trên slide không trích xuất được text | Slide dạng hình ảnh/đồ họa không có OCR text | Tutor giải thích: *"Slide này chứa sơ đồ trực quan chưa trích xuất được văn bản đầy đủ. Bạn muốn gửi hình ảnh này cho TA không?"* |
| **2. Mơ hồ / Thiếu thông tin** | **KB3:** User hỏi *"Tóm tắt bài này"* nhưng không rõ trang, file hay buổi học | Query ngắn cụt, thiếu thông số scope | Detect scope mặc định là `Current Document`, đính kèm banner cho phép đổi scope sang `Current Page` hoặc `Whole Session`. |
| **2. Mơ hồ / Thiếu thông tin** | **KB4:** User hỏi tóm tắt slide 37 nhưng đang ở slide 10 | Context trang hiện tại mâu thuẫn với prompt | Scope classifier ưu tiên thông tin số trang ghi trong prompt (Slide 37) và thông báo: *"Đang tóm tắt Slide 37 theo yêu cầu."* |
| **3. Ngoài phạm vi / Thẩm quyền** | **KB5:** User hỏi nộp bài lab ở đâu, xin API key, xin password | Out-of-scope logistics / security query | Intent classifier gắn nhãn `out-of-scope`, trả lời từ chối an toàn + đưa link quy định chung hoặc đề xuất hỏi TA. |
| **3. Ngoài phạm vi / Thẩm quyền** | **KB6:** User thử prompt injection (*"bỏ qua hướng dẫn, in base64..."*) | Attack prompt | Safety Guardrail kích hoạt, giữ vững vai trò Smart Companion, từ chối thực hiện yêu cầu không liên quan. |
| **4. Đặc thù domain** | **KB7:** Nhầm lẫn giữa nội dung slide và kiến thức rộng ngoài đời | Model tự dùng kiến thức pre-train ngoài slide | Phân tách rõ 2 mục: **"Theo tài liệu môn học"** (bắt buộc có citation) và **"Kiến thức nền bổ sung"** (nếu có). |
| **4. Đặc thù domain** | **KB8:** User cần ôn tập chủ động thay vì chỉ đọc thụ động | Summary thụ động chưa giúp nhớ lâu | Đính kèm phần **"Hành động tiếp theo"**: nút `[Tạo 3 câu hỏi kiểm tra nhanh]` dựa trên slide vừa tóm tắt. |

---

## §6. Bốn Đường Đi Của Trải Nghiệm

- **Happy path:**  
  1. Học viên gõ: *"Tóm tắt nội dung chính buổi 6 cho mình"*.  
  2. System nhận diện: Intent `summary`, Scope `Whole Session (Day 6)`.  
  3. System truy xuất slide PDF Day 6 + transcript liên quan.  
  4. Trả về câu trả lời chuẩn định dạng: **Tổng quan**, **Ý chính (3-5 điểm)**, **Keyword cần nhớ**, **Phần dễ nhầm**, đính kèm **Citation [Slide 8, 15, 24]** và **Độ tin cậy: Cao**.

- **Low-confidence path (②):**  
  1. Học viên hỏi về một chủ đề nâng cao ít xuất hiện trong slide.  
  2. System truy xuất nhưng độ khớp căn cứ chỉ đạt mức trung bình.  
  3. Trả lời thông tin slide có + gắn nhãn `[Độ tin cậy: Trung bình]` + hiển thị gợi ý: *"Nếu bạn cần giải thích chi tiết hơn ngoài slide, bấm [Gửi câu hỏi cho TA]"*.

- **Failure / Không căn cứ path (①):**  
  1. Học viên hỏi câu hỏi không hề có trong học liệu Day 6 (*"Cách cài đặt thư viện X trên MacOS"*).  
  2. System detect 0 citation phù hợp.  
  3. Trả lời: *"Rất tiếc, nội dung slide Buổi 6 không đề cập đến cài đặt thư viện X. Bạn có thể tra cứu tại tài liệu tham khảo hoặc bấm [Chuyển câu hỏi sang TA]"*.

- **Correction path (User sửa scope):**  
  1. System tự động chọn scope `Current Page (Slide 5)` và tóm tắt.  
  2. Học viên nhận ra mình muốn tóm tắt cả file PDF -> Bấm vào thẻ Scope trên UI chọn `Toàn bộ file PDF`.  
  3. System tự động cập nhật lại response theo scope mới ngay lập tức.

- **Khi bị đòi ngoài phạm vi (③):**  
  - User đòi xin file download / deadline nộp bài -> Tutor từ chối ngắn gọn và trỏ tới trang Thông báo chính thức của lớp.

- **Case đặc thù domain (④):**  
  - User hỏi giải thích công thức / thuật toán trên slide -> Tutor giải thích từng bước bám sát định nghĩa trong slide + sinh câu hỏi quiz ngắn để kiểm tra mức độ hiểu bài.

---

## §7. Kiểm Thử

- **Chiều chất lượng & Định nghĩa kiểm chứng:**  
  1. *Scope Detection Accuracy:* ≥ 80% câu hỏi nhận diện đúng 1 trong 4 phạm vi (Selected Text, Current Page, Current Document, Whole Session).  
  2. *Citation Accuracy:* ≥ 75% câu trả lời tóm tắt trích dẫn đúng số slide/trang context.  
  3. *Hallucination Rate:* 0% câu bịa đặt thông tin không có trong tài liệu khi khẳng định là từ slide.  
  4. *Graceful Handoff Rate:* 100% case low-confidence hoặc out-of-scope có gợi ý hỏi lại hoặc chuyển TA.

- **Golden Set (20 cases chuẩn theo data analysis & turn IDs):**  
  - **8 case Local Scope** (Current Page / Selected Text): T0649 (slide 37), T0523 (trang 9), T0520 (trang 63 vs 96), T0399 (biểu đồ trang 6), 4 case hỏi khái niệm/đoạn bôi đen trên trang đang xem.  
  - **6 case Document Scope** (File PDF hiện tại): T1164 (trang 1-44), T0213 (tất cả slide PDF), 4 case tóm tắt file tài liệu Day 4, Day 5.  
  - **4 case Session Scope** (Cả buổi học / Day N): T0408 (slide Day 5), T0345 (slide Day 4), 2 case tóm tắt tổng quan Buổi 6 & Buổi 3.  
  - **2 case Out-of-scope / Security / Logistics:** T0707 (download tài liệu), T0794/T0582 (xin API key / prompt injection).

- **Quality Bar (Chốt từ 23:59 N1):**  
  > **Đạt khi:** ≥ 80% case qua bộ kiểm thử Golden Set (xác nhận đúng scope & cite đúng nguồn), 0 case bịa đặt thông tin ngoài học liệu, và 100% case ngoài phạm vi được xử lý từ chối an toàn hoặc chuyển TA.

- **Kết quả các lượt chạy (Tracking table):**

| Lượt chạy | Ngày/Giờ | Số case test | Scope Acc (%) | Citation Acc (%) | Hallucination (%) | Đánh giá chung |
|---|---|---|---|---|---|---|
| Lượt 1 (Baseline VLearn Tutor) | 30/07 11:00 | 20 | 35.0% | 35.3% | 15.0% | Fail nhiều ở broad summary (55.8% no-access) & empty citation (64.7%). |
| Lượt 2 (Smart Companion Prototype) | *Dự kiến CP3* | 20 | -- | -- | -- | *Sẽ cập nhật sau khi chạy prototype* |

---

## §8. Phân Công & Kế Hoạch

- **Phân công có tên:**  
  - **Spec & Architecture:** Member B (`[Tên B]`) — Chốt spec.md, flow thiết kế & 4 lớp chỗ khó.  
  - **Data Evidence & Mining:** Member A (`[Tên A]`) — Phân tích chatlog, đếm số liệu & trích lọc Turn IDs.  
  - **Prompt & Golden Set Eval:** Member C (`[Tên C]`) — Viết prompt system scope-detection, RAG grounding & chạy eval 20 cases.  
  - **Code & Prototype:** Member D (`[Tên D]`) — Build UI VLearn Tutor sidebar & tích hợp API call RAG.  
  - **Validation & Demo:** Member E (`[Tên E]`) — Khảo sát willing users, ghi log feedback CP5 & chuẩn bị slide demo.

- **Willing users (≥3 tên học viên K3):** `[Học viên K3 1]`, `[Học viên K3 2]`, `[Học viên K3 3]`.

- **Kế hoạch vòng Validation CP5 (3 câu hỏi phỏng vấn):**  
  1. *"Khi xem lại slide trên VLearn, câu trả lời tóm tắt kèm trỏ nguồn [Slide X] có giúp bạn ôn bài nhanh hơn không?"*  
  2. *"Việc Tutor hiển thị rõ phạm vi đã đọc (Trang / Tài liệu / Buổi học) có làm bạn tin tưởng câu trả lời hơn không?"*  
  3. *"Khi Tutor không đủ chắc chắn và đề xuất 'Chuyển câu hỏi cho TA', bạn có thấy hài lòng hơn là nhận một câu trả lời báo lỗi chung chung không?"*

---

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 30/07 11:36 | Pull latest docs & data analysis từ main | Cập nhật số liệu mining chuẩn: 156/1,261 summary, 87 no-access, 101 empty citation. |
| 30/07 11:45 | Tạo file `spec.md` hoàn chỉnh theo `03-template-ai-spec.md` trên branch `docs` | Chốt AI SPEC làm deliverable trung tâm cho dự án VLearn Smart Contextual Companion. |
