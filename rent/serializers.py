from rest_framework import serializers
from rent.models import Category, RentAdvertisement, AdvertisementImage, RentRequest, Favorite, Review
from django.contrib.auth import get_user_model


class EmptySerializer(serializers.Serializer):
    """
    Empty serializer used for endpoints that don't require a request body.
    Example: Approve actions or status updates.
    """
    pass


class AdvertisementImageSerializer(serializers.ModelSerializer):
    """
    Serializer for handling advertisement images.
    """
    image = serializers.ImageField(
        help_text="Upload an image file for the advertisement."
    )

    class Meta:
        model = AdvertisementImage
        fields = ["id", "image"]


class SimpleUserSerializer(serializers.ModelSerializer):
    """
    Simplified user representation showing only `id` and `name`.
    """
    name = serializers.SerializerMethodField(method_name='get_name', help_text="Full name of the user.")

    class Meta:
        model = get_user_model()
        fields = ['id', 'name']

    def get_name(self, obj):
        return obj.get_full_name()


class SimpleAdvertisementSerializer(serializers.ModelSerializer):
    """
    Simplified advertisement serializer for nested usage.
    """
    class Meta:
        model = RentAdvertisement
        fields = ['id', 'title']


class GetFavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving a user's favorite advertisements.
    Includes user and simplified advertisement details.
    """
    user = serializers.SerializerMethodField(method_name='get_user', help_text="Details of the user who favorited.")
    advertisement = SimpleAdvertisementSerializer(help_text="Basic advertisement information.")

    def get_user(self, obj):
        return SimpleUserSerializer(obj.user).data

    class Meta:
        model = Favorite
        fields = ["id", "user", "advertisement"]
        read_only_fields = ["user"]


class FavoriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating a favorite advertisement.
    """
    advertisement = serializers.PrimaryKeyRelatedField(
        queryset=RentAdvertisement.objects.all(),
        help_text="ID of the advertisement to favorite."
    )

    class Meta:
        model = Favorite
        fields = ["advertisement"]


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviews on advertisements.
    """
    user = serializers.SerializerMethodField(method_name='get_user', help_text="Details of the reviewer.")

    def get_user(self, obj):
        return SimpleUserSerializer(obj.user).data

    class Meta:
        model = Review
        fields = ["id", "advertisement", "user", "rating", "comment", "created_at"]
        read_only_fields = ["advertisement", "user", "created_at"]


class RentAdvertisementSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving rental advertisement details.
    Includes images and reviews.
    """
    images = AdvertisementImageSerializer(many=True, required=False, read_only=True)
    owner = serializers.ReadOnlyField(source="owner.id", help_text="ID of the advertisement owner.")
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = RentAdvertisement
        fields = [
            "id", "owner", "category", "title", "description", "price",
            "approved", "created_at", "images", "reviews"
        ]


class RentAdvertisementCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a rental advertisement.
    """
    class Meta:
        model = RentAdvertisement
        fields = ["category", "title", "description", "price"]

    def create(self, validated_data):
        """
        Create advertisement with optional images.
        """
        images = validated_data.pop("images", [])
        ad = RentAdvertisement.objects.create(**validated_data)
        for image in images:
            AdvertisementImage.objects.create(advertisement=ad, image=image)
        return ad


class RentRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving rental requests.
    """
    sender = SimpleUserSerializer(help_text="Details of the user who sent the request.")
    advertisement = SimpleAdvertisementSerializer(help_text="Basic advertisement details.")

    class Meta:
        model = RentRequest
        fields = ["id", "advertisement", "sender", "status", "message", "created_at"]
        read_only_fields = ["status", "created_at", "advertisement", "sender"]


class RentRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a rent request.
    """
    message = serializers.CharField(
        help_text="Message from the requester to the advertisement owner."
    )

    class Meta:
        model = RentRequest
        fields = ["message"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for property categories.
    """
    name = serializers.CharField(help_text="Name of the category.")

    class Meta:
        model = Category
        fields = ["id", "name"]
