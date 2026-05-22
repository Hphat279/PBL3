# Hướng Dẫn Kỹ Thuật: Nền Tảng Hệ Thống & Quản Lý Người Dùng (Core & Accounts)

Tài liệu này giải thích chi tiết cấu trúc hệ thống, cơ chế bảo mật xác thực/phân quyền, cách kế thừa giao diện và phân tích trực tiếp **mã nguồn (code)** của dự án PBL3.

---

## 1. Bản Đồ Thư Mục & Module Phụ Trách

Bạn chịu trách nhiệm hiểu và quản lý các thành phần cốt lõi sau:
* [doccure/](file:///d:/PBL3.PY/PBL3/doccure/): Cấu hình trung tâm của Django.
* [accounts/](file:///d:/PBL3.PY/PBL3/accounts/): Quản lý đăng ký, đăng nhập và thông tin tài khoản.
* [mixins/](file:///d:/PBL3.PY/PBL3/mixins/): Mixin kiểm tra quyền truy cập cho Class-based view.
* [core/](file:///d:/PBL3.PY/PBL3/core/): Thành phần dùng chung (Decorators, Models dùng chung, Template Filters).
* [templates/](file:///d:/PBL3.PY/PBL3/templates/): Hệ thống giao diện HTML kế thừa.

---

## 2. Kiến Trúc Bộ Khung Dự Án (System Platform Settings)

### Cấu hình trong `settings.py`
File: [doccure/settings.py](file:///d:/PBL3.PY/PBL3/doccure/settings.py)

Dưới đây là các thiết lập cấu hình cốt lõi bạn cần nắm:

```python
# 1. Khai báo các App trong dự án
INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    ...
    # Third-party apps
    'ckeditor',             # Hỗ trợ trình soạn thảo văn bản phong phú cho đơn thuốc
    'debug_toolbar',        # Hỗ trợ phân tích hiệu suất và truy vấn SQL (development)
    
    # Custom local apps
    'core',                 # Thành phần cốt lõi toàn cục
    'accounts',             # Đăng nhập & Quản lý tài khoản
    'doctors',              # Nghiệp vụ Bác sĩ
    'patients',             # Nghiệp vụ Bệnh nhân
    'bookings',             # Đặt lịch khám & Kê đơn
    'pharmacy',             # Quản lý kho thuốc & Phát thuốc
]

# 2. Khai báo Custom User Model thay thế cho User mặc định của Django
AUTH_USER_MODEL = "accounts.User"
```

* **Giải thích**: 
  * `INSTALLED_APPS` là nơi Django quét để nhận diện các models, views, tags và các lệnh quản trị. Nếu bạn viết một module/app mới, bạn bắt buộc phải đăng ký tên app tại đây.
  * `AUTH_USER_MODEL` chỉ định cho Django biết cần ánh xạ hệ thống xác thực (auth backend) vào bảng `User` tùy biến của app `accounts`, thay vì bảng `auth_user` mặc định.

### Định tuyến urls.py tổng
File: [doccure/urls.py](file:///d:/PBL3.PY/PBL3/doccure/urls.py)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('doctors/', include('doctors.urls')),
    path('patients/', include('patients.urls')),
    path('bookings/', include('bookings.urls')),
    path('pharmacy/', include('pharmacy.urls')),
]
```

* **Giải thích**:
  * Hàm `include()` chịu trách nhiệm chuyển tiếp yêu cầu đến các file `urls.py` cục bộ trong từng thư mục app con. Cách thiết kế này giảm thiểu xung đột mã nguồn khi làm việc nhóm và tách biệt rõ ràng tài nguyên định tuyến.

---

## 3. Phân Tích Code: Xác Thực (Authentication) & Quản Lý Người Dùng

Hệ thống quản lý thông tin tài khoản qua hai lớp Model khai báo tại [accounts/models.py](file:///d:/PBL3.PY/PBL3/accounts/models.py).

### 3.1. Custom User Model (`accounts.User`)
```python
class User(AbstractUser):
    class RoleChoices(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        PATIENT = "patient", "Patient"
        PHARMACIST = "pharmacist", "Pharmacist"

    username = models.CharField(max_length=30, unique=True)
    role = models.CharField(
        choices=RoleChoices.choices,
        max_length=20,
        default="patient",
        error_messages={"required": "Role must be provided"},
    )
    email = models.EmailField(
        blank=True,
        error_messages={
            "unique": "A user with that email already exists.",
        },
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    registration_number = models.IntegerField(null=True, blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
```

* **Giải thích chi tiết mã nguồn**:
  * `class RoleChoices(models.TextChoices)`: Định nghĩa tập hợp các hằng số đại diện cho các vai trò trong hệ thống dưới dạng text-choices.
  * `role = models.CharField(choices=RoleChoices.choices, ...)`: Trường phân vai chính. Có giá trị mặc định là `"patient"`. Trường này dùng trực tiếp cho cơ chế phân quyền (Authorization).
  * `registration_number`: Một trường số nguyên chỉ áp dụng cho Bác sĩ (Doctor), lưu mã số hành nghề y tế. Đối với Bệnh nhân và Dược sĩ, trường này sẽ nhận giá trị `Null/Blank`.
  * `USERNAME_FIELD = "username"`: Chỉ định trường được dùng làm mã định danh chính khi đăng nhập.

### 3.2. Model Profile (`accounts.Profile`)
```python
class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    avatar = models.ImageField(
        default="defaults/user.png", upload_to=profile_photo_directory_path
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(
        max_length=10,
        choices=[("male", "Nam"), ("female", "Nữ"), ("other", "Khác")],
        blank=True,
    )
    address = models.TextField(blank=True, null=True)
    price_per_consultation = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    is_available = models.BooleanField(default=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    medical_conditions = models.TextField(blank=True, null=True)
```

* **Giải thích chi tiết mã nguồn**:
  * `user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")`: Tạo mối quan hệ 1-1 chặt chẽ với User. Khi tài khoản User bị xóa (`CASCADE`), bản ghi Profile tương ứng cũng tự động bị xóa theo. `related_name="profile"` cho phép ta truy cập ngược từ User sang Profile một cách dễ dàng thông qua cú pháp: `user.profile.phone`.
  * `price_per_consultation`: Phục vụ lưu giá tiền mỗi cuộc tư vấn của bác sĩ.
  * `blood_group`, `allergies`, `medical_conditions`: Lưu trữ hồ sơ y tế cơ bản của bệnh nhân phục vụ cho việc chẩn đoán điều trị khi đặt lịch khám.

---

## 4. Phân Tích Code: Cơ Chế Phân Quyền (Authorization)

Hệ thống cung cấp cơ chế phân quyền dựa trên vai trò (`role`) của User ở cả 2 định dạng View của Django:

### 4.1. Class-Based Views Authorization (Sử dụng Mixin)
Mã nguồn tại file [mixins/custom_mixins.py](file:///d:/PBL3.PY/PBL3/mixins/custom_mixins.py):

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class PatientRequiredMixin(LoginRequiredMixin):
    permission_denied_message = "You are not authorized to view this page"

    def dispatch(self, request, *args, **kwargs):
        # 1. Kiểm tra xem người dùng đã đăng nhập chưa
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        # 2. Kiểm tra vai trò của người dùng có đúng là "patient" không
        if request.user.role != "patient":
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
```

* **Giải thích chi tiết hoạt động**:
  * Hàm `dispatch()` là cổng vào đầu tiên của Class-Based View trong Django trước khi điều phối yêu cầu tới hàm `get()` hoặc `post()`.
  * Mixin ghi đè hàm `dispatch`: 
    * Nếu user chưa đăng nhập (`not request.user.is_authenticated`), lớp cha `LoginRequiredMixin` sẽ tự động chuyển hướng người dùng về trang đăng nhập.
    * Nếu user đã đăng nhập nhưng vai trò không phải là `"patient"` (`request.user.role != "patient"`), hàm `self.handle_no_permission()` sẽ được gọi để trả về trang thông báo lỗi 403 Forbidden hoặc thông báo lỗi cấp quyền.
  * Tương tự, `DoctorRequiredMixin` yêu cầu `role == "doctor"` và `PharmacistRequiredMixin` yêu cầu `role == "pharmacist"`.

### 4.2. Function-Based Views Authorization (Sử dụng Decorator)
Mã nguồn tại file [core/decorators.py](file:///d:/PBL3.PY/PBL3/core/decorators.py):

```python
from django.core.exceptions import PermissionDenied

def user_is_doctor(function):
    def wrap(request, *args, **kwargs):
        user = request.user
        # Kiểm tra vai trò của người dùng hiện tại
        if user.role == "doctor":
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied  # Ném lỗi HTTP 403

    return wrap
```

* **Giải thích chi tiết hoạt động**:
  * Đây là một Python Decorator bọc lấy các hàm view.
  * Khi có yêu cầu truy cập, wrapper `wrap()` sẽ kiểm tra thuộc tính `role` của `request.user`. Nếu hợp lệ, nó cho phép tiếp tục thực thi view chính (`function(...)`). Ngược lại, nó lập tức ném ra ngoại lệ `PermissionDenied` để Django tự động render trang lỗi HTTP 403.

---

## 5. Phân Tích Code: Kế Thừa Giao Diện (Template Inheritance)

Django Template Engine giúp xây dựng giao diện đồng nhất bằng việc sử dụng Khung giao diện dùng chung kết hợp nhúng và ghi đè nội dung.

### 5.1. Khung xương chính: `templates/base.html`
Mã nguồn tiêu biểu tại [templates/base.html](file:///d:/PBL3.PY/PBL3/templates/base.html):

```html
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{% block title %}{% endblock %} - PBL3</title>
    <!-- Import CSS dùng chung -->
    <link rel="stylesheet" href="{% static 'assets/css/bootstrap.min.css' %}">
    <link rel="stylesheet" href="{% static 'assets/css/style.css' %}">
    <!-- Thư viện HTMX dùng cho tương tác bất đồng bộ -->
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    {% block css %}{% endblock %}
</head>
<body>
    <div class="main-wrapper">
        <!-- Nhúng navbar dùng chung -->
        {% include 'includes/navbar.html' %}

        <!-- Vùng hiển thị thông báo động -->
        {% if messages %}
            <div class="container mt-3">
                {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                    {{ message }}
                </div>
                {% endfor %}
            </div>
        {% endif %}

        <!-- Vùng nội dung động cho các trang con ghi đè -->
        {% block content %}{% endblock %}

        <!-- Nhúng footer dùng chung -->
        {% include 'includes/footer.html' %}
    </div>
    <!-- Import JS dùng chung -->
    <script src="{% static 'assets/js/jquery.min.js' %}"></script>
    <script src="{% static 'assets/js/bootstrap.min.js' %}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

* **Giải thích cơ chế**:
  * Các khối `{% block title %}`, `{% block css %}`, `{% block content %}`, `{% block scripts %}` là các "placeholder" trống. Các trang HTML con kế thừa bằng từ khóa `{% extends 'base.html' %}` và tự điền nội dung tương ứng vào bên trong các khối này.
  * Lệnh `{% include 'tên_file.html' %}` dùng để tách nhỏ và nhúng các đoạn HTML tĩnh/lặp lại (như Header, Footer, Sidebar) giúp code sạch sẽ và dễ bảo trì.

### 5.2. Phân chia menu động theo vai trò người dùng trong `navbar.html`
Mã nguồn tại file [templates/includes/navbar.html](file:///d:/PBL3.PY/PBL3/templates/includes/navbar.html#L38-L61):

```html
<ul class="main-nav">
    <li {% if request.path == '/' %}class="active"{% endif %}>
        <a href="{% url 'core:home' %}">Trang chủ</a>
    </li>
    
    <!-- Kiểm tra nếu chưa đăng nhập -->
    {% if not user.is_authenticated %}
        <li class="login-link">
            <a href="{% url 'accounts:login' %}">Đăng nhập / Đăng ký</a>
        </li>
        
    <!-- Kiểm tra nếu đăng nhập với vai trò Bệnh nhân -->
    {% elif user.role == 'patient' %}
        <li class="has-submenu">
            <a href="#">Bệnh nhân <i class="fas fa-chevron-down"></i></a>
            <ul class="submenu">
                <li><a href="{% url 'patients:dashboard' %}">Bảng điều khiển</a></li>
                <li><a href="{% url 'patients:profile-setting' %}">Cài đặt hồ sơ</a></li>
            </ul>
        </li>
        
    <!-- Kiểm tra nếu đăng nhập với vai trò Dược sĩ -->
    {% elif user.role == 'pharmacist' %}
        <li class="has-submenu">
            <a href="#">Dược sĩ <i class="fas fa-chevron-down"></i></a>
            <ul class="submenu">
                <li><a href="{% url 'pharmacy:dashboard' %}">Bảng điều khiển</a></li>
                <li><a href="{% url 'pharmacy:medicine-list' %}">Quản lý kho</a></li>
            </ul>
        </li>
    {% endif %}
</ul>
```

* **Giải thích logic**:
  * Đối tượng `user` luôn tồn tại sẵn trong context của mọi template nhờ cấu hình `auth context processor` mặc định của Django.
  * Hệ thống sử dụng thẻ điều kiện `{% if %}` của Django Template để kiểm tra trạng thái đăng nhập (`user.is_authenticated`) và kiểm tra giá trị của thuộc tính `user.role` để ẩn/hiện các đường link phù hợp cho từng loại đối tượng người dùng.

---

## 6. Phân Tích Code: Các Hàm & Bộ Lọc Tiện Ích (Utilities & Filters)

### 6.1. Định dạng hiển thị tiền tệ
Mã nguồn tại file [core/templatetags/currency_filters.py](file:///d:/PBL3.PY/PBL3/core/templatetags/currency_filters.py#L7-L27):

```python
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def vnd(value):
    if value is None:
        return ""
    try:
        # Chuyển đổi dữ liệu số Decimal hoặc String sang Integer
        val = int(Decimal(value))
    except Exception:
        try:
            val = int(value)
        except Exception:
            return value

    # Định dạng dấu phân cách phần nghìn dạng dấu chấm (150000 -> 150.000)
    s = f"{val:,}".replace(',', '.')
    return f"₫{s}"
```

* **Giải thích chi tiết mã nguồn**:
  * `@register.filter`: Decorator đăng ký hàm `vnd` thành một custom template filter.
  * Logic định dạng: Sử dụng chuỗi định dạng Python `{val:,}` để thêm dấu phân cách hàng nghìn bằng dấu phẩy theo tiêu chuẩn Anh/Mỹ, sau đó dùng `.replace(',', '.')` để đổi dấu phẩy thành dấu chấm cho phù hợp chuẩn hiển thị của Việt Nam. Cuối cùng, thêm biểu tượng tiền tệ `₫` ở đầu.
  * **Cách sử dụng trên HTML**: `{{ user.profile.price_per_consultation|vnd }}` -> Kết quả hiển thị: `₫150.000`.

### 6.2. Tạo đường dẫn ảnh đại diện ngẫu nhiên bảo mật
Mã nguồn tại file [utils/file_utils.py](file:///d:/PBL3.PY/PBL3/utils/file_utils.py):

```python
import string
from random import choice

def generate_file_name(length=30):
    # Tập hợp các ký tự chữ cái và chữ số
    letters = string.ascii_letters + string.digits
    return "".join(choice(letters) for _ in range(length))

def profile_photo_directory_path(instance, filename):
    # Tạo tên file mới ngẫu nhiên kết hợp phần mở rộng gốc của ảnh
    return "profiles/{0}".format(
        generate_file_name() + "." + filename.split(".")[-1]
    )
```

* **Giải thích chi tiết mã nguồn**:
  * Hàm `profile_photo_directory_path` được gắn trực tiếp vào tham số `upload_to` của trường ảnh đại diện `avatar` trong Model `Profile`.
  * Hàm sinh tên file ngẫu nhiên gồm 30 ký tự bằng cách lấy ngẫu nhiên (`choice`) các ký tự từ danh sách chữ và số.
  * Tác dụng:
    1. **Bảo mật**: Người dùng ngoài hệ thống không thể mò đường dẫn file ảnh.
    2. **Chống trùng lặp**: Tránh trường hợp hai người dùng khác nhau tải lên hai file có cùng tên (ví dụ: `image.jpg`), làm ghi đè và mất file của nhau.
