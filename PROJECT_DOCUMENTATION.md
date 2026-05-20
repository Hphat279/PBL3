# Tài Liệu Dự Án PBL3 - Hệ Thống Đặt Lịch Khám Bệnh

## Tổng Quan Dự Án

PBL3 là một hệ thống đặt lịch khám bệnh hiện đại kết nối bệnh nhân với bác sĩ. Nền tảng này đơn giản hóa quy trình tìm bác sĩ, đặt lịch hẹn và quản lý tư vấn y tế.

### Mục Tiêu
- Hiện đại hóa việc tiếp cận chăm sóc sức khỏe tại Việt Nam
- Đơn giản hóa việc đặt lịch cho bệnh nhân
- Quản lý thực hành hiệu quả cho bác sĩ
- Cải thiện tiếp cận chăm sóc sức khỏe thông qua công nghệ
- Đảm bảo quyền riêng tư và bảo mật dữ liệu bệnh nhân
- Giảm giấy tờ thông qua hồ sơ điện tử

## Kiến Trúc Hệ Thống

### Công Nghệ Sử Dụng

#### Backend
- **Python 3.8+**
- **Django 5.0.6** - Framework web chính
- **Django REST Framework 3.15.1** - API REST
- **SQLite3** - Cơ sở dữ liệu mặc định (có thể thay bằng PostgreSQL/MySQL)
- **Pillow 10.3.0** - Xử lý hình ảnh
- **Django CKEditor 6.7.2** - Soạn thảo văn bản phong phú

#### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap 4** - Framework CSS
- **jQuery** - Thư viện JavaScript
- **Chart.js** - Biểu đồ và thống kê
- **HTMX** - Tương tác động
- **Font Awesome** - Biểu tượng

#### Công Cụ Phát Triển
- **Django Debug Toolbar 4.4.2** - Gỡ lỗi
- **Black 24.4.2** - Định dạng code (line-length: 79)
- **Factory Boy 3.3.3** - Tạo dữ liệu test
- **Faker 37.0.1** - Dữ liệu giả
- **Pytest 8.3.0** - Testing
- **Gunicorn 23.0.0** - WSGI server

### Cấu Trúc Thư Mục

```
PBL3/
├── db.sqlite3                    # Cơ sở dữ liệu SQLite
├── manage.py                     # Django management script
├── pyproject.toml               # Cấu hình Black formatter
├── requirements.txt             # Dependencies Python
├── README.md                    # Tài liệu dự án
├── doccure/                     # Thư mục chính Django
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # Cấu hình Django
│   ├── urls.py                 # URL routing chính
│   └── wsgi.py
├── accounts/                    # App quản lý tài khoản
│   ├── models.py               # User, Profile
│   ├── views/                  # Login, Register
│   ├── forms.py                # Form đăng ký
│   ├── managers.py             # Custom User Manager
│   └── urls.py
├── bookings/                    # App đặt lịch
│   ├── models.py               # Booking, Prescription
│   ├── views.py                # Logic đặt lịch
│   └── urls.py
├── core/                       # App cốt lõi
│   ├── models.py               # Speciality, Review
│   └── views.py                # Home, Terms, Privacy
├── doctors/                     # App bác sĩ
│   ├── models/                 # Education, Experience, Schedule
│   ├── views.py                # Dashboard, Profile
│   ├── forms.py                # Profile form
│   └── urls.py
├── patients/                    # App bệnh nhân
│   ├── models.py               # (Trống)
│   ├── views.py                # Patient views
│   └── urls.py
├── mixins/                      # Mixins tùy chỉnh
├── utils/                       # Utilities
├── static/                      # Static files
├── media/                       # Media files
├── templates/                   # HTML templates
├── fixtures/                    # Dữ liệu mẫu
├── tests/                       # Test cases
└── screenshots/                 # Ảnh demo
```

## Cấu Trúc Cơ Sở Dữ Liệu

### Models Chính

#### 1. accounts.User (Custom User Model)
- **username**: CharField (unique)
- **role**: CharField (choices: doctor/patient)
- **email**: EmailField
- **first_name, last_name**: CharField
- **registration_number**: IntegerField (cho bác sĩ)
- **Methods**:
  - `get_full_name()`: Trả về họ tên đầy đủ
  - `get_doctor_profile()`: URL profile bác sĩ
  - `average_rating`: Trung bình rating
  - `rating_count`: Số lượng đánh giá

#### 2. accounts.Profile
- **user**: OneToOneField -> User
- **avatar**: ImageField
- **phone, dob, about**: Thông tin cá nhân
- **specialization**: Chuyên khoa (cho bác sĩ)
- **gender, address, city, state, postal_code, country**
- **price_per_consultation**: Giá tư vấn
- **is_available**: Có sẵn không
- **blood_group, allergies, medical_conditions**: Thông tin y tế

