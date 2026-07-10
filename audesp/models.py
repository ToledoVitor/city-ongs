from django.db import models

from accounts.models import BaseOrganizationTenantModel
from contracts.models import Contract


class AudespSubmission(BaseOrganizationTenantModel):
    """Tracks one built (and optionally submitted) Fase V JSON payload for a
    (contract, fiscal_year). Building/validating happens locally; submission
    to the AUDESP webservice is a later phase (no API client exists yet)."""

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
