"""
clinic/models/access.py
Quản trị & Phân quyền nội bộ phòng khám.

LƯU Ý ĐỒNG BỘ (2026-05):
    Hệ thống phân quyền đã được hợp nhất.
    Toàn bộ vai trò (doctor, nurse, receptionist, pharmacist, admin)
    giờ đây được quản lý qua accounts.User.role (RoleChoices).

    Model Role và UserRole đã bị xoá khỏi code để tránh trùng lặp.
    Bảng DB cũ (roles, user_roles) vẫn tồn tại nhưng không còn được sử dụng.
"""
