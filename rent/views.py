from rest_framework import generics, viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Prefetch
from django.http import HttpResponseRedirect
from sslcommerz_lib import SSLCOMMERZ
import requests
from api.permissions import IsAdminOrReadOnly
from rent.paginations import DefaultPagination
from rent.models import Category, RentAdvertisement, AdvertisementImage, RentRequest, Favorite, Review,PaymentTransaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404


import uuid




from rent.serializers import (
    CategorySerializer, AdvertisementImageSerializer, RentAdvertisementSerializer,
    RentAdvertisementCreateSerializer, RentRequestSerializer, RentRequestCreateSerializer,
    FavoriteSerializer, GetFavoriteSerializer, ReviewSerializer, EmptySerializer,CreatePaymentSerializer,PaymentTransactionSerializer
)


from django.conf import settings

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

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
    pagination_class = DefaultPagination


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

    def get_queryset(self):
        """
        If `?my=true` is passed, return only the current user's ads.
        Otherwise return all ads.
        """
        queryset = super().get_queryset()
        my = self.request.query_params.get("my")

        if my and my.lower() == "true":
            if self.request.user.is_authenticated:
                queryset = queryset.filter(owner=self.request.user)
            else:
                queryset = queryset.none()

        return queryset

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
            return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, approved=False)


class AdvertisementImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing images of a specific rental advertisement.
    """
    serializer_class = AdvertisementImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

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
    queryset = RentRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "change_status":
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
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # 🔹 Custom response format
        return Response(
            {
                "success": True,
                "count": queryset.count(),
                "ad_id": kwargs.get("ad_pk"),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def perform_create(self, serializer):
        ad_id = self.kwargs.get("ad_pk")
        ad = RentAdvertisement.objects.get(id=ad_id)

        if RentRequest.objects.filter(advertisement=ad, status="accepted").exists():
            raise serializers.ValidationError({
                "detail": "This advertisement already has an accepted request."
            })

        if RentRequest.objects.filter(advertisement=ad, sender=self.request.user).exists():
            raise serializers.ValidationError({
                "detail": "You have already sent a request for this advertisement."
            })

        self.instance = serializer.save(
            advertisement=ad,
            sender=self.request.user,
            status="pending"
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        # Add custom data
        return Response(
            {
                "message": "Rent request created successfully",
                "id": self.instance.id,   # newly created request ID
                "status": self.instance.status,
                "advertisement": self.instance.advertisement.id,
            },
            status=status.HTTP_201_CREATED
        )
        
        

    @action(detail=True, methods=['post'])
    def change_status(self, request, ad_pk=None, pk=None):
        """
        Change status of a rent request.
        Allowed statuses: accepted, rejected, canceled
        """
        rent_request = self.get_object()
        ad = rent_request.advertisement
        new_status = request.data.get("status")

        if new_status not in ["accepted", "rejected", "canceled"]:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Only owner can accept/reject
        if new_status in ["accepted", "rejected"] and request.user.id != ad.owner_id:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ Sender can cancel their own request
        if new_status == "canceled" and request.user.id != rent_request.sender_id:
            return Response({"detail": "Only sender can cancel this request."}, status=status.HTTP_403_FORBIDDEN)

        # ❌ Prevent rejecting/accepting already accepted
        if rent_request.status == "accepted" and new_status in ["rejected", "canceled"]:
            return Response({"detail": "Cannot modify an already accepted request."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            if new_status == "accepted":
                # Prevent multiple accepted requests
                if RentRequest.objects.filter(advertisement=ad, status="accepted").exists():
                    return Response({"detail": "Another request already accepted."}, status=status.HTTP_400_BAD_REQUEST)

                rent_request.status = "accepted"
                rent_request.save()

                ad.accepted = True
                ad.accepted_for = rent_request.sender
                ad.save()

                # Close other requests
                RentRequest.objects.filter(advertisement=ad).exclude(id=rent_request.id).update(status="closed")

            else:
                # Simple rejection/cancel
                rent_request.status = new_status
                rent_request.save()

        return Response({
            "status": f"request {new_status}",
            "request_id": rent_request.id,
            "advertisement": ad.id,
            "by": request.user.id
        }, status=status.HTTP_200_OK)


class MyRequestsViewSet(viewsets.ViewSet):
    """
    API endpoint to list rent requests for the authenticated user.
    - ?type=sent      → Requests sent by the user.
    - ?type=received  → Requests received by the user's advertisements.
    - ?status=pending → Optional filter by status.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        req_type = request.query_params.get("type", "sent")  # default to "sent"
        status_param = request.query_params.get("status")

        if req_type == "received":
            # ✅ Requests where the logged-in user is the advertisement owner
            queryset = RentRequest.objects.filter(
                advertisement__owner=request.user
            ).select_related(
                "advertisement", "advertisement__owner", "sender"
            ).prefetch_related("advertisement__images")

        else:  # "sent"
            # ✅ Requests sent by the logged-in user
            queryset = RentRequest.objects.filter(
                sender=request.user
            ).select_related(
                "advertisement", "advertisement__owner"
            ).prefetch_related("advertisement__images")

        # ✅ Optional filter by status
        if status_param:
            queryset = queryset.filter(status=status_param)

        serializer = RentRequestSerializer(queryset, many=True)
        return Response({
            "type": req_type,
            "count": queryset.count(),
            "results": serializer.data
        })


class FavoriteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user favorites.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination
    

    def get_serializer_class(self):
        if self.action == "list":
            return GetFavoriteSerializer
        return FavoriteSerializer

    def get_queryset(self):
        # Prevent error when generating Swagger schema
        if getattr(self, 'swagger_fake_view', False):
            return Favorite.objects.none()
        
        # Normal behavior for real requests
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if Favorite.objects.filter(user=self.request.user, advertisement=serializer.validated_data['advertisement']).exists():
            raise serializers.ValidationError({"detail": "You have already favorited this advertisement."})
        serializer.save(user=self.request.user)



class ReviewListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to get all reviews across all advertisements.
    Only supports list and retrieve actions.
    """
    queryset = Review.objects.all().select_related("user", "advertisement")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        data = {
            "count": queryset.count(),
            "results": serializer.data,
            "message": "All reviews retrieved successfully"
        }
        return Response(data)


    
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
        




class MyPaymentsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint for an authenticated user to see their payments.
    GET /my-payments/
    Supports ?status=success etc.
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination  # reuse your pagination

    def get_queryset(self):
        qs = PaymentTransaction.objects.filter(user=self.request.user).select_related("rent_request")
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs



# {
#   "amount": 1500,
#   "order_id": 4,
# }

SSLCZ_STORE_ID = "shoho68bfb2678b5d6"
SSLCZ_STORE_PASSWD = "shoho68bfb2678b5d6@ssl"

# Helper to generate unique tran_id
def generate_tran_id(order_id):
    return f"txn_{order_id}_{uuid.uuid4().hex[:8]}"

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request):
    """
    Initiate payment: create PaymentTransaction and SSLCOMMERZ session.
    Body: { amount, order_id, num_items, payment_type }
    """
    serializer = CreatePaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    amount = data["amount"]
    order_id = data["order_id"]
    num_items = data.get("num_items", 1)
    payment_type = data.get("payment_type", "rent")

    # Build unique tran_id
    tran_id = generate_tran_id(order_id)
    

    # Create DB record (initiated)
    with transaction.atomic():
        rent_request = None
        rent_request_id = order_id if payment_type == "rent" else None
        
        if rent_request_id:
            try:
                rent_request = RentRequest.objects.get(id=rent_request_id)
            except RentRequest.DoesNotExist:
                return Response({"error": "Rent request not found"}, status=404)
            
        tx = PaymentTransaction.objects.create(
            user=request.user,
            rent_request=rent_request,
            amount=amount,
            currency="BDT",
            payment_type=payment_type,
            transaction_id=tran_id,
            status="initiated",
        )

    # Prepare SSLCommerz payload
    settings_map = {
        'store_id': SSLCZ_STORE_ID,
        'store_pass': SSLCZ_STORE_PASSWD,
        'issandbox':  True
    }
    sslcz = SSLCOMMERZ(settings_map)

    post_body = {
        'total_amount': str(amount),
        'currency': "BDT",
        'tran_id': tran_id,
        'success_url': f"{settings.BACKEND_URL}/api/v1/payment/success/",
        'fail_url': f"{settings.BACKEND_URL}/api/v1/payment/fail/",
        'cancel_url': f"{settings.BACKEND_URL}/api/v1/payment/cancel/",
        'emi_option': 0,
        'cus_name': f"{request.user.first_name} {request.user.last_name}" or "Customer",
        'cus_email': request.user.email or "customer@example.com",
        'cus_phone': getattr(request.user, "phone_number", "01700000000"),
        'cus_add1': getattr(request.user, "address", "Dhaka"),
        'cus_city': "Dhaka",
        'cus_country': "Bangladesh",
        'ship_name': f"{request.user.first_name} {request.user.last_name}" or "Customer",
        'ship_add1': getattr(request.user, "address", "Dhaka"),
        'ship_city': "Dhaka",
        'ship_postcode': "1000",
        'ship_country': "Bangladesh",
        'shipping_method': "Courier",
        'num_of_item': num_items,
        'product_name': "Rent Payment",
        'product_category': "Service",
        'product_profile': "general"
    }

    try:
        response = sslcz.createSession(post_body)
    except Exception as e:
        # update tx
        tx.status = "failed"
        tx.gateway_response = {"exception": str(e)}
        tx.save()
        
        return Response({"error": "Failed to create payment session", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # If gateway returned success
    tx.gateway_response = response
    tx.status = "pending" if response.get("status") == "SUCCESS" else "failed"
    tx.save()

    if response.get("status") == "SUCCESS":
        return Response({"payment_url": response.get("GatewayPageURL"), "tran_id": tran_id}, status=status.HTTP_200_OK)

    return Response({"error": "Payment initiation failed", "details": response}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def payment_success(request):
    """
    Handle payment success callback from SSLCommerz.
    Updates PaymentTransaction, linked RentRequest, and advertisement booking.
    """
    data = request.data
    tran_id = data.get("tran_id")
    if not tran_id:
        return Response({"error": "Missing tran_id"}, status=400)

    print("✅ Payment Success Callback Received:", tran_id)

    # Wrap all DB operations in a single transaction
    with transaction.atomic():
        try:
            tx = PaymentTransaction.objects.select_for_update().get(transaction_id=tran_id)
        except PaymentTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

        # Save gateway payload and mark transaction as success
        tx.gateway_response = data
        tx.status = "success"
        tx.save()

        print("🔔 Payment successful for transaction:", tx)

        # If linked to a rent_request, update its status and lock the ad
        if tx.rent_request:
            rent_request = tx.rent_request
            rent_request.status = "advanced"
            rent_request.save()

            # Lock the ad to prevent race conditions
            ad = RentAdvertisement.objects.select_for_update().get(id=rent_request.advertisement.id)
            ad.booked = True
            ad.booked_by = tx.user
            ad.save()

            print("🔔 Rent request updated and advertisement booked:", ad)

    return HttpResponseRedirect(f"{settings.FRONTEND_URL}/payment-success?tran_id={tran_id}")

    # return Response({
    #     "status": "SUCCESS",
    #     "tran_id": tran_id,
    #     "rent_request": tx.rent_request.id if tx.rent_request else None,
    #     "message": "Payment successful, advertisement booked." if tx.rent_request else "Payment successful."
    # }, status=200)


@api_view(["POST"])
def payment_fail(request):
    data = request.data
    print("❌ Payment Failed:", data)

    # Update order/payment status as FAILED
    # return Response({"status": "FAILED", "data": data})
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}/payment-failed")


@api_view(["POST"])
def payment_cancel(request):
    data = request.data
    print("⚠️ Payment Cancelled:", data)

    # Update order/payment status as CANCELLED
    # return Response({"status": "CANCELLED", "data": data})
    return HttpResponseRedirect(f"{settings.FRONTEND_URL}/payment-cancelled")
