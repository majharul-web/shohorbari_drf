from django.core.exceptions import ValidationError


def validate_file_size(file):
    max_size = 50
    max_size_in_bytes = max_size * 1024 * 1024  # Convert MB to bytes
    if file.size > max_size_in_bytes:
        raise ValidationError(f"File size exceeds {max_size} MB limit.")