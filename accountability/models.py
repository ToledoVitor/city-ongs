from django.db import models
from simple_history.models import HistoricalRecords

from accounts.models import Organization, User
from activity.models import ActivityLog
from bank.models import BankAccount
from contracts.choices import NatureChoices
from contracts.models import Contract, ContractItem
from utils.choices import MonthChoices, StatusChoices
from utils.models import BaseModel


class Accountability(BaseModel):
    class ReviewStatus(models.TextChoices):
        WIP = "WIP", "Em Andamento"
        SENT = "SENT", "Enviada para análise"
        CORRECTING = "CORRECTING", "Corrigindo"
        FINISHED = "FINISHED", "Finalizada"

    month = models.IntegerField(
        verbose_name="Mês",
        choices=MonthChoices,
        default=MonthChoices.JAN,
    )
    year = models.IntegerField(
        verbose_name="Ano",
        default=0,
    )

    contract = models.ForeignKey(
        Contract,
        verbose_name="Contrato",
        related_name="accountabilities",
        on_delete=models.CASCADE,
    )
    pendencies = models.CharField(
        verbose_name="Pendências",
        max_length=255,
        null=True,
        blank=True,
    )

    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.WIP,
        max_length=10,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Prestação mês {self.month}"

    @property
    def month_label(self):
        return MonthChoices(self.month).label.capitalize()

    @property
    def is_on_execution(self) -> bool:
        return self.status in {
            Accountability.ReviewStatus.WIP,
            Accountability.ReviewStatus.CORRECTING,
        }

    @property
    def is_sent(self) -> bool:
        return self.status == Accountability.ReviewStatus.SENT

    @property
    def is_finished(self) -> bool:
        return self.status == Accountability.ReviewStatus.FINISHED

    @property
    def status_label(self) -> str:
        return Accountability.ReviewStatus(self.status).label

    @property
    def recent_logs(self):
        accountability_logs = ActivityLog.objects.filter(target_object_id=self.id)

        revenues_ids = [
            str(id) for id in self.revenues.values_list("id", flat=True)[:10]
        ]
        revenues_logs = ActivityLog.objects.filter(
            target_object_id__in=revenues_ids,
        )

        expenses_ids = [
            str(id) for id in self.expenses.values_list("id", flat=True)[:10]
        ]
        expenses_logs = ActivityLog.objects.filter(
            target_object_id__in=expenses_ids,
        )

        combined_querset = (
            accountability_logs | revenues_logs | expenses_logs
        ).distinct()
        return combined_querset.order_by("-created_at")[:10]

    class Meta:
        verbose_name = "Prestação"
        verbose_name_plural = "Prestações"
        unique_together = ("contract", "month", "year")


class AccountabilityFile(BaseModel):
    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Prestação",
        related_name="files",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name="Criado por",
        related_name="accountability_files",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/accountabilities/",
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name="Nome do Arquivo",
        max_length=128,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Prestação {self.id}"

    class Meta:
        verbose_name = "Arquivo de Prestação"
        verbose_name_plural = "Arquivo de Prestações"


