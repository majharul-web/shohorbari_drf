from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class Category(models.Model):
    """
    Model representing a property category (e.g., Apartment, House).
    """
    name = models.CharField(
        max_length=100,
        help_text="Name of the category."
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
