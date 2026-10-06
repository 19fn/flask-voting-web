"""Vote totals and percentage shares for the results display."""

from decimal import ROUND_HALF_UP, Decimal


def percentage(count, total):
    """Return ``count`` as a percentage of ``total``, rounded to one decimal.

    Rounds half up (12.25 -> 12.3), unlike ``round()``, which rounds half to
    even and is affected by binary floating point. Returns 0.0 when
    ``total`` is zero instead of raising ``ZeroDivisionError``.
    """
    if total <= 0:
        return 0.0
    value = Decimal(count) * 100 / Decimal(total)
    return float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def format_percentage(value):
    """Format a percentage for display: ``0%`` for zero, else ``12.3%``."""
    if value == 0:
        return "0%"
    return f"{value:.1f}%"


def vote_results(green, red):
    """Return the total and each option's count and percentage share."""
    total = green + red
    green_pct = percentage(green, total)
    red_pct = percentage(red, total)
    return {
        "total": total,
        "green": {
            "count": green,
            "percent": green_pct,
            "label": format_percentage(green_pct),
        },
        "red": {
            "count": red,
            "percent": red_pct,
            "label": format_percentage(red_pct),
        },
    }
