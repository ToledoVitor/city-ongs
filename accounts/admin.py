from django.contrib import admin

from accounts.models import Area, CityHall, Organization, User

admin.site.register(Area)
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(CityHall)