#### 3. core.Speciality
- **name**: Tên chuyên khoa
- **slug**: Slug tự động tạo
- **description**: Mô tả
- **image**: Hình ảnh
- **is_active**: Hoạt động
- **Properties**:
  - `doctor_count`: Số bác sĩ trong chuyên khoa
  - `image_url`: URL hình ảnh

#### 4. core.Review
- **patient**: ForeignKey -> User
- **doctor**: ForeignKey -> User
- **booking**: OneToOneField -> Booking
- **rating**: IntegerField (1-5)
- **review**: TextField
- **created_at, updated_at**: DateTimeField

#### 5. bookings.Booking
- **doctor**: ForeignKey -> User (role=doctor)
- **patient**: ForeignKey -> User (role=patient)
- **appointment_date**: DateField
- **appointment_time**: TimeField
- **booking_date**: DateTimeField (auto_now_add)
- **status**: CharField (pending/confirmed/completed/cancelled/no_show)
- **Meta**:
  - unique_together: (doctor, appointment_date, appointment_time)
  - ordering: [-appointment_date, -appointment_time]

#### 6. bookings.Prescription
- **booking**: OneToOneField -> Booking
- **doctor, patient**: ForeignKey -> User
- **symptoms, diagnosis**: TextField
- **medications**: RichTextField (CKEditor)
- **notes**: TextField
- **created_at, updated_at**: DateTimeField

#### 7. doctors.Education
- **user**: ForeignKey -> User
- **college, degree**: CharField
- **year_of_completion**: IntegerField

#### 8. doctors.Experience
- **user**: ForeignKey -> User
- **institution**: CharField
- **from_year, to_year**: IntegerField
- **working_here**: BooleanField
- **designation**: CharField

#### 9. doctors.TimeRange
- **start, end**: TimeField
- **is_active**: BooleanField
- **slots_per_hour**: PositiveIntegerField (default=4)
- **Methods**:
  - `get_slot_duration()`: Trả về khoảng thời gian slot (phút)
  - `get_available_slots(date)`: Liệt kê slot trống

#### 10. doctors.*Day (Saturday, Sunday, Monday, etc.)
- **user**: OneToOneField -> User
- **time_range**: ManyToManyField -> TimeRange

## Quy Tắc Nghiệp Vụ (Business Rules)

### 1. Quy Tắc Đặt Lịch
- Một bác sĩ không thể có 2 lịch hẹn cùng thời điểm
- Bệnh nhân chỉ có thể đặt lịch với bác sĩ có role="doctor"
- Bác sĩ chỉ có thể nhận lịch hẹn từ bệnh nhân có role="patient"
- Thời gian đặt lịch phải trong khoảng thời gian làm việc của bác sĩ
- Mỗi booking chỉ có 1 prescription

### 2. Quy Tắc Đánh Giá
- Chỉ bệnh nhân đã có booking với bác sĩ mới có thể đánh giá
- Mỗi cặp patient-doctor chỉ có 1 review
- Rating từ 1-5 sao

### 3. Quy Tắc Tài Khoản
- Username là duy nhất
- Role không thể thay đổi sau khi tạo
- Bác sĩ có registration_number
- Profile là bắt buộc cho tất cả user

### 4. Quy Tắc Chuyên Khoa
- Speciality có slug tự động tạo từ name
- Chỉ hiển thị speciality có is_active=True
- Doctor count được tính động

### 5. Quy Tắc Thời Gian Bác Sĩ
- Mỗi ngày trong tuần có thể có nhiều TimeRange
- Slots được chia đều trong TimeRange
- Mặc định 4 slots/giờ (15 phút/slot)

## Chức Năng Chính

### Cho Bệnh Nhân
1. **Tìm Kiếm Bác Sĩ**
   - Tìm theo chuyên khoa, tên, địa điểm
   - Xem profile bác sĩ
   - Xem lịch trình có sẵn

2. **Đặt Lịch Hẹn**
   - Chọn ngày và giờ trong lịch trống
   - Xem chi tiết lịch hẹn
   - Hủy lịch hẹn

3. **Quản Lý Hồ Sơ**
   - Hồ sơ cá nhân
   - Lịch sử đặt lịch
   - Hóa đơn điện tử
   - Đánh giá bác sĩ

### Cho Bác Sĩ
1. **Quản Lý Profile**
   - Thông tin cá nhân
   - Học vấn và kinh nghiệm
   - Chuyên khoa
   - Giá tư vấn

