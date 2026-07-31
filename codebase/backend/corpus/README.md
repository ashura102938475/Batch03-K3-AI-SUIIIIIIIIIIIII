# Corpus

Backend hiện ưu tiên index trực tiếp data pack tại
`codebase/data/vlearn-pack/`: 2 PDF slide và 6 transcript sạch có mã đoạn
`[Txx-NNN]`. Thư mục này chỉ còn vai trò chứa corpus fallback nếu cần bổ sung
fixture nhỏ cho test.

Không copy thêm toàn bộ data pack vào đây. Khi viết test, dùng fixture tối thiểu
và ghi rõ dữ liệu mock. Khi trích dẫn chatlog/transcript trong tài liệu, dùng
`turn_id` hoặc mã đoạn thay vì thông tin nhận dạng.
