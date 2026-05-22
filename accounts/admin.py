from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import User, Profile


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ["username", "role", "is_active", "is_staff"]
    list_filter = ("role", "is_active")
    actions = ["activate_users"]
    search_fields = (
        "first_name",
        "last_name",
        "username",
    )
    fieldsets = (
        (None, {"fields": ("username", "password", "role")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "role"),
            },
        ),
    )

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} tài khoản đã được kích hoạt.")

    activate_users.short_description = "Kích hoạt người dùng đã chọn"


@admin.register(Profile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "image_tag"]

    def image_tag(self, obj):
        return format_html('<img src="{}" width="80px" />'.format(obj.image))

    image_tag.short_description = "Avatar"
    image_tag.allow_tags = True
