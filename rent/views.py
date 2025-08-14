from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from api.permissions import IsAdminOrReadOnly,FullDjangoModelPermissions
from django.db.models import Prefetch
from rent.paginations import DefaultPagination

from rent.models import (
    Category, RentAdvertisement, AdvertisementImage,
    RentRequest, Favorite, Review
)
from rent.serializers import (
    CategorySerializer,AdvertisementImageSerializer, RentAdvertisementSerializer, RentAdvertisementCreateSerializer,
    RentRequestSerializer, RentRequestCreateSerializer,
    FavoriteSerializer,GetFavoriteSerializer, ReviewSerializer,EmptySerializer
)

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.role == "admin"
    
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

class RentAdvertisementViewSet(viewsets.ModelViewSet):
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
        if self.action=="approve":
            return EmptySerializer
        if self.action == "create":
            return RentAdvertisementCreateSerializer
        return RentAdvertisementSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['approve', 'pending_list']:
            return [permissions.IsAdminUser()]
        else:
            return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, approved=False)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        ad = self.get_object()
        ad.approved = True
        ad.save()
        return Response({'status': 'advertisement approved'})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        ads = self.queryset.filter(approved=False)
        serializer = self.get_serializer(ads, many=True)
        return Response(serializer.data)



class AdvertisementImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing advertisement images.
    - Allows listing, retrieving, creating, updating, and deleting images for a specific advertisement.
    - Only admin users can create, update, or delete images.
    - Regular users can view the images.
    """

    serializer_class = AdvertisementImageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        # Support for swagger / schema generation (optional)
        if getattr(self, 'swagger_fake_view', False):
            return RentAdvertisement.objects.none()
        ad_id = self.kwargs.get('ad_pk')  # nested lookup key from router
        # Return images related to this advertisement
        return AdvertisementImage.objects.filter(advertisement_id=ad_id)

    def perform_create(self, serializer):
        ad_id = self.kwargs.get('ad_pk')
        # Save AdvertisementImage with FK to RentAdvertisement
        serializer.save(advertisement_id=ad_id)

    def get_serializer_context(self):
        return {'advertisement_id': self.kwargs.get('ad_pk')}


class RentRequestViewSet(viewsets.ModelViewSet):
    queryset = RentRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action=="accept":
            return EmptySerializer
        if self.action in ['create','update']:
            return RentRequestCreateSerializer
        return RentRequestSerializer

    def get_queryset(self):
        if self.action == "list":
            ad_id = self.kwargs.get("ad_pk")
            ad = RentAdvertisement.objects.get(id=ad_id)
            # Only owner can view requests for their ad
            if self.request.user != ad.owner:
                return RentRequest.objects.none()
            return RentRequest.objects.filter(advertisement=ad)
        return super().get_queryset()

    def perform_create(self, serializer):
        ad_id = self.kwargs.get("ad_pk")
        ad = RentAdvertisement.objects.get(id=ad_id)
        # Check if user already sent request or ad is approved/closed
        if RentRequest.objects.filter(advertisement=ad, sender=self.request.user).exists():
            raise serializers.ValidationError({"detail": "You have already sent a request for this advertisement."})
        serializer.save(advertisement=ad, sender=self.request.user, status="pending")

    @action(detail=True, methods=['post'])
    def accept(self, request, ad_pk=None, pk=None):
        rent_request = self.get_object()
        ad = rent_request.advertisement
        if request.user != ad.owner:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        # Accept this request
        rent_request.status = "accepted"
        rent_request.save()

        # Close other requests
        RentRequest.objects.filter(advertisement=ad).exclude(id=rent_request.id).update(status="closed")
        return Response({"status": "request accepted"})

class FavoriteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return GetFavoriteSerializer
        return FavoriteSerializer

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # check if favorite already exists
        if Favorite.objects.filter(user=self.request.user, advertisement=serializer.validated_data['advertisement']).exists():
            raise serializers.ValidationError({"detail": "You have already favorited this advertisement."})
        serializer.save(user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        ad_id = self.kwargs.get("ad_pk")
        return Review.objects.filter(advertisement_id=ad_id)

    def perform_create(self, serializer):
        ad_id = self.kwargs.get("ad_pk")
        # check if user already reviewed this ad
        if Review.objects.filter(user=self.request.user, advertisement_id=ad_id).exists():
            raise serializers.ValidationError({"detail": "You have already reviewed this advertisement."})
        serializer.save(user=self.request.user, advertisement_id=ad_id)
