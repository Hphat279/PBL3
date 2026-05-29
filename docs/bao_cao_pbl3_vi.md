BÁO CÁO NÓI MIỆNG — PBL3 (NGHIỆP VỤ & CODE STYLE)

Hướng dẫn: đọc thẳng, từng mục ngắn gọn. Mỗi mục: Tính năng (features) → Luật (rules) → Lưu ý triển khai (endpoint/technical note).

MỞ ĐẦU (5s)
Kính chào thầy/cô, em trình bày phần nghiệp vụ và các rules kèm lý do chọn kỹ thuật. Em sẽ đi qua: Patient, Doctor, Booking, Prescription, Authentication/Profile, Admin & Security, rồi nêu style code.

1. PATIENT (BỆNH NHÂN) — 35s
- Features:
  - Đăng ký/đăng nhập (email/password hoặc Google OAuth), hoàn thành hồ sơ bắt buộc, tìm bác sĩ, đặt/hủy lịch, xem lịch sử, tải đơn thuốc.
- Rules (rõ ràng):
  1. Trường bắt buộc: `email`, `first_name`, `last_name`, `phone`, `country`, `address`.
  2. Nếu `country == 'Vietnam'` → `city` và `district` là bắt buộc.
  3. Middleware bắt buộc (ProfileCompletionMiddleware): redirect mọi route nếu profile chưa hoàn thành, ngoại trừ whitelist: logout, static, allauth callbacks.
  4. Sau submit: server-side validate; nếu hợp lệ set `profile_completed = True`.
- Lưu ý triển khai:
  - Endpoints: `GET/PUT /api/profile/`, `POST /api/bookings/`.
  - UI: Select2 cho chọn city/district, cascading selects từ `vietnam_regions.json` hoặc API.
- Câu đọc mẫu: “Người dùng đăng nhập → nếu thiếu trường bắt buộc → hệ thống chuyển tới Complete Profile → sau khi hoàn thành, user trở lại dashboard.”

2. DOCTOR (BÁC SĨ) — 25s
- Features:
  - Nộp hồ sơ chuyên môn, admin verify, quản lý availability, confirm/cancel booking, ghi chú bệnh án, tạo prescription.
- Rules:
  1. Bác sĩ phải `is_verified == True` (admin approve) mới hiển thị lịch công khai.
  2. Availability không được overlap — validate khi tạo.
  3. Chỉ bác sĩ owner mới CRUD prescription cho booking của họ.
- Lưu ý triển khai:
  - Endpoints: `POST /api/doctors/` (submit), `PATCH /api/doctors/{id}/verify/` (admin), `POST/GET /api/doctors/{id}/availability/`.
- Câu đọc mẫu: “Bác sĩ nộp hồ sơ → admin duyệt → bác sĩ tạo slot → bệnh nhân đặt → bác sĩ confirm.”

3. BOOKING (ĐẶT LỊCH) — 40s
- Features:
  - Tạo booking, confirm, cancel, reschedule, trạng thái hoàn tất.
- Rules / States:
  1. Trạng thái: `pending` → `confirmed` → `completed`; có thể chuyển `cancelled`, `no_show`, `rescheduled`.
  2. Tạo booking phải atomic: dùng DB transaction + `select_for_update` để tránh double-booking.
  3. Khi tạo booking: lock slot trong X phút (configurable) chờ confirm/payment; nếu timeout → release slot.
  4. Refund/penalty theo policy configurable (hours-before).
- Lưu ý triển khai:
  - Endpoints: `POST /api/bookings/`, `GET /api/bookings/{id}/`, `PATCH /api/bookings/{id}/`.
  - Concurrency: implement slot lock + transaction; test edge cases concurrent requests.
- Câu đọc mẫu: “Patient đặt slot → hệ thống tạo booking pending + lock slot → doctor confirm → chuyển confirmed.”

4. PRESCRIPTION (ĐƠN THUỐC) — 15s
- Features:
  - Bác sĩ tạo prescription liên kết booking; patient có thể tải PDF.
- Rules:
  1. Chỉ doctor owner của booking được phép tạo prescription.
  2. Prescription có thể chứa `valid_until` và lưu lịch sử cho audit.
- Lưu ý triển khai:
  - Endpoints: `POST /api/prescriptions/`, `GET /api/prescriptions/{id}/download/`.
- Câu đọc mẫu: “Sau ca khám, bác sĩ tạo đơn → bệnh nhân download.”

5. AUTHENTICATION & GOOGLE FALLBACK (OTP) — 30s
- Features:
  - Google OAuth (ưu tiên) + fallback gửi OTP 6 chữ số qua email nếu OAuth không dùng được.
- Rules:
  1. OAuth: nếu provider trả email trùng user hiện có → auto-link; nếu không → tạo account mới.
  2. OTP: code 6 chữ số; TTL = 10 phút; rate-limit (ví dụ 3 lần/15 phút).
  3. OTP lưu model `GoogleVerification` với `created_at` và `expiry`.
- Lưu ý triển khai:
  - Flows: `GET /accounts/google/login/` (allauth) hoặc `POST /accounts/google/start/` + `POST /accounts/google/verify/`.
  - Email dev fallback: console backend nếu SMTP không cấu hình.
- Câu đọc mẫu: “Ưu tiên OAuth; nếu OAuth không khả dụng thì gửi OTP, nhập mã verify và login.”

6. PROFILE ENFORCEMENT (TÁCH RIÊNG) — 10s
- Rule triển khai: Middleware site-wide redirect nếu profile incomplete; whitelist routes cần thiết.
- Lưu ý: validate server-side khi submit, set `profile_completed` đúng.

7. ADMIN & SECURITY — 20s
- Features:
  - Admin quản lý users, doctors, SocialApp (Google client), audit logs.
- Rules bảo mật:
  1. Audit log cho hành động quan trọng: create booking, cancel, create prescription.
  2. OTP có expiry + rate limit; lưu UTC; hiển thị theo timezone user.
  3. Roles phân tách: `patient`, `doctor`, `admin`.
- Lưu ý triển khai:
  - Sử dụng Django admin cho approve doctors, cấu hình SocialApp; background worker cho notifications.

8. STYLE CODE & LÝ DO CHỌN (RÕ RÀNG) — 25s
Tên style: **Django Clean-Service Style** — giữ `views`/`serializers` thật mỏng; mọi logic nghiệp vụ đặt trong `service layer`; dùng Adapter (`SocialAccountAdapter`) cho social auth; tuân SOLID để mỗi module chỉ có một trách nhiệm. Lý do: tách các concerns giúp dễ viết unit test, giảm phụ thuộc giữa các module và dễ mở rộng; phần booking dùng DB transaction + `select_for_update` để đảm bảo tính nhất quán. Công cụ chất lượng: `black`/`isort`/`flake8` + pre-commit hooks; `mypy` tuỳ chọn cho kiểm tra kiểu.

KẾT LUẬN NGẮN (10s)
- Điểm nhấn: (1) Profile enforcement để đảm bảo dữ liệu đầu vào; (2) Atomic booking để tránh double-booking; (3) Google OAuth ưu tiên + OTP fallback để đảm bảo trải nghiệm người dùng.
- Em sẵn sàng demo hoặc trả lời câu hỏi chi tiết về rule/endpoint.

HƯỚNG DẪN ĐỌC NHANH
- Mỗi mục đọc 2–4 câu: tính năng → rule → 1 câu demo. Giữ nhịp đều, rõ ràng.

HẾT
