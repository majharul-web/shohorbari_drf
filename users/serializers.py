from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from users.models import CustomUser



class UserCreateSerializer(BaseUserCreateSerializer):
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
        extra_kwargs = {"password": {"write_only": True}}


class UserSerializer(BaseUserSerializer):
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


