from django.contrib import admin

from accounts.models import CityHall, Organization, User, UserOrganizationRelatioship

admin.site.register(User)
admin.site.register(UserOrganizationRelatioship)
admin.site.register(Organization)
admin.site.register(CityHall)
