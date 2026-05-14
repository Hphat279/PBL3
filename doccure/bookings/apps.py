from django.apps import AppConfig


class BookingsConfig(AppConfig):
    name = "bookings"
    default_auto_field = "django.db.models.AutoField"
    verbose_name = "Đặt lịch online"

    def ready(self):
        import bookings.signals  # noqa: F401 – kết nối signals đồng bộ
