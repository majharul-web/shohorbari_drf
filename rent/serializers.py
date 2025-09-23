from rest_framework import serializers
from rent.models import Category, RentAdvertisement, AdvertisementImage, RentRequest, Favorite, Review, PaymentTransaction
from django.contrib.auth import get_user_model
from django.contrib.auth import get_user_model

User = get_user_model()


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

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for property categories.
    """
    name = serializers.CharField(help_text="Name of the category.")

    class Meta:
        model = Category
        fields = ["id", "name", "created_at"]
        
class SimpleUserSerializer(serializers.ModelSerializer):
    """
    Simplified user representation showing only `id`, `name`, `email`, and profile image.
    Returns the full URL for profile_image if available.
    """
    name = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email", "profile_image"]

    def get_name(self, obj):
        return obj.get_full_name()

    def get_profile_image(self, obj):
        request = self.context.get("request")
        if obj.profile_image:
            # If Cloudinary is used, obj.profile_image.url is already a full URL
            image_url = obj.profile_image.url
            # If it's local storage, prepend the domaindf
            if request is not None:
                return request.build_absolute_uri(image_url) 
            return image_url
        return None


class SimpleAdvertisementSerializer(serializers.ModelSerializer):
    """
    Simplified advertisement serializer for nested usage.
    """
    image = serializers.SerializerMethodField(help_text="URL of the first image of the advertisement.")  

    class Meta:
        model = RentAdvertisement
        fields = ['id', 'title', 'price', 'booked', 'image']

    def get_image(self, obj):
        first_image = obj.images.first()
        if first_image:
            return first_image.image.url  # <-- CloudinaryField gives .url
        return None



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
    owner = SimpleUserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = RentAdvertisement
        fields = [
            "id", "owner", "category", "title", "description", "price",
            "approved", "booked", "created_at", "images", "reviews"
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

class SimpleRentRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentRequest
        fields = ["id", "advertisement", "status", "sender", "created_at"]
        depth = 1  # optional, to expand related advertisement/sender
        

class PaymentTransactionSerializer(serializers.ModelSerializer):
    user=SimpleUserSerializer(read_only=True)
    rent_request = SimpleRentRequestSerializer(read_only=True)
    class Meta:
        model = PaymentTransaction
        fields = "__all__"
        read_only_fields = ["id", "rent_request", "user", "gateway_response", "created_at", "updated_at"]

class CreatePaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    order_id = serializers.CharField()   # your internal order/rent_request id
    num_items = serializers.IntegerField(required=False, default=1)
    payment_type = serializers.ChoiceField(choices=PaymentTransaction.PAYMENT_TYPE_CHOICES, default="rent")




