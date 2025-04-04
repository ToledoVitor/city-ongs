from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from accountability.models import Accountability, Revenue
from accounts.models import BaseModel, Organization
from contracts.models import Contract


class PartnershipTransparency(BaseModel):
    """
    Model to store and display partnership information in the transparency portal.
    This model aggregates information from Contracts and Accountabilities.
    """

    contract = models.OneToOneField(
        Contract,
        verbose_name="Contrato",
        related_name="transparency_info",
        on_delete=models.CASCADE,
    )

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
        related_name="transparency_info",
        on_delete=models.CASCADE,
    )

    last_updated = models.DateTimeField(
        verbose_name="Última atualização",
        auto_now=True,
    )

    is_public = models.BooleanField(
        verbose_name="Visível no portal",
        default=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Informação de Transparência"
        verbose_name_plural = "Informações de Transparência"

    def __str__(self):
        return f"Transparência - {self.contract.name}"

    @property
    def total_value(self):
        return self.contract.total_value

    @property
    def released_value(self):
        return sum(
            revenue.value
            for revenue in Revenue.objects.filter(
                accountability__contract=self.contract,
                status=Revenue.ReviewStatus.APPROVED,
            )
        )

    @property
    def accountability_status(self):
        latest_accountability = (
            Accountability.objects.filter(contract=self.contract)
            .order_by("-year", "-month")
            .first()
        )

        if not latest_accountability:
            return "Não iniciada"

        return latest_accountability.status_label

    @property
    def next_accountability_date(self):
        latest_accountability = (
            Accountability.objects.filter(contract=self.contract)
            .order_by("-year", "-month")
            .first()
        )

        if not latest_accountability:
            return None

        # Calculate next month
        next_month = latest_accountability.month + 1
        next_year = latest_accountability.year

        if next_month > 12:
            next_month = 1
            next_year += 1

        return timezone.datetime(next_year, next_month, 1).date()


class FinancialTransfer(BaseModel):
    """
    Model to track and display financial transfers related to partnerships.
    """

    partnership = models.ForeignKey(
        PartnershipTransparency,
        verbose_name="Parceria",
        related_name="transfers",
        on_delete=models.CASCADE,
    )

    transfer_date = models.DateField(
        verbose_name="Data do repasse",
    )

    value = models.DecimalField(
        verbose_name="Valor",
        max_digits=12,
        decimal_places=2,
    )

    account = models.CharField(
        verbose_name="Conta creditada",
        max_length=255,
    )

    document_type = models.CharField(
        verbose_name="Tipo de instrumento",
        max_length=100,
    )

    document_number = models.CharField(
        verbose_name="Número do instrumento",
        max_length=100,
    )

    document_year = models.IntegerField(
        verbose_name="Ano do instrumento",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Repasse Financeiro"
        verbose_name_plural = "Repasses Financeiros"
        ordering = ["-transfer_date"]

    def __str__(self):
        return f"Repasse - {self.partnership.contract.name} - {self.transfer_date}"


class AccountabilityReport(BaseModel):
    """
    Model to store and display accountability reports in the transparency portal.
    """

    partnership = models.ForeignKey(
        PartnershipTransparency,
        verbose_name="Parceria",
        related_name="accountability_reports",
        on_delete=models.CASCADE,
    )

    accountability = models.OneToOneField(
        Accountability,
        verbose_name="Prestação de contas",
        related_name="transparency_report",
        on_delete=models.CASCADE,
    )

    activities_description = models.TextField(
        verbose_name="Descrição das atividades",
    )

    goals_achievement = models.TextField(
        verbose_name="Comprovação do alcance das metas",
    )

    expected_results = models.TextField(
        verbose_name="Resultados esperados",
    )

    rejection_reason = models.TextField(
        verbose_name="Motivo da rejeição",
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Relatório de Prestação de Contas"
        verbose_name_plural = "Relatórios de Prestação de Contas"

    def __str__(self):
        return f"Relatório - {self.partnership.contract.name} - {self.accountability.month}/{self.accountability.year}"


class IrregularityReport(BaseModel):
    """
    Model to store reports of irregularities in resource application.
    """

    partnership = models.ForeignKey(
        PartnershipTransparency,
        verbose_name="Parceria",
        related_name="irregularity_reports",
        on_delete=models.CASCADE,
    )

    report_date = models.DateTimeField(
        verbose_name="Data do relatório",
        auto_now_add=True,
    )

    description = models.TextField(
        verbose_name="Descrição da irregularidade",
    )

    status = models.CharField(
        verbose_name="Status",
        max_length=20,
        choices=[
            ("PENDING", "Pendente"),
            ("INVESTIGATING", "Em investigação"),
            ("RESOLVED", "Resolvido"),
            ("REJECTED", "Rejeitado"),
        ],
        default="PENDING",
    )

    resolution = models.TextField(
        verbose_name="Resolução",
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Relatório de Irregularidade"
        verbose_name_plural = "Relatórios de Irregularidades"
        ordering = ["-report_date"]

    def __str__(self):
        return f"Irregularidade - {self.partnership.contract.name} - {self.report_date}"
