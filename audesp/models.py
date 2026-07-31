from django.db import models

from accounts.models import BaseOrganizationTenantModel, CityHall
from accountability.models import BudgetCommitment
from audesp import secrets as audesp_secrets
from contracts.models import Contract
from utils.models import BaseModel


class AudespSubmission(BaseOrganizationTenantModel):
    """Tracks one built (and optionally submitted) Fase V JSON payload for a
    (contract, fiscal_year). Building/validating happens locally; submission
    to the AUDESP webservice is a later phase (no API client exists yet).

    Retificação (manual §1.2 point 4): resending a *complete* document with
    `retificacao=True` fully replaces the prior submission for the same
    exercício. Retifying an exercício older than the latest submitted one
    cascades server-side -- every later exercício still SUBMITTED/ACCEPTED
    at TCESP flips to `Excluído`. `audesp.services.submit` runs that check
    locally before sending and flips the affected rows to
    `StatusChoices.EXCLUDED` as a side effect, so this table doesn't
    silently go stale relative to what TCESP actually did.
    """

    class AjusteTypeChoices(models.TextChoices):
        CONTRATO_GESTAO = "CONTRATO_GESTAO", "Contrato de Gestão"
        CONVENIO = "CONVENIO", "Convênio"
        TERMO_COLABORACAO = "TERMO_COLABORACAO", "Termo de Colaboração"
        TERMO_FOMENTO = "TERMO_FOMENTO", "Termo de Fomento"
        TERMO_PARCERIA = "TERMO_PARCERIA", "Termo de Parceria"
        DECLARACAO_NEGATIVA = "DECLARACAO_NEGATIVA", "Declaração Negativa"

    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        VALID = "VALID", "Válido"
        INVALID = "INVALID", "Inválido"
        SUBMITTED = "SUBMITTED", "Enviado"
        ACCEPTED = "ACCEPTED", "Aceito"
        REJECTED = "REJECTED", "Rejeitado"
        # Cascaded exclusion (manual §1.2 point 4), not a rejection: this
        # submission was itself fine, but TCESP voided it server-side because
        # a *later* retificação replaced an earlier exercício of the same
        # (contract, ajuste_type). Different remediation than REJECTED --
        # rejected needs a fix before resending, excluded-by-cascade just
        # needs a plain resend of this same exercício.
        EXCLUDED = "EXCLUDED", "Excluído"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="audesp_submissions",
        on_delete=models.CASCADE,
    )
    fiscal_year = models.IntegerField(verbose_name="Exercício")
    ajuste_type = models.CharField(
        verbose_name="Tipo de Ajuste (AUDESP)",
        max_length=20,
        choices=AjusteTypeChoices,
    )
    retificacao = models.BooleanField(
        verbose_name="Retificação",
        default=False,
        help_text="Reenvio integral que substitui a prestação anterior deste "
        "exercício (manual §1.2, item 4). Retificar um exercício anterior ao "
        "último enviado exclui, em cascata, os exercícios posteriores já "
        "enviados/aceitos no TCESP.",
    )
    status = models.CharField(
        verbose_name="Status",
        max_length=10,
        choices=StatusChoices,
        default=StatusChoices.DRAFT,
    )
    payload = models.JSONField(
        verbose_name="Documento JSON",
        help_text="Último payload construído para este (ajuste, exercício)",
    )
    validation_errors = models.JSONField(
        verbose_name="Erros de Validação",
        default=list,
        blank=True,
        help_text="Erros de validação contra o JSON Schema, se houver",
    )
    protocol_number = models.CharField(
        verbose_name="Número de Protocolo",
        max_length=32,
        null=True,
        blank=True,
        help_text="Preenchido após envio bem-sucedido ao webservice AUDESP",
    )
    built_at = models.DateTimeField(verbose_name="Construído em", auto_now_add=True)

    class Meta:
        verbose_name = "Submissão AUDESP"
        verbose_name_plural = "Submissões AUDESP"
        ordering = ("-built_at",)
        indexes = [
            models.Index(fields=["contract", "fiscal_year", "-built_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.contract.name} - {self.fiscal_year} ({self.get_status_display()})"
        )


class AudespCredential(BaseModel):
    """Registers that a TCESP AUDESP login exists for (city_hall, environment)
    — manual §1.2.6: separate credential + "Transmissão Pacotes - Fase V"
    permission per environment (piloto vs produção). The login belongs to
    the órgão concessor (city hall), not the beneficiary entity — a single
    município reports on every organization under it through one AUDESP
    account.

    The actual username/password are never stored here (or anywhere in this
    database) — `get_credentials()` resolves them via `audesp.secrets`,
    which reads `.env` locally or GCP Secret Manager otherwise. This row is
    only a registry of which (city_hall, environment) pairs are configured
    and active.
    """

    class EnvironmentChoices(models.TextChoices):
        PILOTO = "PILOTO", "Piloto"
        PRODUCAO = "PRODUCAO", "Produção"

    city_hall = models.ForeignKey(
        CityHall,
        verbose_name="Prefeitura",
        related_name="audesp_credentials",
        on_delete=models.CASCADE,
    )
    environment = models.CharField(
        verbose_name="Ambiente",
        max_length=8,
        choices=EnvironmentChoices,
    )
    is_active = models.BooleanField(verbose_name="Ativo", default=True)

    class Meta:
        verbose_name = "Credencial AUDESP"
        verbose_name_plural = "Credenciais AUDESP"
        constraints = [
            models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("city_hall", "environment"),
                name="unique_audesp_credential_per_city_hall_environment",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.city_hall} - {self.get_environment_display()}"

    def get_credentials(self):
        """Returns (username, password), resolved through `audesp.secrets`."""
        return audesp_secrets.get_credentials(self.city_hall, self.environment)


class AudespFaseIVSubmission(BaseOrganizationTenantModel):
    """Tracks one built (and optionally submitted) Fase IV JSON payload —
    either an "ajuste" (contract/instrument registration) or an "empenho"
    (budget commitment note linked to an already-registered ajuste). Both
    document types are sent through the same `/f4/enviar-ajuste` endpoint
    (per the official manual, Empenho is a "sub-módulo" of Ajuste, not a
    separate submission path) and share this table's shape/lifecycle, which
    mirrors `AudespSubmission`'s (Fase V) for consistency.

    See AUDESP_FASE_IV_AUDIT.md for what this can and can't do yet — in
    particular, `descritor.codigoEdital` (required on every ajuste payload)
    references a Licitação/Dispensa record this codebase does not register;
    that remains an external prerequisite, same as Fase V's own certidão
    references.
    """

    class DocumentTypeChoices(models.TextChoices):
        AJUSTE = "AJUSTE", "Ajuste"
        EMPENHO = "EMPENHO", "Empenho"

    class StatusChoices(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        VALID = "VALID", "Válido"
        INVALID = "INVALID", "Inválido"
        SUBMITTED = "SUBMITTED", "Enviado"
        ACCEPTED = "ACCEPTED", "Aceito"
        REJECTED = "REJECTED", "Rejeitado"

    contract = models.ForeignKey(
        Contract,
        verbose_name="Ajuste",
        related_name="audesp_fase_iv_submissions",
        on_delete=models.CASCADE,
    )
    budget_commitment = models.ForeignKey(
        BudgetCommitment,
        verbose_name="Empenho",
        related_name="audesp_fase_iv_submissions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Preenchido apenas quando document_type = EMPENHO",
    )
    document_type = models.CharField(
        verbose_name="Tipo de Documento",
        max_length=7,
        choices=DocumentTypeChoices,
    )
    status = models.CharField(
        verbose_name="Status",
        max_length=10,
        choices=StatusChoices,
        default=StatusChoices.DRAFT,
    )
    payload = models.JSONField(
        verbose_name="Documento JSON",
        help_text="Último payload construído para esta submissão",
    )
    validation_errors = models.JSONField(
        verbose_name="Erros de Validação",
        default=list,
        blank=True,
        help_text="Erros de validação contra o JSON Schema, se houver",
    )
    protocol_number = models.CharField(
        verbose_name="Número de Protocolo",
        max_length=32,
        null=True,
        blank=True,
        help_text="Preenchido após envio bem-sucedido ao webservice AUDESP",
    )
    built_at = models.DateTimeField(verbose_name="Construído em", auto_now_add=True)

    class Meta:
        verbose_name = "Submissão AUDESP Fase IV"
        verbose_name_plural = "Submissões AUDESP Fase IV"
        ordering = ("-built_at",)
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(document_type="EMPENHO", budget_commitment__isnull=False)
                    | models.Q(document_type="AJUSTE", budget_commitment__isnull=True)
                ),
                name="fase_iv_empenho_requires_budget_commitment",
            ),
        ]
        indexes = [
            models.Index(fields=["contract", "document_type", "-built_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.contract.name} - {self.get_document_type_display()} ({self.get_status_display()})"
