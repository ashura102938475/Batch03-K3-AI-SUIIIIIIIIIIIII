# Corpus — slide GIẢ tự viết

**Toàn bộ nội dung trong thư mục này là slide giả do nhóm tự viết cho prototype.**
Không phải slide thật của khoá AI Thực Chiến.

Lý do: data pack (`data/vlearn-pack/`) chưa có thư mục `slides/` — README của pack ghi
"sẽ bổ sung trước sự kiện". Nhóm tự viết nội dung bám theo cấu trúc quan sát được trên
giao diện VLearn (`day01_302.pdf`, 83 trang, môn COMP2010) để prototype có thứ để
retrieve và cite.

## Quy ước

- Một file `.md` = một tài liệu. Frontmatter khai `day`, `doc_id`, `title`, `total_pages`.
- Mỗi heading `## Trang N` = một chunk, cite ra `[Trang N]`.
- Số trang trong file giả không liên tục (1, 2, 5, 12...) — cố ý, để giống việc chỉ index
  được một phần tài liệu.

## Cố ý KHÔNG có `day05`

Đường đi trải nghiệm "không đủ căn cứ → không bịa → chuyển TA" phải là thật. Trong
`app.py` Day 5 vẫn hiện trong danh sách tài liệu nhưng không có corpus, nên khi hỏi
"tóm tắt Day 5" hệ thống thiếu dữ liệu thật chứ không phải hardcode câu từ chối.

## Transcript thì lấy ở đâu?

Không nằm ở đây. `companion/retriever.py` đọc transcript thật từ
`../data/vlearn-pack/transcript/transcript-04-clean.md` lúc chạy, và cite bằng mã
`[T04-NNN]`. Data pack không được commit vào repo nộp bài nên tuyệt đối không copy
transcript vào thư mục này.
