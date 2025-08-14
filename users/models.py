from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import validate_email, FileExtensionValidator
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
from users.validators import validate_file_size
from rest_framework import serializers


# =========================
# Custom User Manager
# =========================
class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model.
    Overrides default user creation methods to use email instead of username.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user.

        Args:
            email (str): The user's email (required).
            password (str): The user's password (required).
            **extra_fields: Additional attributes for the user model.

        Raises:
            ValueError: If email is not provided.
            ValueError: If email format is invalid.
            ValueError: If password is not provided.

        Returns:
            CustomUser: Newly created user instance.
        """
        if not email:
            raise ValueError("Email must be set")

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Invalid email format")

        if not password:
            raise ValueError("Password must be set")

        # Normalize email and set username equal to email
        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with elevated permissions.

        Args:
            email (str): The superuser's email.
            password (str): The superuser's password.
            **extra_fields: Additional attributes for the superuser.

        Raises:
            ValueError: If required superuser fields are not set correctly.

        Returns:
            CustomUser: Newly created superuser instance.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get('role') != 'admin':
            raise ValueError("Superuser must have role=admin")
        if not password:
            raise ValueError("Superuser must have a password.")

        return self.create_user(email, password, **extra_fields)


# =========================
# Custom User Model
# =========================
class CustomUser(AbstractUser):
    """
    Custom user model replacing username-based authentication with email.
    Includes additional fields like phone number, address, role, and profile image.

    Attributes:
        email (EmailField): Unique email address used for authentication.
        phone_number (CharField): Optional user phone number.
        address (TextField): Optional user address.
        role (CharField): User role, either 'admin' or 'user'.
        profile_image (CloudinaryField): Optional Cloudinary-hosted profile image.
    """

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    profile_image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        validators=[
            validate_file_size,
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ]
    )

    # Authentication will be based on email instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No additional required fields for createsuperuser

    objects = CustomUserManager()

    def __str__(self):
        """Return the email as the string representation of the user."""
        return self.email


