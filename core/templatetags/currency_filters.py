from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def vnd(value):
    """Format a number as Vietnamese Dong with dot as thousand separator and no decimals.

    Examples:
        300000 -> ₫300.000
        3000000 -> ₫3.000.000
    """
    if value is None:
        return ""
    try:
        # convert Decimal or numeric strings to int
        val = int(Decimal(value))
    except Exception:
        try:
            val = int(value)
        except Exception:
            return value

    s = f"{val:,}".replace(',', '.')
    return f"₫{s}"


@register.filter
def status_label(value):
    """Translate internal status codes to Vietnamese labels."""
    if not value:
        return ""
    mapping = {
        'pending': 'Đang chờ',
        'confirmed': 'Đã xác nhận',
        'completed': 'Hoàn thành',
        'cancelled': 'Đã hủy',
        'no_show': 'Vắng mặt',
    }
    return mapping.get(value, str(value).title())


@register.filter
def date_vn(value):
    """Format a date/datetime to a Vietnamese-friendly string: '27 Tháng 9, 2003'."""
    if not value:
        return ""
    try:
        # value may be date or datetime
        day = value.day
        month = value.month
        year = value.year
        return f"{day} Tháng {month}, {year}"
    except Exception:
        return value
