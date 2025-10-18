from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class Category(models.Model):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
    )
    
    """
    Model representing a property category (e.g., Apartment, House).
    """
    name = models.CharField(
        max_length=100,
        help_text="Name of the category."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active",
        help_text="Status of the category."
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the advertisement was created."
    )

    def __str__(self):
        return self.name


class RentAdvertisement(models.Model):
    """
    Model representing a rental advertisement.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ads",
        help_text="User who created the advertisement."
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Category of the property."
    )
    title = models.CharField(
        max_length=255,
        help_text="Title of the advertisement."
    )
    description = models.TextField(
        help_text="Detailed description of the property."
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Price of the property."
    )
    approved = models.BooleanField(
        default=False,
        help_text="Whether the advertisement is approved by admin."
    )
    booked = models.BooleanField(
        default=False,
        help_text="Whether the advertisement is booked."
    )
    booked_by = models.ForeignKey(   
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_ads",
        help_text="User who successfully booked this advertisement via payment."
    )

    accepted = models.BooleanField(
        default=False,
        help_text="Whether the advertisement is booked."
    )
    
    accepted_for = models.ForeignKey(   
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_ads",
        help_text="User who successfully accepted this advertisement via request."
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the advertisement was created."
    )

    def __str__(self):
        return self.title


class AdvertisementImage(models.Model):
    """
    Model representing images for a rental advertisement.
    """
    advertisement = models.ForeignKey(
        RentAdvertisement,
        on_delete=models.CASCADE,
        related_name="images",
        help_text="Advertisement this image belongs to."
    )
    image = CloudinaryField(
        "image",
        help_text="Image file stored in Cloudinary."
    )
    
    def __str__(self):
        return f'Image for {self.advertisement.title}'


class RentRequest(models.Model):
    """
    Model representing a rental request sent by a user to an advertisement.
    """
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("canceled", "Canceled"),
        ("completed", "Completed"),
        ("advanced", "Advanced"),
        ("closed", "Closed"),
    )

    advertisement = models.ForeignKey(
        RentAdvertisement,
        on_delete=models.CASCADE,
        related_name="requests",
        help_text="Advertisement for which the request is made."
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rent_requests",
        help_text="User who sent the rent request."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Status of the rent request."
    )
    
    message = models.TextField(
        blank=True,
        default="",
        help_text="Optional message from the sender."
    )
    additional_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Optional additional name for the rental."
    )
    additional_phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Optional additional phone number for the rental."
    )
    additional_address = models.TextField(
        blank=True,
        default="",
        help_text="Optional additional address details."
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the request was created."
    )
    
    def __str__(self):
        return f'Request by {self.sender.username} for {self.advertisement.title}'


class Favorite(models.Model):
    """
    Model representing a user's favorite advertisement.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        help_text="User who favorited the advertisement."
    )
    advertisement = models.ForeignKey(
        RentAdvertisement,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        help_text="Advertisement marked as favorite."
    )

    class Meta:
        unique_together = ("user", "advertisement")
        verbose_name = "Favorite"
        verbose_name_plural = "Favorites"
        
    def __str__(self):
        return f'{self.user.first_name} favorited {self.advertisement.title}'


class Review(models.Model):
    """
    Model representing a review for a rental advertisement.
    """
    advertisement = models.ForeignKey(
        RentAdvertisement,
        on_delete=models.CASCADE,
        related_name="reviews",
        help_text="Advertisement being reviewed."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        help_text="User who wrote the review."
    )
    rating = models.PositiveSmallIntegerField(
        help_text="Rating given by the user (1-5)."
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional comment provided by the user."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the review was created."
    )

    class Meta:
        unique_together = ("advertisement", "user")
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
    
    def __str__(self):
        return f'Review by {self.user.first_name} for {self.advertisement.title}'




class PaymentTransaction(models.Model):
    STATUS_CHOICES = (
        ("initiated", "Initiated"),
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    )

    PAYMENT_TYPE_CHOICES = (
        ("rent", "Rent"),
        ("security_deposit", "Security Deposit"),
        ("other", "Other"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    rent_request = models.ForeignKey("RentRequest", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="BDT")
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES, default="rent")
    transaction_id = models.CharField(max_length=200, unique=True)  # tran_id from gateway (txn_xxx)
    gateway_response = models.JSONField(null=True, blank=True)      # raw payload for debugging/audit
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="initiated")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_id} - {self.user} - {self.amount} {self.currency} - {self.status}"