class Favored(BaseModel):
    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
        related_name="favoreds",
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name="Nome",
        max_length=128,
    )
    document = models.CharField(
        verbose_name="CPF/CNPJ",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = str(string_doc)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Favorecido"
        verbose_name_plural = "Favorecidos"


class ResourceSource(BaseModel):
    class OriginChoices(models.TextChoices):
        FEDERAL = "FEDERAL", "Federal"
        STATE = "STATE", "Estadual"
        MUNICIPAL = "MUNICIPAL", "Municipal"
        COUNTERPART_PARTNER = "COUNTERPART_PARTNER", "Contrapartida de parceiro"
        PRIVATE_SPONSOR = "PRIVATE_SPONSOR", "Patrocinador privado"
        PARLIAMENTARY = "PARLIAMENTARY", "Emenda Parlamentar"

    class CategoryChoices(models.TextChoices):
        NOT_APPLIABLE = "NOT_APPLIABLE", "Não Aplicavél"
        COOPERATION_AGREEMENT = "COOPERATION_AGREEMENT", "Acordo de Cooperação"
        AGREEMENT = "AGREEMENT", "Convênio"
        COLLABORATION_AGREEMENT = "COLLABORATION_AGREEMENT", "Termo de Colaboração"
        PROMOTION_AGREEMENT = "PROMOTION_AGREEMENT", "Termo de Fomento"
        DONATION_AGREEMENT = "DONATION_AGREEMENT", "Contrato de Doação"
        MANAGEMENT_AGREEMENT = "MANAGEMENT_AGREEMENT", "Contrato de Gestão"
        TRANSFER_AGREEMENT = "TRANSFER_AGREEMENT", "Contrato de Repasse"
        PARTNERSHIP_AGREEMENT = "PARTNERSHIP_AGREEMENT", "Termo de Parceria"

    organization = models.ForeignKey(
        Organization,
        verbose_name="Organização",
        related_name="resource_sources",
        on_delete=models.CASCADE,
    )

    name = models.CharField(verbose_name="Nome da fonte", max_length=64)
    document = models.IntegerField(
        verbose_name="CPF/CNPJ da fonte",
        null=True,
        blank=True,
    )
    contract_number = models.CharField(
        verbose_name="Número do contrato",
        max_length=32,
        null=True,
        blank=True,
    )

    origin = models.CharField(
        verbose_name="Origem da Fonte",
        choices=OriginChoices,
        default=OriginChoices.FEDERAL,
        max_length=19,
    )
    category = models.CharField(
        verbose_name="Categoria",
        choices=CategoryChoices,
        default=CategoryChoices.NOT_APPLIABLE,
        max_length=23,
    )

    class Meta:
        verbose_name = "Fonte de Recurso"
        verbose_name_plural = "Fonte de Recursos"
        unique_together = ("organization", "name")

    def __str__(self) -> str:
        return self.name

    @property
    def origin_label(self) -> str:
        return ResourceSource.OriginChoices(self.origin).label

    @property
    def category_label(self) -> str:
        return ResourceSource.CategoryChoices(self.category).label

    def save(self, *args, **kwargs):
        if self.document is not None:
            string_doc = "".join([i for i in str(self.document) if i.isdigit()])
            self.document = int(string_doc)

        super().save(*args, **kwargs)


class Expense(BaseModel):
    class ReviewStatus(models.TextChoices):
        IN_ANALISIS = "IN_ANALISIS", "Em Análise"
        REJECTED = "REJECTED", "Rejeitada"
        APPROVED = "APPROVED", "Aprovada"

    class LiquidationChoices(models.TextChoices):
        BILL = "BILL", "Boleto"
        CHECK = "CHECK", "Cheque"
        DEBIT_CREDIT_CARD = "DEBIT_CREDIT_CARD", "Cartão Débito/Crédito"
        DIRECT_DEBIT = "DIRECT_DEBIT", "Débito em Conta"
        ELETRONIC_TRANSFER = "ELETRONIC_TRANSFER", "Transferência Eletrônica"
        MONEY = "MONEY", "Dinheiro"
        OBTV = "OBTV", "OBTV"

    class DocumentChoices(models.TextChoices):
        INSURANCE_POLICY = "INSURANCE_POLICY", "Apolice de Seguro"
        DEBIT_NOTICE = "DEBIT_NOTICE", "Aviso de Débito"
        PAY_SLIP = "PAY_SLIP", "Boleto"
        TAX_RECEIPT = "TAX_RECEIPT", "Cupom Fiscal"
        DARF = "DARF", "DARF"
        INVOICE = "INVOICE", "Fatura"
        GPS = "GPS", "GPS"
        GRCS_DOC = "GRCS_DOC", "GRCS ou DOC"
        GRF = "GRF", "GRF"
        GRRF = "GRRF", "GRRF"
        PAYSLIP = "PAYSLIP", "Holerite"
        NF = "NF", "NF"
        NFE = "NFE", "NF-E"
        NFS = "NFS", "NFS"
        NFSE = "NFSE", "NFS-E"
        NF_INVOICES = "NF_INVOICES", "Notas Fiscais (Eletronica, Serviços, etc)"
        OTHERS = "OTHERS", "Outros"
        RECEIPT = "RECEIPT", "Recibo"
        VACATION_RECEIPT = "VACATION_RECEIPT", "Recibo de Férias"
        RPA = "RPA", "RPA"
        TERMINATION_AGREEMENT = "TERMINATION_AGREEMENT", "Termo de Rescisão"

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Prestação",
        related_name="expenses",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.IN_ANALISIS,
        max_length=11,
    )
    pendencies = models.CharField(
        verbose_name="Pendências",
        max_length=255,
        null=True,
        blank=True,
    )

    # flags
    paid = models.BooleanField(verbose_name="Pago?", default=False)
    conciled = models.BooleanField(verbose_name="Conciliado?", default=False)
    planned = models.BooleanField(verbose_name="Planejado?", default=True)

    # specifications
    identification = models.CharField(
        verbose_name="Identificação da Despesa",
        max_length=128,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=256,
        null=True,
        blank=True,
    )
    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    # relations
    source = models.ForeignKey(
        ResourceSource,
        verbose_name="Fonte de Despesa",
        related_name="expenses",
        on_delete=models.CASCADE,
    )
    favored = models.ForeignKey(
        Favored,
        verbose_name="Favorecido",
        related_name="expenses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    item = models.ForeignKey(
        ContractItem,
        verbose_name="Item Relacionado",
        related_name="expenses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    nature = models.CharField(
        verbose_name="Natureza da Despesa",
        choices=NatureChoices.choices,
        max_length=34,
        null=True,
        blank=True,
    )

    # dates
    due_date = models.DateField(
        verbose_name="Vencimento",
        null=True,
        blank=True,
    )
    competency = models.DateField(
        verbose_name="Competência",
    )
    liquidation = models.DateField(
        verbose_name="Liquidação",
        null=True,
        blank=True,
    )
    liquidation_form = models.CharField(
        verbose_name="Forma de Liquidação",
        choices=LiquidationChoices.choices,
        default=LiquidationChoices.ELETRONIC_TRANSFER,
        max_length=18,
    )

    # documents
    document_type = models.CharField(
        verbose_name="Tipo de Documento",
        choices=DocumentChoices.choices,
        max_length=21,
        null=True,
        blank=True,
    )
    document_number = models.CharField(
        verbose_name="Número do documento",
        max_length=64,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"

    @property
    def nature_label(self) -> str:
        if self.nature:
            return NatureChoices(self.nature).label
        return "-"

    @property
    def status_label(self) -> str:
        return Expense.ReviewStatus(self.status).label

    @property
    def document_type_label(self) -> str:
        if self.document_type:
            return Expense.DocumentChoices(self.document_type).label
        return "-"

    @property
    def liquidation_form_label(self) -> str:
        if self.liquidation_form:
            return Expense.LiquidationChoices(self.liquidation_form).label
        return ""

    def __str__(self) -> str:
        return f"Despesa {self.id}"


# TODO: drop model??
class ExpenseAnalysis(BaseModel):
    status = models.CharField(
        verbose_name="Status",
        choices=StatusChoices,
        default=StatusChoices.ANALYZING,
        max_length=22,
    )
    comments = models.CharField(verbose_name="Comentários", max_length=256)
    pending = models.CharField(verbose_name="Pendências", max_length=256)

    reviwer = models.ForeignKey(
        User,
        verbose_name="Usuário",
        related_name="expense_anaysis",
        on_delete=models.CASCADE,
    )
    expense = models.ForeignKey(
        Expense,
        verbose_name="Despesa",
        related_name="expenses_analysis",
        on_delete=models.CASCADE,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Análise {self.id} - {self.status}"

    class Meta:
        verbose_name = "Análise de Despesa"
        verbose_name_plural = "Análise de Despesas"


class Revenue(BaseModel):
    class RevenueSource(models.TextChoices):
        CITY_HALL = "CITY_HALL", "Prefeitura"
        COUNTERPART = "COUNTERPART", "Contrapartida"

    class ReviewStatus(models.TextChoices):
        IN_ANALISIS = "IN_ANALISIS", "Em Análise"
        REJECTED = "REJECTED", "Rejeitada"
        APPROVED = "APPROVED", "Aprovada"

    class Nature(models.TextChoices):
        UNDUE_CREDIT = "UNDUE_CREDIT", "Crédito Indevido"
        BANK_DEPOSIT = "BANK_DEPOSIT", "Depósito Bancário"
        RETURN_DEPOSIT = "RETURN_DEPOSIT", "Depósito para devolução ao Órgão Concedente"
        PAYMENT_REVERSAL = "PAYMENT_REVERSAL", "Estorno de Pagamento"
        FEE_REVERSAL = "FEE_REVERSAL", "Estorno de Tarifas"
        OTHER_REVENUES = (
            "OTHER_REVENUES",
            "Outras Receitas decorrentes da execução do ajuste",
        )
        OWN_RESOURCES = "OWN_RESOURCES", "Recurso próprio da entidade parceira"
        REIMBURSEMENT_INTEREST = (
            "REIMBURSEMENT_INTEREST",
            "Reembolso de Juros, multas, glosas, pagto. Indevido, duplicidade etc",
        )
        FEE_REIMBURSEMENT = "FEE_REIMBURSEMENT", "Reembolso de Tarifas"
        INVESTMENT_INCOME = "INVESTMENT_INCOME", "Rendimento de Aplicação"
        SAVINGS_INCOME = "SAVINGS_INCOME", "Rendimento de Poupança"
        PUBLIC_TRANSFER = "PUBLIC_TRANSFER", "Repasse Público"
        PREVIOUS_BALANCE = "PREVIOUS_BALANCE", "Saldo anterior para acerto"

    accountability = models.ForeignKey(
        Accountability,
        verbose_name="Contabilidade",
        related_name="revenues",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        verbose_name="Status",
        choices=ReviewStatus.choices,
        default=ReviewStatus.IN_ANALISIS,
        max_length=11,
    )
    pendencies = models.CharField(
        verbose_name="Pendências",
        max_length=255,
        null=True,
        blank=True,
    )

    # flags
    paid = models.BooleanField(verbose_name="Pago?", default=False)
    conciled = models.BooleanField(verbose_name="Conciliado?", default=False)

    # specifications
    identification = models.CharField(
        verbose_name="Identificação da Despesa",
        max_length=128,
    )
    observations = models.CharField(
        verbose_name="Observações",
        max_length=256,
        null=True,
        blank=True,
    )
    value = models.DecimalField(
        verbose_name="Valor da Despesa",
        decimal_places=2,
        max_digits=12,
    )

    # dates
    competency = models.DateField(
        verbose_name="Competência",
    )
    receive_date = models.DateField(
        verbose_name="Data de Recebimento",
        null=True,
        blank=True,
    )

    source = models.CharField(
        verbose_name="Fonte de Recurso",
        choices=RevenueSource.choices,
        default=RevenueSource.CITY_HALL,
    )
    bank_account = models.ForeignKey(
        BankAccount,
        verbose_name="Conta Bancária Destino",
        related_name="revenues",
        on_delete=models.CASCADE,
    )
    revenue_nature = models.CharField(
        verbose_name="Natureza da Receita",
        choices=Nature.choices,
        default=Nature.BANK_DEPOSIT,
        max_length=22,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Receita {self.identification}"

    @property
    def source_label(self) -> str:
        return Revenue.RevenueSource(self.source).label

    @property
    def status_label(self) -> str:
        return Revenue.ReviewStatus(self.status).label

    @property
    def revenue_nature_label(self) -> str:
        if self.revenue_nature:
            return Revenue.Nature(self.revenue_nature).label
        return "-"

    class Meta:
        verbose_name = "Receita"
        verbose_name_plural = "Receitas"


class ExpenseFile(BaseModel):
    expense = models.ForeignKey(
        Expense,
        verbose_name="Despesa",
        related_name="files",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name="Criado por",
        related_name="expense_files",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/expenses/",
        null=True,
        blank=True,
    )
    name = models.CharField(
        # TODO: remove null
        verbose_name="Nome do Arquivo",
        max_length=128,
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Despesa {self.id}"

    class Meta:
        verbose_name = "Arquivo de Despesa"
        verbose_name_plural = "Arquivo de Despesas"


class RevenueFile(BaseModel):
    revenue = models.ForeignKey(
        Revenue,
        verbose_name="Recurso",
        related_name="files",
        on_delete=models.CASCADE,
    )
    created_by = models.ForeignKey(
        User,
        verbose_name="Criado por",
        related_name="revenue_files",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    name = models.CharField(
        # TODO: remove null
        verbose_name="Nome do Arquivo",
        max_length=128,
        null=True,
        blank=True,
    )
    file = models.FileField(
        verbose_name="Arquivo",
        upload_to="uploads/revenues/",
        null=True,
        blank=True,
    )

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"Arquivo de Receita {self.id}"

    class Meta:
        verbose_name = "Arquivo de Receita"
        verbose_name_plural = "Arquivo de Receitas"
