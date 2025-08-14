from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from users.models import CustomUser


# =====================================
# Serializer for Creating a New User
# =====================================
class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for user registration.
    Extends Djoser's default UserCreateSerializer to work with the CustomUser model.

    Fields:
        id (int): Auto-generated user ID.
        email (str): User's unique email (used for login).
        password (str): Write-only password.
        first_name (str): Optional first name.
        last_name (str): Optional last name.
        role (str): User role ('admin' or 'user'), read-only on registration.
        is_active (bool): Whether the user account is active, read-only.
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "is_active",
        )
        read_only_fields = ("role", "is_active")
        extra_kwargs = {
            "password": {"write_only": True}  # Prevent password from being returned in responses
        }


# =====================================
# Serializer for Retrieving/Updating a User
# =====================================
class UserSerializer(BaseUserSerializer):
    """
    Serializer for viewing or updating an existing user's profile.
    Extends Djoser's default UserSerializer for CustomUser.

    Fields:
        id (int): Auto-generated user ID.
        email (str): Unique email address of the user.
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        phone_number (str): Optional phone number.
        address (str): Optional physical address.
        role (str): Role of the user ('admin' or 'user'), read-only.
        is_active (bool): Whether the user is active, read-only.
        profile_image (ImageField): Optional profile picture stored in Cloudinary.
    """

    profile_image = serializers.ImageField(required=False)

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "role",
            "is_active",
            "profile_image",
        ]
        read_only_fields = ("role", "is_active")
