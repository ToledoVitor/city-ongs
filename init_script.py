from accounts.models import (
    Area,
    CityHall,
    Organization,
    User,
    UserOrganizationRelatioship,
)

varzea = CityHall.objects.create(name="Prefeitura Municipal de Varzea Paulista")
CityHall.objects.create(name="Prefeitura Municipal de Campo Limpo Paulista")
CityHall.objects.create(name="Prefeitura Municipal de Jundiai")

a1 = Area.objects.create(
    city_hall=varzea,
    name="Desenvolvimento social",
    description="Desenvolvimento social",
)
a2 = Area.objects.create(
    city_hall=varzea,
    name="Desenvolvimento economico",
    description="Desenvolvimento economico",
)
a3 = Area.objects.create(
    city_hall=varzea,
    name="Gestão e Fiscalização",
    description="Gestão e Fiscalização",
)

u = User.objects.get()
u.first_name = "Vitor"
u.last_name = "Toledo"
u.save()

u.areas.add(a1)
u.areas.add(a2)
u.areas.add(a3)

o1 = Organization.objects.create(name="Ong Contabilide Vitor Toledo")
o2 = Organization.objects.create(name="Fundação Social de Desenvolvimento Social")

UserOrganizationRelatioship.objects.create(
    user=u,
    organization=o1,
)
UserOrganizationRelatioship.objects.create(
    user=u,
    organization=o2,
)
