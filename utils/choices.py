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


class StatesChoices(models.TextChoices):
    AC = "AC", "Acre"
    AL = "AL", "Alagoas"
    AP = "AP", "Amapá"
    AM = "AM", "Amazonas"
    BA = "BA", "Bahia"
    CE = "CE", "Ceará"
    DF = "DF", "Distrito Federal"
    ES = "ES", "Espírito Santo"
    GO = "GO", "Goiás"
    MA = "MA", "Maranhão"
    MT = "MT", "Mato Grosso"
    MS = "MS", "Mato Grosso do Sul"
    MG = "MG", "Minas Gerais"
    PA = "PA", "Pará"
    PB = "PB", "Paraíba"
    PR = "PR", "Paraná"
    PE = "PE", "Pernambuco"
    PI = "PI", "Piauí"
    RJ = "RJ", "Rio de Janeiro"
    RN = "RN", "Rio Grande do Norte"
    RS = "RS", "Rio Grande do Sul"
    RO = "RO", "Rondônia"
    RR = "RR", "Roraima"
    SC = "SC", "Santa Catarina"
    SP = "SP", "São Paulo"
    SE = "SE", "Sergipe"
    TO = "TO", "Tocantins"
