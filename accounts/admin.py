from django.contrib import admin

from accounts.models import User, UserOngRelatioship, Ong, CityHall


admin.site.register(User)
admin.site.register(UserOngRelatioship)
admin.site.register(Ong)
admin.site.register(CityHall)
