from django.contrib import admin

from accounts.models import Area, CityHall, Committee, Organization, User

admin.site.register(Area)
admin.site.register(Committee)
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(CityHall)
