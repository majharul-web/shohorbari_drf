from django.core.exceptions import ValidationError

def validate_file_size(file):
    """
    Validates that the uploaded file does not exceed the maximum allowed size.

    Args:
        file (UploadedFile): The file uploaded by the user.

    Raises:
        ValidationError: If the uploaded file exceeds the maximum size limit.

    Details:
        - Maximum size allowed: 50 MB
        - Can be applied to image, video, or document uploads.
        - Commonly used in Django model fields or DRF serializer fields
          as a validator.

    Example:
        >>> validate_file_size(uploaded_file)
        # Raises ValidationError if file is larger than allowed
    """
    max_size = 50  # Maximum size in MB
    max_size_in_bytes = max_size * 1024 * 1024  # Convert MB to bytes

    # Compare file size with maximum limit
    if file.size > max_size_in_bytes:
        raise ValidationError(f"File size exceeds {max_size} MB limit.")
