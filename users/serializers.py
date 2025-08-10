from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer as BaseUserSerializer
from .models import CustomUser, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "phone_number", "address", "image"]


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "address",
            "role",
            "is_active",
        )
        read_only_fields = ("role", "is_active")
        extra_kwargs = {"password": {"write_only": True}}


class UserSerializer(BaseUserSerializer):
    profile = UserProfileSerializer(required=False)

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
            "profile",
        ]
        read_only_fields = ("role", "is_active")

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance
