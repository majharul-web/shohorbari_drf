# views.py
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Q
from django.utils.timezone import now, timedelta
from rent.models import RentAdvertisement

class DashboardStatsViewSet(ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request):
        today = now()
        last_7_days = today - timedelta(days=7)
        last_30_days = today - timedelta(days=30)

        current_month = today.month
        current_year = today.year
        last_month = 12 if current_month == 1 else current_month - 1
        last_month_year = current_year - 1 if current_month == 1 else current_year

        stats = RentAdvertisement.objects.aggregate(
            total_ads=Count("id"),
            approved_ads=Count("id", filter=Q(approved=True)),
            pending_ads=Count("id", filter=Q(approved=False)),
            ads_last_7_days=Count("id", filter=Q(created_at__gte=last_7_days)),
            ads_current_month=Count(
                "id",
                filter=Q(created_at__year=current_year, created_at__month=current_month)
            ),
            ads_last_month=Count(
                "id",
                filter=Q(created_at__year=last_month_year, created_at__month=last_month)
            ),
        )
        return Response(stats)
