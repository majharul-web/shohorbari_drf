from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Count, Q
from django.utils.timezone import now, timedelta
from rent.models import RentAdvertisement


class DashboardStatsViewSet(ViewSet):
    """
    API endpoint providing admin dashboard statistics for rental advertisements.
    Only accessible to admin users.
    """
    permission_classes = [IsAdminUser]

    def list(self, request):
        """
        Retrieve rental advertisement statistics.

        Returns:
            - total_ads: Total number of ads in the system.
            - approved_ads: Ads that have been approved by admins.
            - pending_ads: Ads awaiting approval.
            - ads_last_7_days: Ads created in the last 7 days.
            - ads_current_month: Ads created in the current month.
            - ads_last_month: Ads created in the previous month.
        """
        today = now()

        # Date ranges
        last_7_days = today - timedelta(days=7)
        current_month = today.month
        current_year = today.year

        # Last month calculations
        last_month = 12 if current_month == 1 else current_month - 1
        last_month_year = current_year - 1 if current_month == 1 else current_year

        # Aggregated statistics
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
