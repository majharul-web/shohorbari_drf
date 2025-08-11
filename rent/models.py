from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class RentAdvertisement(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ads")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class AdvertisementImage(models.Model):
    advertisement = models.ForeignKey(RentAdvertisement, on_delete=models.CASCADE, related_name="images")
    image = CloudinaryField("image")
    
    def __str__(self):
        return f'Image for {self.advertisement.title}'

class RentRequest(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("closed", "Closed"),
    )
    advertisement = models.ForeignKey(RentAdvertisement, on_delete=models.CASCADE, related_name="requests")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rent_requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Request by {self.sender.username} for {self.advertisement.title}'

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    advertisement = models.ForeignKey(RentAdvertisement, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        unique_together = ("user", "advertisement")
        
    def __str__(self):
        return f'{self.user.first_name} favorited {self.advertisement.title}'

class Review(models.Model):
    advertisement = models.ForeignKey(RentAdvertisement, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("advertisement", "user")
    
    def __str__(self):
        return f'Review by {self.user.first_name} for {self.advertisement.title}'
