from django.contrib import admin

from accounts.models import CityHall, Organization, User

admin.site.register(User)
admin.site.register(Organization)
admin.site.register(CityHall)
