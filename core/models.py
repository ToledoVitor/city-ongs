from django.db import models
from utils.models import SoftDeleteModel


# Create your models here.
class Project(SoftDeleteModel):
    ...


class CompanyAddress(SoftDeleteModel):
    ...


class Company(SoftDeleteModel):
    name = models.CharField(verbose_name="Name of the company")
    # Mudar para https://pypi.org/project/django-cpf-cnpj/
    # cnpj = models.CharField(verbose_name="Name of the company")
    address = models.ForeignKey(CompanyAddress, on_delete=models.CASCADE)