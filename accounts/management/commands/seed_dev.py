from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django_cpf_cnpj.fields import CNPJ
from easy_tenants import tenant_context

from accounts.models import Area, CityHall, Organization, User
from contracts.models import Company
from utils.choices import StatesChoices

DEV_PASSWORD = "admin"


def ensure_city_hall(*, name, mayor, document):
    digits = "".join(c for c in document if c.isdigit())
    obj, _ = CityHall.objects.get_or_create(
        document=digits,
        defaults={"name": name, "mayor": mayor},
    )
    changed = False
    if obj.name != name:
        obj.name = name
        changed = True
    if obj.mayor != mayor:
        obj.mayor = mayor
        changed = True
    if changed:
        obj.save()
    return obj


def ensure_organization(*, city_hall, name, owner, document):
    digits = "".join(c for c in document if c.isdigit())
    org, _ = Organization.objects.get_or_create(
        city_hall=city_hall,
        document=digits,
        defaults={"name": name, "owner": owner or ""},
    )
    changed = False
    if org.name != name:
        org.name = name
        changed = True
    if (org.owner or "") != (owner or ""):
        org.owner = owner or ""
        changed = True
    if changed:
        org.save()
    return org


def ensure_area(*, organization, city_hall, name, description):
    area, _ = Area.objects.get_or_create(
        organization=organization,
        name=name,
        defaults={"city_hall": city_hall, "description": description},
    )
    changed = False
    if area.city_hall_id != city_hall.id:
        area.city_hall = city_hall
        changed = True
    if area.description != description:
        area.description = description
        changed = True
    if changed:
        area.save()
    return area


def ensure_company(organization, cnpj_digits, **fields):
    digits = "".join(c for c in cnpj_digits if c.isdigit())
    cnpj_value = CNPJ(digits)
    with tenant_context(organization):
        company, _ = Company.objects.get_or_create(
            organization=organization,
            cnpj=cnpj_value,
            defaults=fields,
        )
        changed = False
        for key, value in fields.items():
            if getattr(company, key) != value:
                setattr(company, key, value)
                changed = True
        if changed:
            company.save()
    return company


def ensure_user(
    *,
    email,
    organization,
    access_level,
    cpf,
    first_name,
    last_name,
    is_superuser,
    is_staff,
    areas,
):
    user, _ = User.objects.update_or_create(
        email=email,
        defaults={
            "username": email,
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization,
            "access_level": access_level,
            "cpf": cpf,
            "cnpj": None,
            "is_superuser": is_superuser,
            "is_staff": is_staff,
            "is_active": True,
            "deactivated_at": None,
            "password_redefined": True,
        },
    )
    user.set_password(DEV_PASSWORD)
    user.save()
    user.areas.set(areas)
    return user


@transaction.atomic
def run_seed():
    varzea = ensure_city_hall(
        name="Prefeitura Municipal de Várzea Paulista",
        mayor="Jorge Prefeito",
        document="11222333000181",
    )
    ensure_city_hall(
        name="Prefeitura Municipal de Campo Limpo Paulista",
        mayor="João Prefeito",
        document="60701190000104",
    )
    ensure_city_hall(
        name="Prefeitura Municipal de Jundiaí",
        mayor="José Prefeito",
        document="00000000000191",
    )

    org_primary = ensure_organization(
        city_hall=varzea,
        name="ONG Contabilidade Vitor Toledo",
        owner="Marcos Dono",
        document="52998224725",
    )
    org_secondary = ensure_organization(
        city_hall=varzea,
        name="Fundação Social de Desenvolvimento Social",
        owner="Matheus Dono",
        document="39053344705",
    )

    a1 = ensure_area(
        organization=org_primary,
        city_hall=varzea,
        name="Desenvolvimento social",
        description="Desenvolvimento social",
    )
    a2 = ensure_area(
        organization=org_primary,
        city_hall=varzea,
        name="Desenvolvimento econômico",
        description="Desenvolvimento econômico",
    )
    a3 = ensure_area(
        organization=org_primary,
        city_hall=varzea,
        name="Gestão e Fiscalização",
        description="Gestão e Fiscalização",
    )
    ensure_area(
        organization=org_secondary,
        city_hall=varzea,
        name="Projetos transversais",
        description="Áreas compartilhadas entre programas",
    )

    primary_areas = [a1, a2, a3]

    ensure_user(
        email="admin@admin.com",
        organization=org_primary,
        access_level=User.AccessChoices.MASTER,
        cpf="85351346893",
        first_name="Admin",
        last_name="Master",
        is_superuser=True,
        is_staff=True,
        areas=primary_areas,
    )
    ensure_user(
        email="contador@dev.local",
        organization=org_primary,
        access_level=User.AccessChoices.ORGANIZATION_ACCOUNTANT,
        cpf="11144477735",
        first_name="Ana",
        last_name="Contadora",
        is_superuser=False,
        is_staff=False,
        areas=[a1, a2],
    )

    ensure_company(
        org_primary,
        "24479422000150",
        name="Empresa Contratante",
        street="Rua Fausto Silveira Pires",
        number=93,
        complement=None,
        district="Jardim Primavera",
        city="Várzea Paulista",
        uf=StatesChoices.SP,
        postal_code="13220270",
    )
    ensure_company(
        org_primary,
        "49279736000130",
        name="Empresa Contratada",
        street="Rua Senador Vergueiro",
        number=250,
        complement="Apto 305",
        district="Flamengo",
        city="Rio de Janeiro",
        uf=StatesChoices.RJ,
        postal_code="22220000",
    )
    ensure_company(
        org_primary,
        "21135963000172",
        name="Software Vitor Toledo S.A.",
        street="Rua Xavier da Silveira",
        number=29,
        complement="Apto 901",
        district="Copacabana",
        city="Rio de Janeiro",
        uf=StatesChoices.RJ,
        postal_code="22061010",
    )
    ensure_company(
        org_primary,
        "98521329000100",
        name="Empresa Teste",
        street="Rua Testes",
        number=100,
        complement="Bloco B",
        district="Jardim Testes",
        city="Testópolis",
        uf=StatesChoices.GO,
        postal_code="11110000",
    )

    return {
        "logins": [
            ("admin@admin.com", User.AccessChoices.MASTER, True),
            ("contador@dev.local", User.AccessChoices.ORGANIZATION_ACCOUNTANT, False),
        ],
    }


class Command(BaseCommand):
    help = "Idempotent dev seed: prefeituras, organizações, empresas e dois usuários de teste."

    def handle(self, *args, **options):
        if not getattr(settings, "DEVELOPMENT", False):
            raise CommandError("Este comando só roda com DEVELOPMENT=true.")

        result = run_seed()
        self.stdout.write(self.style.SUCCESS("Seed concluído."))
        self.stdout.write(f"Senha dev: {DEV_PASSWORD!r}")
        for email, level, staff in result["logins"]:
            self.stdout.write(f"  {email}  access={level}  staff={staff}")
