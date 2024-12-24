from django.db import models

from contracts.models import Contract
from utils.models import BaseModel
from simple_history.models import HistoricalRecords


class Report(BaseModel):
    # file
    category = models.CharField(verbose_name="Categoria", max_length=128)
    form = models.CharField(verbose_name="Formato", max_length=128)

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="reports",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
