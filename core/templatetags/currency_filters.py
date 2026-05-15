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
