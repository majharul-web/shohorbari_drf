from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser


# Register your models here.


class UserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_active')
    list_filter = ('is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name',
         'last_name', 'address', 'phone_number','image')}),
        ('Permissions', {'fields': ('is_staff', 'is_active',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(CustomUser, UserAdmin)
admin.site.site_header = 'Shohor Bari Admin'
admin.site.site_title = 'Shohor Bari Admin Portal'
admin.site.index_title = 'Welcome to Shohor Bari Admin Portal'
