from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Prefetch

from api.permissions import IsAdminOrReadOnly
from rent.paginations import DefaultPagination
from rent.models import Category, RentAdvertisement, AdvertisementImage, RentRequest, Favorite, Review
from rent.serializers import (
    CategorySerializer, AdvertisementImageSerializer, RentAdvertisementSerializer,
    RentAdvertisementCreateSerializer, RentRequestSerializer, RentRequestCreateSerializer,
    FavoriteSerializer, GetFavoriteSerializer, ReviewSerializer, EmptySerializer
)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow only the owner of an object or admin users to modify it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.role == "admin"


class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing property categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class RentAdvertisementViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating, retrieving, updating, and managing rental advertisements.
    Supports filtering, searching, and ordering.
    """
    queryset = RentAdvertisement.objects.select_related('category', 'owner').prefetch_related(
        'images',
        Prefetch('reviews', queryset=Review.objects.select_related('user'))
    ).all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'approved']
    pagination_class = DefaultPagination
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'price']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == "approve":
            return EmptySerializer
        if self.action == "create":
            return RentAdvertisementCreateSerializer
        return RentAdvertisementSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['approve', 'pending']:
            return [permissions.IsAdminUser()]
        else:
            return [permissions.AllowAny()]

    def perform_create(self, serializer):
        """
        Attach the logged-in user as the owner when creating an ad.
        """
        serializer.save(owner=self.request.user, approved=False)

    @swagger_auto_schema(
        method='post',
        operation_summary="Approve rental advertisement",
        operation_description="Mark a rental advertisement as approved (Admin only).",
        responses={200: openapi.Response("Advertisement approved successfully")}
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        ad = self.get_object()
        ad.approved = True
        ad.save()
        return Response({'status': 'advertisement approved'})

    @swagger_auto_schema(
        method='get',
        operation_summary="List pending advertisements",
        operation_description="Retrieve all advertisements that are not yet approved.",
        responses={200: RentAdvertisementSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def pending(self, request):
        ads = self.queryset.filter(approved=False)
        serializer = self.get_serializer(ads, many=True)
        return Response(serializer.data)


class AdvertisementImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing images of a specific rental advertisement.
    """
    serializer_class = AdvertisementImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AdvertisementImage.objects.none()
        ad_id = self.kwargs.get('ad_pk')
        return AdvertisementImage.objects.filter(advertisement_id=ad_id)

    def perform_create(self, serializer):
        ad_id = self.kwargs.get('ad_pk')
        serializer.save(advertisement_id=ad_id)

    def get_serializer_context(self):
        return {'advertisement_id': self.kwargs.get('ad_pk')}


class RentRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing rent requests for advertisements.
    """
    queryset = RentRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "accept":
            return EmptySerializer
        if self.action in ['create', 'update']:
            return RentRequestCreateSerializer
        return RentRequestSerializer

    def get_queryset(self):
        if self.action == "list":
            ad_id = self.kwargs.get("ad_pk")
            ad = RentAdvertisement.objects.get(id=ad_id)
            if self.request.user != ad.owner:
                return RentRequest.objects.none()
            return RentRequest.objects.filter(advertisement=ad)
        return super().get_queryset()

    def perform_create(self, serializer):
        ad_id = self.kwargs.get("ad_pk")
        ad = RentAdvertisement.objects.get(id=ad_id)
        if RentRequest.objects.filter(advertisement=ad, sender=self.request.user).exists():
            raise serializers.ValidationError({"detail": "You have already sent a request for this advertisement."})
        serializer.save(advertisement=ad, sender=self.request.user, status="pending")

    @swagger_auto_schema(
        method='post',
        operation_summary="Accept rent request",
        operation_description="Accept a rent request and close all other requests for the same advertisement.",
        responses={200: openapi.Response("Request accepted")}
    )
    @action(detail=True, methods=['post'])
    def accept(self, request, ad_pk=None, pk=None):
        rent_request = self.get_object()
        ad = rent_request.advertisement
        if request.user != ad.owner:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        rent_request.status = "accepted"
        rent_request.save()
        RentRequest.objects.filter(advertisement=ad).exclude(id=rent_request.id).update(status="closed")
        return Response({"status": "request accepted"})


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user favorites.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return GetFavoriteSerializer
        return FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if Favorite.objects.filter(user=self.request.user, advertisement=serializer.validated_data['advertisement']).exists():
            raise serializers.ValidationError({"detail": "You have already favorited this advertisement."})
        serializer.save(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing reviews on advertisements.
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        ad_id = self.kwargs.get("ad_pk")
        return Review.objects.filter(advertisement_id=ad_id)

    def perform_create(self, serializer):
        ad_id = self.kwargs.get("ad_pk")
        if Review.objects.filter(user=self.request.user, advertisement_id=ad_id).exists():
            raise serializers.ValidationError({"detail": "You have already reviewed this advertisement."})
        serializer.save(user=self.request.user, advertisement_id=ad_id)
