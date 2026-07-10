from datetime import date

from django.db import models
from simple_history.models import HistoricalRecords

from accountability.models import Accountability, AnnualStatement, Revenue
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

        return date(next_year, next_month, 1)


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


class TransparencyChecklist(BaseModel):
    """AUDESP manual §34 "Transparência" - self-assessment mirroring the exact
    checklist the JSON document reports: whether the entity keeps a website,
    and (if so) whether it meets each of the 3 fixed requirement lists below.

    All boolean fields below are only meaningful when `has_website` is True —
    the JSON builder (Phase 4) omits the requirement blocks entirely
    otherwise, matching manual §34.2 rule 1.
    """

    annual_statement = models.OneToOneField(
        AnnualStatement,
        verbose_name="Prestação de Contas Anual",
        related_name="transparency_checklist",
        on_delete=models.CASCADE,
    )
    has_website = models.BooleanField(
        verbose_name="Mantém Sítio na Internet?",
        default=False,
        help_text="Lei Federal nº 12.527/11 (LAI), art. 8º §2º",
    )
    websites = models.JSONField(
        verbose_name="Sítios na Internet",
        default=list,
        blank=True,
    )

    # Art. 7º e 8º §1º (manual §34.1, tabela 1 de 8 itens)
    art7_8_1_organizational_structure = models.BooleanField(
        verbose_name="Competência e Estrutura Organizacional",
        null=True,
        blank=True,
    )
    art7_8_1_contact_information = models.BooleanField(
        verbose_name="Endereço, e-mail, telefones e horários de atendimento",
        null=True,
        blank=True,
    )
    art7_8_1_transfer_records = models.BooleanField(
        verbose_name="Registro de repasses ou transferências de recursos financeiros",
        null=True,
        blank=True,
    )
    art7_8_1_expense_records = models.BooleanField(
        verbose_name="Registros de despesas realizadas com recursos públicos",
        null=True,
        blank=True,
    )
    art7_8_1_procurement_information = models.BooleanField(
        verbose_name="Informações sobre contratações de bens e serviços",
        null=True,
        blank=True,
    )
    art7_8_1_goals_tracking_information = models.BooleanField(
        verbose_name="Informações para acompanhamento de programas/ações/metas",
        null=True,
        blank=True,
    )
    art7_8_1_faq = models.BooleanField(
        verbose_name="Respostas a perguntas mais frequentes da sociedade",
        null=True,
        blank=True,
    )
    art7_8_1_audit_results = models.BooleanField(
        verbose_name="Resultado de inspeções, auditorias e prestações de contas",
        null=True,
        blank=True,
    )

    # Art. 8º §3º (manual §34.1, tabela 2 de 6 itens)
    art8_3_content_search_tool = models.BooleanField(
        verbose_name="Ferramenta de pesquisa de conteúdo",
        null=True,
        blank=True,
    )
    art8_3_open_format_reports = models.BooleanField(
        verbose_name="Geração de relatórios em formatos eletrônicos abertos",
        null=True,
        blank=True,
    )
    art8_3_automated_external_access = models.BooleanField(
        verbose_name="Acesso automatizado por sistemas externos em formatos abertos",
        null=True,
        blank=True,
    )
    art8_3_discloses_data_structure_formats = models.BooleanField(
        verbose_name="Divulga os formatos utilizados na estruturação da informação",
        null=True,
        blank=True,
    )
    art8_3_ensures_authenticity_integrity = models.BooleanField(
        verbose_name="Garante autenticidade e integridade das informações",
        null=True,
        blank=True,
    )
    art8_3_periodic_updates = models.BooleanField(
        verbose_name="Atualização periódica",
        null=True,
        blank=True,
    )

    # Divulgação das Informações (manual §34.1, tabela 3 de 10 itens)
    disclosure_updated_bylaws = models.BooleanField(
        verbose_name="Estatuto Social atualizado",
        null=True,
        blank=True,
    )
    disclosure_agreements = models.BooleanField(
        verbose_name="Ajustes (Termo de Parceria, Convênio, etc.)",
        null=True,
        blank=True,
    )
    disclosure_work_plan = models.BooleanField(
        verbose_name="Plano de Trabalho",
        null=True,
        blank=True,
    )
    disclosure_officers_list = models.BooleanField(
        verbose_name="Relação Nominal dos Dirigentes",
        null=True,
        blank=True,
    )
    disclosure_service_providers_list = models.BooleanField(
        verbose_name="Lista de prestadores de serviços e valores pagos",
        null=True,
        blank=True,
    )
    disclosure_individualized_compensation = models.BooleanField(
        verbose_name="Remuneração individualizada de dirigentes e empregados",
        null=True,
        blank=True,
    )
    disclosure_financial_statements = models.BooleanField(
        verbose_name="Balanços e Demonstrações Contábeis",
        null=True,
        blank=True,
    )
    disclosure_purchasing_regulation = models.BooleanField(
        verbose_name="Regulamento de Compras",
        null=True,
        blank=True,
    )
    disclosure_hiring_regulation = models.BooleanField(
        verbose_name="Regulamento de Contratação de Pessoal",
        null=True,
        blank=True,
    )
    disclosure_sic_statistical_report = models.BooleanField(
        verbose_name="Relatório estatístico de atendimento pelo SIC",
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Checklist de Transparência (AUDESP)"
        verbose_name_plural = "Checklists de Transparência (AUDESP)"

    def __str__(self):
        return f"Checklist de Transparência - {self.annual_statement}"
