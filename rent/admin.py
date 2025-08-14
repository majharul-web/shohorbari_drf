from django.contrib import admin
from rent.models import (
    Category,
    RentAdvertisement,
    Favorite,
    RentRequest,
    Review,
    AdvertisementImage
)

# Register your models here.
admin.site.register(Category)
admin.site.register(RentAdvertisement)
admin.site.register(Favorite)
admin.site.register(RentRequest)
admin.site.register(Review)
admin.site.register(AdvertisementImage)