2. **Quản Lý Lịch Trình**
   - Thiết lập thời gian làm việc theo ngày
   - Chia slot thời gian
   - Xem lịch hẹn

3. **Quản Lý Cuộc Hẹn**
   - Xem danh sách bệnh nhân
   - Chấp nhận/từ chối lịch hẹn
   - Hoàn thành cuộc hẹn
   - Viết đơn thuốc

4. **Thống Kê**
   - Số bệnh nhân
   - Thu nhập
   - Đánh giá

### Cho Quản Trị Viên
1. **Dashboard**
   - Thống kê tổng quan
   - Biểu đồ doanh thu
   - Báo cáo hiệu suất

2. **Quản Lý Người Dùng**
   - Xem danh sách bác sĩ/bệnh nhân
   - Quản lý tài khoản

3. **Quản Lý Chuyên Khoa**
   - Thêm/sửa/xóa chuyên khoa
   - Quản lý hình ảnh

4. **Giám Sát**
   - Xem tất cả lịch hẹn
   - Quản lý đơn thuốc
   - Modereate đánh giá

## Quy Tắc Code (Coding Standards)

### 1. Python Style Guide (PEP8)
- Sử dụng Black formatter với line-length=79
- 4 spaces indentation
- Naming conventions:
  - Classes: PascalCase
  - Functions/Methods: snake_case
  - Variables: snake_case
  - Constants: UPPER_CASE

### 2. Django Best Practices
- Sử dụng Class-Based Views thay vì Function-Based
- Model inheritance từ AbstractUser
- ForeignKey với related_name
- Meta class cho ordering, unique_together
- Properties cho computed fields

### 3. Database Design
- Sử dụng ForeignKey cho relationships
- OneToOneField cho dữ liệu mở rộng
- ManyToManyField cho quan hệ nhiều-nhiều
- Unique constraints để tránh duplicate
- Indexing cho các trường tìm kiếm thường xuyên

### 4. Security
- Sử dụng Django's built-in authentication
- CSRF protection
- Input validation qua forms
- Role-based access control
- Secure file uploads

### 5. Performance
- Select_related/Prefetch_related cho queries
- Pagination cho danh sách lớn
- Caching khi cần thiết
- Optimized database queries

## Cài Đặt và Chạy Dự Án

### Yêu Cầu Hệ Thống
- Python 3.8+
- pip
- Virtualenv (khuyến nghị)

### Tài Khoản Demo
Sau khi load fixtures:
- **Bác sĩ**: username: doctor1, password: Abcdefgh.1
- **Bệnh nhân**: username: patient1, password: Abcdefgh.1

## API Endpoints

### Authentication
- `POST /accounts/login/` - Đăng nhập
- `POST /accounts/register/doctor/` - Đăng ký bác sĩ
- `POST /accounts/register/patient/` - Đăng ký bệnh nhân

### Doctors
- `GET /doctors/` - Danh sách bác sĩ
- `GET /doctors/<username>/` - Chi tiết bác sĩ
- `GET /doctors/dashboard/` - Dashboard bác sĩ
- `POST /doctors/<username>/book/` - Đặt lịch

### Bookings
- `GET /bookings/` - Danh sách lịch hẹn
- `POST /bookings/cancel/<id>/` - Hủy lịch

### Admin
- `GET /admin/` - Dashboard admin
- `GET /admin/doctors/` - Quản lý bác sĩ
- `GET /admin/patients/` - Quản lý bệnh nhân
- `GET /admin/appointments/` - Quản lý lịch hẹn

## Testing

### Chạy Tests
```bash
pytest
# hoặc
python manage.py test
```

### Coverage
```bash
pytest --cov=.
```

## Deployment

### Development
- DEBUG = True
- SQLite database
- Django Debug Toolbar

### Production
- DEBUG = False
- PostgreSQL/MySQL database
- Gunicorn + Nginx
- Environment variables cho secrets

### Docker
- Dockerfile cho production
- docker-compose.prod.yml

## Các Điểm Cần Lưu Ý

### 1. Business Logic
- Validation cho thời gian đặt lịch
- Kiểm tra role trước khi thực hiện actions
- Unique constraints cho bookings

### 2. UI/UX
- Responsive design với Bootstrap
- HTMX cho dynamic content
- Chart.js cho visualizations

### 3. Security
- Django's security features
- Input sanitization
- File upload security

### 4. Scalability
- Database optimization
- Caching strategy
- API design cho mobile app

### 5. Style Code
- PEP8 + Django conventions với Black formatter.
- Để đảm bảo code quality và consistency. 
- Style này giúp code dễ đọc, dễ maintain và theo chuẩn industry.