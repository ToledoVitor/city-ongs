from django.contrib import admin

from accounts.models import CityHall, Ong, User, UserOngRelatioship

admin.site.register(User)
admin.site.register(UserOngRelatioship)
admin.site.register(Ong)
admin.site.register(CityHall)
