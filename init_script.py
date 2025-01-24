from accounts.models import (
    Area,
    CityHall,
    Organization,
    User,
)
from contracts.models import Company
from utils.choices import StatesChoices

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

o1 = Organization.objects.create(name="Ong Contabilide Vitor Toledo", city_hall=varzea)
o2 = Organization.objects.create(
    name="Fundação Social de Desenvolvimento Social", city_hall=varzea
)

super_user = User.objects.create(
    first_name="Vitor",
    last_name="Toledo",
    email="admin@admin.com",
    password="admin@2025",
    Organization=o1,
)
super_user.areas.add(a1)
super_user.areas.add(a2)
super_user.areas.add(a3)

Company.objects.create(
    name="Empresa Contratente",
    cnpj="24479422000150",
    street="Rua Fausto Silveira Pires",
    number=93,
    complement=None,
    district="Jardim Primavera",
    city="Varzea Paulista",
    uf=StatesChoices.SP,
    postal_code=13220270,
    organization=o1,
)
Company.objects.create(
    name="Empresa Contratada",
    cnpj="49279736000130",
    street="Rua Senador Vergueiro",
    number=250,
    complement="Apto 305",
    district="Flamengo",
    city="Rio de Janeiro",
    uf=StatesChoices.RJ,
    postal_code=22220000,
    organization=o1,
)
Company.objects.create(
    name="Software Vitor Toledo S.A.",
    cnpj="21135963000172",
    street="Rua Xavier da Silveira",
    number=29,
    complement="Apto 901",
    district="Copacabana",
    city="Rio de Janeiro",
    uf=StatesChoices.RJ,
    postal_code=22061010,
    organization=o1,
)
Company.objects.create(
    name="Empresa Teste",
    cnpj="98521329000100",
    street="Rua Testes",
    number=100,
    complement="Bloco B",
    district="Jardim Testes",
    city="Testópolis",
    uf=StatesChoices.GO,
    postal_code=11110000,
    organization=o1,
)
