

# admin.py
from django.contrib import admin
from rent.models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "user", "amount", "currency", "status", "payment_type", "created_at")
    list_filter = ("status", "payment_type", "currency")
    search_fields = ("transaction_id", "user__email", "user__username")
    readonly_fields = ("gateway_response",)
