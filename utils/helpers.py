import os
from datetime import datetime


def get_current_datetime():
    """Return current date and time."""
    return datetime.now()


def allowed_file(filename):
    """Check whether uploaded file has an allowed extension."""

    ALLOWED_EXTENSIONS = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp"
    }

    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def format_price(price):
    """Format price in Indian Rupees."""

    return f"₹{price:,.2f}"


def format_quantity(quantity, unit):
    """Return quantity with unit."""

    return f"{quantity} {unit}"


def generate_filename(filename):
    """Generate unique filename."""

    extension = filename.rsplit(".", 1)[1].lower()

    unique_name = datetime.now().strftime("%Y%m%d%H%M%S")

    return f"{unique_name}.{extension}"