from django.db import models


class MonthChoices(models.IntegerChoices):
    JAN = 1, "janeiro"
    FEB = 2, "fevereiro"
    MAR = 3, "março"
    APR = 4, "abril"
    MAY = 5, "maio"
    JUN = 6, "junho"
    JUL = 7, "julho"
    AUG = 8, "agosto"
    SEP = 9, "setembro"
    OCT = 10, "outubro"
    NOV = 11, "novembro"
    DEC = 12, "dezembro"


class StatusChoices(models.TextChoices):
    ANALYZING = "ANALYZING", "em análise"
    CORRECTING = "CORRECTING", "correção"
    APPROVED = "APPROVED", "aprovado"
    APPROVED_WITH_PENDENCE = "APPROVED_WITH_PENDENCE", "aprovado com ressalva"
    REJECTED = "REJECTED", "rejeitado"
