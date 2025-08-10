from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import validate_email, FileExtensionValidator
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
from users.validators import validate_file_size

# Custom User Manager
class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Invalid email format")

        if not password:
            raise ValueError("Password must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, username=email, **extra_fields)  # set username = email
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
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

# Custom User model
class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    email = models.EmailField(unique=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    profile_image = CloudinaryField('image', blank=True, null=True,validators=[validate_file_size, FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    objects = CustomUserManager()

    def __str__(self):
        return self.email



