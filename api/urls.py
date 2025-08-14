from django.urls import path, include
from rest_framework_nested import routers

from rent.views import (
    CategoryViewSet,
    RentAdvertisementViewSet,
    FavoriteViewSet,
    RentRequestViewSet,
    ReviewViewSet,
    AdvertisementImageViewSet
)
from admin_app.views import DashboardStatsViewSet

# Main router
router = routers.DefaultRouter()
router.register("ads", RentAdvertisementViewSet, basename="ads")
router.register("favorites", FavoriteViewSet, basename="favorites")
router.register("categories", CategoryViewSet, basename="categories")
router.register("dashboard/stats", DashboardStatsViewSet, basename="dashboard-stats")

# Nested routes for ads
ads_router = routers.NestedSimpleRouter(router, "ads", lookup="ad")
ads_router.register("requests", RentRequestViewSet, basename="ad-requests")
ads_router.register("reviews", ReviewViewSet, basename="ad-reviews")
ads_router.register("images", AdvertisementImageViewSet, basename="ad-images")

urlpatterns = [
    path('', include(router.urls)),
    path('', include(ads_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
