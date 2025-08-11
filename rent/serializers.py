from rest_framework import serializers
from rent.models import Category, RentAdvertisement, AdvertisementImage, RentRequest, Favorite, Review
from django.contrib.auth import get_user_model

class AdvertisementImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(
        help_text="Image file for the product"
    )
    class Meta:
        model = AdvertisementImage
        fields = ["id", "image"]
        
class SimpleUserSerializer(serializers.ModelSerializer):
    name= serializers.SerializerMethodField(method_name='get_name')
    class Meta:
        model = get_user_model()
        fields = ['id', 'name']

    def get_name(self, obj):
        return obj.get_full_name()

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["id", "user", "advertisement"]
        read_only_fields = ["user"]

class ReviewSerializer(serializers.ModelSerializer):
    user= serializers.SerializerMethodField(method_name='get_user')

    def get_user(self, obj):
        return SimpleUserSerializer(obj.user).data
    
    class Meta:
        model = Review
        fields = ["id", "advertisement", "user", "rating", "comment", "created_at"]
        read_only_fields = ["advertisement", "user", "created_at"]

class RentAdvertisementSerializer(serializers.ModelSerializer):
    images = AdvertisementImageSerializer(many=True, required=False, read_only=True)
    owner = serializers.ReadOnlyField(source="owner.id")
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = RentAdvertisement
        fields = ["id", "owner", "category", "title", "description", "price", "approved", "created_at", "images","reviews"]

class RentAdvertisementCreateSerializer(serializers.ModelSerializer):
    # images = serializers.ListField(
    #     child=serializers.ImageField(), write_only=True, required=False
    # )

    class Meta:
        model = RentAdvertisement
        fields = ["category", "title", "description", "price"]

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        ad = RentAdvertisement.objects.create(**validated_data)
        for image in images:
            AdvertisementImage.objects.create(advertisement=ad, image=image)
        return ad

class RentRequestSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source="sender.id")

    class Meta:
        model = RentRequest
        fields = ["id", "advertisement", "sender", "status", "message", "created_at"]
        read_only_fields = ["status", "created_at", "advertisement", "sender"]

class RentRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentRequest
        fields = ["message"]
        


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
