from django.db.models import IntegerChoices, TextChoices


class AudespDocumentTypeChoices(IntegerChoices):
    """Creditor document type, per AUDESP Fase V manual §7/§8/§9/§12/§16 ("credor" triple)."""

    CPF = 1, "CPF"
    CNPJ = 2, "CNPJ"
    RNE = 3, "RNE"


class AudespFundingSourceTypeChoices(IntegerChoices):
    """Manual §9/§11/§12/§17 "fonte_recurso_tipo" — full list per JSON Schema v1.14."""

    TREASURY = 1, "Recursos do Tesouro"
    STATE_TRANSFERS_EARMARKED = 2, "Transferências e Convênios Estaduais - Vinculados"
    SPECIAL_FUNDS_OWN_RESOURCES_EARMARKED = (
        3,
        "Recursos Próprios de Fundos Especiais de Despesa - Vinculados",
    )
    INDIRECT_ADMINISTRATION_OWN_RESOURCES = (
        4,
        "Recursos Próprios da Administração Indireta",
    )
    FEDERAL_TRANSFERS_EARMARKED = 5, "Transferências e Convênios Federais - Vinculados"
    OTHER_FUNDING_SOURCES = 6, "Outras Fontes de Recursos"
    CREDIT_OPERATIONS = 7, "Operações de Crédito"
    INDIVIDUAL_PARLIAMENTARY_AMENDMENTS = (
        8,
        "Emendas Parlamentares Individuais - Legislativo Municipal",
    )
    TREASURY_PRIOR_YEARS = 91, "Tesouro - Exercícios Anteriores"
    STATE_TRANSFERS_EARMARKED_PRIOR_YEARS = (
        92,
        "Transferências e Convênios Estaduais - Vinculados - Exercícios Anteriores",
    )
    SPECIAL_FUNDS_OWN_RESOURCES_EARMARKED_PRIOR_YEARS = (
        93,
        "Recursos Próprios de Fundos Especiais de Despesa - Vinculados - Exercícios Anteriores",
    )
    INDIRECT_ADMINISTRATION_OWN_RESOURCES_PRIOR_YEARS = (
        94,
        "Recursos Próprios da Administração Indireta - Exercícios Anteriores",
    )
    FEDERAL_TRANSFERS_EARMARKED_PRIOR_YEARS = (
        95,
        "Transferências e Convênios Federais - Vinculados - Exercícios Anteriores",
    )
    OTHER_FUNDING_SOURCES_PRIOR_YEARS = (
        96,
        "Outras Fontes de Recursos - Exercícios Anteriores",
    )
    CREDIT_OPERATIONS_PRIOR_YEARS = (
        97,
        "Operações de Crédito - Exercícios Anteriores",
    )
    INDIVIDUAL_PARLIAMENTARY_AMENDMENTS_PRIOR_YEARS = (
        98,
        "Emendas Parlamentares Individuais - Exercícios Anteriores",
    )


class AudespExpenseCategoryTypeChoices(IntegerChoices):
    """Manual §8 "categoria_despesas_tipo" — full list per JSON Schema v1.14.

    No value 75 (removed in schema v1.9 — was "Utilidades Públicas - Gás").
    """

    PERMANENT_GOODS_COMPUTER_EQUIPMENT = (
        1,
        "Bens e Materiais Permanentes - Bens e Equipamentos de Informática",
    )
    PERMANENT_GOODS_HOSPITAL_EQUIPMENT = (
        2,
        "Bens e Materiais Permanentes - Bens e Equipamentos Hospitalares",
    )
    PERMANENT_GOODS_OTHER = (
        3,
        "Bens e Materiais Permanentes - Outros Bens e Materiais Permanentes",
    )
    FINANCIAL_BANKING_FEES_PAID = (
        4,
        "Despesas Financeiras e Bancárias - Despesas Bancárias Pagas",
    )
    FINANCIAL_BANKING_IOF_PAID = 5, "Despesas Financeiras e Bancárias - IOF Pago"
    FINANCIAL_BANKING_INTEREST_PAID = (
        6,
        "Despesas Financeiras e Bancárias - Juros Pagos",
    )
    FINANCIAL_BANKING_OTHER = (
        7,
        "Despesas Financeiras e Bancárias - Outras Despesas Financeiras e Bancárias",
    )
    MISCELLANEOUS = 8, "Diversos - Diversos"
    ADMINISTRATIVE_FUEL = 9, "Gastos Administrativos - Combustível"
    ADMINISTRATIVE_PARKING_TRANSPORT_TAXI = (
        10,
        "Gastos Administrativos - Estacionamento/Condução/Táxi",
    )
    ADMINISTRATIVE_OFFICE_SUPPLIES_MAIL_COPIES = (
        11,
        "Gastos Administrativos - Material de Expediente/Correio/Fotocópias",
    )
    ADMINISTRATIVE_INSURANCE = 12, "Gastos Administrativos - Seguros"
    ADMINISTRATIVE_TRAVEL = (
        13,
        "Gastos Administrativos - Viagens (Hotel/Passagens Aéreas/Pass.Rodoviárias)",
    )
    ADMINISTRATIVE_OTHER = (
        14,
        "Gastos Administrativos - Outros Gastos Administrativos",
    )
    FOODSTUFFS = 15, "Gêneros Alimentícios - Gêneros Alimentícios"
    LEASE_AMBULANCES = 16, "Locação - Ambulâncias"
    LEASE_MISCELLANEOUS = 17, "Locação - Diversas"
    LEASE_COMPUTER_EQUIPMENT = 18, "Locação - Equipamento de Informática"
    LEASE_HOSPITAL_EQUIPMENT = 19, "Locação - Equipamento Médico Hospitalar"
    LEASE_REAL_ESTATE = 20, "Locação - Imóvel"
    LEASE_LAUNDRY_LINEN = 21, "Locação - Lavanderia e Enxoval"
    LEASE_SOFTWARE_SYSTEM = 22, "Locação - Sistema de Software"
    LEASE_VEHICLES = 23, "Locação - Veículos"
    MAINTENANCE_COMPUTER_EQUIPMENT = 24, "Manutenção - Equipamento de Informática"
    MAINTENANCE_HOSPITAL_EQUIPMENT = (
        25,
        "Manutenção - Equipamento Médico Hospitalar",
    )
    MAINTENANCE_BUILDING = 26, "Manutenção - Predial e Imobiliário"
    MAINTENANCE_VEHICLES = 27, "Manutenção - Veículos"
    MAINTENANCE_OTHER = 28, "Manutenção - Outras Manutenções"
    MATERIALS_HYGIENE_CLEANING_UNIFORMS = (
        29,
        "Materiais - Material de Higienização e Limpeza/Uniformes",
    )
    MATERIALS_EDUCATIONAL = 30, "Materiais - Material Didático"
    MATERIALS_SPORTS = 31, "Materiais - Material Esportivo"
    MATERIALS_OTHER = 32, "Materiais - Outros Materiais"
    MEDICAL_HOSPITAL_SUPPLIES = (
        33,
        "Material Médico e Hospitalar - Material Médico e Hospitalar",
    )
    MEDICINES = 34, "Medicamentos - Medicamentos"
    HR_THIRTEENTH_SALARY = 35, "Recursos Humanos - 13º Salário"
    HR_APPRENTICES = 36, "Recursos Humanos - Aprendizes"
    HR_MEDICAL_ASSISTANCE = 37, "Recursos Humanos - Assistência Médica"
    HR_ADVANCE_NOTICE = 38, "Recursos Humanos - Aviso Prévio"
    HR_INSS_EMPLOYER_SHARE = (
        39,
        "Recursos Humanos - Contribuição ao INSS - Cota Patronal",
    )
    HR_PIS_CONTRIBUTION = 40, "Recursos Humanos - Contribuição ao PIS"
    HR_TRAINING_COURSES = 41, "Recursos Humanos - Cursos/Treinamento/Reciclagem"
    HR_MANAGEMENT_SALARY = 42, "Recursos Humanos - Diretoria (Salários e Ordenados)"
    HR_INTERNS = 43, "Recursos Humanos - Estagiários"
    HR_VACATIONS = 44, "Recursos Humanos - Férias"
    HR_FGTS = 45, "Recursos Humanos - FGTS"
    HR_BONUSES = 46, "Recursos Humanos - Gratificações"
    HR_SEVERANCE = 47, "Recursos Humanos - Indenizações"
    HR_INSS = 48, "Recursos Humanos - INSS"
    HR_IRRF = 49, "Recursos Humanos - IRRF"
    HR_FGTS_TERMINATION_FINE = 50, "Recursos Humanos - Multa Rescisória FGTS"
    HR_SALARIES_AND_WAGES = (
        51,
        "Recursos Humanos - Salários e Ordenados (Exceto Diretoria)",
    )
    HR_FOOD_VOUCHER = 52, "Recursos Humanos - Vale Alimentação"
    HR_MEAL_VOUCHER = 53, "Recursos Humanos - Vale Refeição"
    HR_TRANSPORTATION_VOUCHER = 54, "Recursos Humanos - Vale Transporte"
    HR_OTHER = 55, "Recursos Humanos - Outras Despesas de Recursos Humanos"
    THIRD_PARTY_COMMON_WASTE_COLLECTION = (
        56,
        "Serviços de Terceiros - Coleta de Lixo Comum",
    )
    THIRD_PARTY_HOSPITAL_WASTE_COLLECTION = (
        57,
        "Serviços de Terceiros - Coleta de Lixo Hospitalar",
    )
    THIRD_PARTY_ACCOUNTING_CONSULTING = (
        58,
        "Serviços de Terceiros - Consultoria/Assessoria Contábil",
    )
    THIRD_PARTY_LEGAL_CONSULTING = (
        59,
        "Serviços de Terceiros - Consultoria/Assessoria Jurídica",
    )
    THIRD_PARTY_CLEANING_MAINTENANCE = (
        60,
        "Serviços de Terceiros - Limpeza e Conservação",
    )
    THIRD_PARTY_CONSTRUCTION_RENOVATION = 61, "Serviços de Terceiros - Obras/Reformas"
    THIRD_PARTY_OTHER_INDIVIDUAL = (
        62,
        "Serviços de Terceiros - Outros Serviços de Terceiros Pessoa Física",
    )
    THIRD_PARTY_OTHER_LEGAL_ENTITY = (
        63,
        "Serviços de Terceiros - Outros Serviços de Terceiros Pessoa Jurídica",
    )
    THIRD_PARTY_ADVERTISING = (
        64,
        "Serviços de Terceiros - Publicidade e Propaganda",
    )
    THIRD_PARTY_DIAGNOSTIC_SUPPORT = (
        65,
        "Serviços de Terceiros - Serviço de Apoio Diagnóstico Terapêutico (SADT)",
    )
    THIRD_PARTY_AUDIT_SERVICES = 66, "Serviços de Terceiros - Serviços de Auditoria"
    THIRD_PARTY_IT_SERVICES = (
        67,
        "Serviços de Terceiros - Serviços de Tecnologia da Informação (TI)",
    )
    THIRD_PARTY_SECURITY = 68, "Serviços de Terceiros - Vigilância"
    MEDICAL_SERVICES_INDIVIDUAL = (
        69,
        "Serviços Médicos - Serviços Médicos Pessoa Física",
    )
    MEDICAL_SERVICES_LEGAL_ENTITY = (
        70,
        "Serviços Médicos - Serviços Médicos Pessoa Jurídica",
    )
    UTILITIES_WATER_SEWAGE = 71, "Utilidades Públicas - Água e Esgoto"
    UTILITIES_ELECTRICITY = 72, "Utilidades Públicas - Força e Luz"
    UTILITIES_INTERNET_CABLE_TV = 73, "Utilidades Públicas - Internet/TV a Cabo"
    UTILITIES_TELEPHONE = 74, "Utilidades Públicas - Telefones"
    UTILITIES_OTHER = 76, "Utilidades Públicas - Outras Utilidades Públicas"
    AGREEMENTS_SUS_SERVICES = (
        77,
        "Despesas de Convênios - Contratualização de Serviços do SUS",
    )
    MAINTENANCE_FURNITURE_EQUIPMENT = (
        78,
        "Manutenção - Manutenção de Mobiliário e Equipamentos",
    )
    MATERIALS_HYGIENE_CLEANING = 79, "Materiais - Material de Higienização e Limpeza"
    MATERIALS_UNIFORMS = 80, "Materiais - Uniformes"
    MATERIALS_SAFETY_EQUIPMENT = (
        81,
        "Materiais - Equipamentos de Segurança do Trabalho (EPI)",
    )
    MATERIALS_LINEN = 82, "Materiais - Enxoval"
    HR_DENTAL_ASSISTANCE = 83, "Recursos Humanos - Assistência Odontológica"
    HR_INSURANCE = 84, "Recursos Humanos - Seguros"
    UTILITIES_COOKING_GAS = 85, "Utilidades Públicas - Gás de Cozinha"
    CONSUMABLE_MATERIALS_TOYS = 86, "Materiais de Consumo - Brinquedos"
    TAXES_STATE = (
        87,
        "Tributos - Estaduais (ICMS/IPVA/ITCMD/Taxas e Outros)",
    )
    TAXES_FEDERAL = (
        88,
        "Tributos - Federais (IRRF/PIS/COFINS/CSLL/ITR/IOF/Taxas e Outros)",
    )
    TAXES_MUNICIPAL = 89, "Tributos - Municipais (IPTU/ISS/ITBI/Taxas e Outros)"


class AudespPublicationVehicleChoices(IntegerChoices):
    """Manual §22.1 "tipo_veiculo_publicacao" — shared across §22/23/28/29/30."""

    MUNICIPAL_OFFICIAL_GAZETTE = 1, "Diário Oficial do Município"
    STATE_OFFICIAL_GAZETTE = 2, "Diário Oficial do Estado"
    FEDERAL_OFFICIAL_GAZETTE = 3, "Diário Oficial da União"
    ELECTRONIC_COURT_GAZETTE = 4, "Diário da Justiça Eletrônico"
    NATIONAL_PUBLIC_PROCUREMENT_PORTAL = 5, "Portal Nacional de Compras Públicas"
    NATIONAL_CIRCULATION_NEWSPAPER = 6, "Jornal de grande circulação nacional"
    REGIONAL_CIRCULATION_NEWSPAPER = 7, "Jornal de grande circulação regional/municipal"
    PUBLIC_BULLETIN_BOARD = 8, "Quadro ou mural de acesso público"
    DIRECT_ADMINISTRATION_WEBSITE = 9, "Site da administração direta na Internet"
    OTHER = 10, "Outros"


class NatureChoices(TextChoices):
    # Permanent Goods and Materials
    PERMANENT_GOODS_AND_MATERIALS = (
        "PERMANENT_GOODS_AND_MATERIALS",
        "Bens e Materiais permanentes",
    )
    COMPUTER_GOODS_AND_EQUIPMENT = (
        "COMPUTER_GOODS_AND_EQUIPMENT",
        "Bens e equipamentos de informática",
    )
    HOSPITAL_GOODS_AND_EQUIPMENT = (
        "HOSPITAL_GOODS_AND_EQUIPMENT",
        "Bens e equipamentos hospitalares",
    )

    # Fuel
    FUEL = "FUEL", "Combustível"

    # Financial and banking expenses
    BANKING_EXPENSES = "BANKING_EXPENSES", "Despesas bancárias"
    BANKING_IOF = "BANKING_IOF", "IOF"
    BANKING_IRRF = "BANKING_IRRF", "IRRF"
    INTEREST = "INTEREST", "Juros"

    # Foodstuffs
    FOODSTUFFS = "FOODSTUFFS", "Gêneros Alimentícios"

    # Real Estate Lease
    REAL_ESTATE_LEASE = "REAL_ESTATE_LEASE", "Locação de Imóveis"

    # Miscellaneous Leases
    AMBULANCES = "AMBULANCES", "Ambulâncias"
    COMPUTER_EQUIPMENT = "COMPUTER_EQUIPMENT", "Equipamento de informática"
    HOSPITCAL_MEDICAL_EQUIPMENT = (
        "HOSPITCAL_MEDICAL_EQUIPMENT",
        "Equipamento médico hospitalar",
    )
    LAUNDRY_LINEN = "LAUNDRY_LINEN", "Lavanderia e enxoval"
    CAR_LEASE = "CAR_LEASE", "Locação de Carro"
    MISCELLANOUS_LEASES = "MISCELLANOUS_LEASES", "Locações Diversas"
    SOFTWARE_SYSTEM = "SOFTWARE_SYSTEM", "Sistema de software"

    # Medical and Hospital Supplies
    MEDICAL_HOSPITAL_SUPPLIES = (
        "MEDICAL_HOSPITAL_SUPPLIES",
        "Material Médico e Hospitalar",
    )

    # Medicines
    MEDICINES = "MEDICINES", "Medicamentos"

    # Works
    WORKS = "WORKS", "Obras"

    # Other expenses
    OTHER_ADMINISTRATIVE_EXPENSES = (
        "OTHER_ADMINISTRATIVE_EXPENSES",
        "Despesas Administrativas",
    )
    RETURN_OF_FUNDS = (
        "RETURN_OF_FUNDS",
        "Devolução de Recurso ao Órgão Concedente",
    )
    PARKING_DRIVING_TAXI = (
        "PARKING_DRIVING_TAXI",
        "Estacionamento/condução/táxi",
    )
    IPTU = "IPTU", "IPTU"
    TAXES_FEES_CONTRIBUTIONS = (
        "TAXES_FEES_CONTRIBUTIONS",
        "Impostos, Taxas e Contribuições",
    )
    OTHER_EXPENSES = "OTHER_EXPENSES", "Outras despesas - Diversos"
    INSURANCE = "INSURANCE", "Seguros"
    TRAVEL_TICKET_STAY = "TRAVEL_TICKET_STAY", "Viagens (passagem, hospedagem)"

    # Other Consumables
    COOKING_GAS = "COOKING_GAS", "Gás de Cozinha"
    COMPUTER_SUPPLIES = "COMPUTER_SUPPLIES", "Materiais de Informática"
    MATERIALS_FOR_SMALL_REPAIRS = (
        "MATERIALS_FOR_SMALL_REPAIRS",
        "Materiais para Pequenos Reparos",
    )
    EDUCATIONAL_MATERIAL = "EDUCATIONAL_MATERIAL", "Material Pedagógico"
    HYGIENE_CLEANING_SUPPLIES_UNIFORMS = (
        "HYGIENE_CLEANING_SUPPLIES_UNIFORMS",
        "Material de Higiene/Limpeza/Uniformes",
    )
    SPORTS_EQUIPMENTS = "SPORTS_EQUIPMENTS", "Material esportivo"
    UTENSILS = "UTENSILS", "Utensílios"
    OFFICE_SUPPLIES_1 = "OFFICE_SUPPLIES_1", "Materiais de Expediente"
    OFFICE_SUPPLIES_2 = "OFFICE_SUPPLIES_2", "Material de Escritório"
    OFFICE_SUPPLIES_3 = (
        "OFFICE_SUPPLIES_3",
        "Material de expediente/correio/fotocópias",
    )
    OTHER_CONSUMABLES = "OTHER_CONSUMABLES", "Outros Materiais de Consumo"

    # Other Third-Party Services
    COMMON_WASTE_COLLECT = "COMMON_WASTE_COLLECT", "Coleta de lixo comum"
    HOSPITAL_WASTE_COLLECT = (
        "HOSPITAL_WASTE_COLLECT",
        "Coleta de lixo hospitalar",
    )
    CONSULTING_LEGAL_ADVICE = (
        "CONSULTING_LEGAL_ADVICE",
        "Consultoria/assessoria jurídica",
    )
    CLEANING_MAINTENANCE = "CLEANING_MAINTENANCE", "Limpeza e conservação"
    MAINTENANCE_HOSPITAL_EQUIPMENT = (
        "MAINTENANCE_HOSPITAL_EQUIPMENT",
        "Manutenção - Equipamento Médico Hospitalar",
    )
    MAINTENANCE_COMPUTER_EQUIPMENT = (
        "MAINTENANCE_COMPUTER_EQUIPMENT",
        "Manutenção - Equipamento de Informática",
    )
    MAINTENANCE_BUILDING = (
        "MAINTENANCE_BUILDING",
        "Manutenção - predial e Imobiliário",
    )
    MAINTENANCE_VEHICLE = "MAINTENANCE_VEHICLE", "Manutenção de veículos"
    CONSTRUCTION = "CONSTRUCTION", "Obras"
    MAINTENANCE_OTHERS = "MAINTENANCE_OTHERS", "Outras Manutenções"
    LEGAL_THIRD_PARTY_SERVICES = (
        "LEGAL_THIRD_PARTY_SERVICES",
        "Outros serviços de terceiros pessoa jurídica",
    )
    ADVERTISING_PUBILICITY = (
        "ADVERTISING_PUBILICITY",
        "Publicidade e propaganda",
    )
    THERAPEUTIC_SUPPORT_SERVICE = (
        "THERAPEUTIC_SUPPORT_SERVICE",
        "Serviço de apoio diagnóstico terapêutico (sadt)",
    )
    SERVICES_ACCOUNTING = "SERVICES_ACCOUNTING", "Serviços Contábeis"
    SERVICES_AUDITING = "SERVICES_AUDITING", "Serviços de auditoria"
    SERVIECS_IT = "SERVIECS_IT", "Serviços de tecnologia da informação (TI)"
    SERVICES_SURVEILLANCES = "SERVICES_SURVEILLANCES", "Vigilância"

    # Human Resources (5)
    THIRTHEENTH_SALARY = "THIRTHEENTH_SALARY", "13º Salário"
    APPRENTICES = "APPRENTICES", "Aprendizes"
    MEDICAL_ASSISTENCE = "MEDICAL_ASSISTENCE", "Assistência médica"
    ADVANCE_NOTICE = "ADVANCE_NOTICE", "Aviso prévio"
    BENEFITS = "BENEFITS", "Benefícios"
    INTERNSHIP_ALLOWANCE = (
        "INTERNSHIP_ALLOWANCE",
        "Bolsa Auxílio - estagiários",
    )
    INSS_CONTRIBUTION_SHARE = (
        "INSS_CONTRIBUTION_SHARE",
        "Contribuição ao INSS - Cota Patronal",
    )
    PIS_CONTRIBUTION = "PIS_CONTRIBUTION", "Contribuição ao PIS"
    SOCIAL_CONTRIBUTIONS = "SOCIAL_CONTRIBUTIONS", "Contribuições Sociais"
    COURSES_TRAINING_RETRAINING = (
        "COURSES_TRAINING_RETRAINING",
        "Cursos/treinamento/reciclagem",
    )
    PERSONNEL_EXPENSES = "PERSONNEL_EXPENSES", "Despesas com Pessoal"
    COLLECTIVE_BARGAINING = "COLLECTIVE_BARGAINING", "Dissídio coletivo"
    SOCIAL_CHARGES = "SOCIAL_CHARGES", "Encargos Sociais"
    FGTS = "FGTS", "FGTS"
    RESERVE_FUND = "RESERVE_FUND", "Fundo de Reserva"
    VACATIONS = "VACATIONS", "Férias"
    BONUSES = "BONUSES", "Gratificações"
    HR_INSS = "HR_INSS", "INSS"
    HR_IRRF = "HR_IRRF", "IRRF"
    COMPENSATIONS = "COMPENSATIONS", "Indenizações"
    TERMINATION_EMPLOYMENT_CONTRACT = (
        "TERMINATION_EMPLOYMENT_CONTRACT",
        "Rescisão de Contrato de Trabalho - TRCT",
    )
    MISCELLANOUS_WITHHOLDINGS = (
        "MISCELLANOUS_WITHHOLDINGS",
        "Retenções Diversas",
    )
    MANAGEMENT_SALARY = (
        "MANAGEMENT_SALARY",
        "Salário diretoria (salários e ordenados)",
    )
    SALARIES_AND_WAGES = (
        "SALARIES_AND_WAGES",
        "Salários e ordenados (exceto diretoria)",
    )
    UNIFORMS = "UNIFORMS", "Uniformes"
    FOOD_VOUCHERS = "FOOD_VOUCHERS", "Vale Alimentação"
    MEAL_VOUCHERS = "MEAL_VOUCHERS", "Vale Refeição"
    TRANSPORTATION_VOUCHERS = "TRANSPORTATION_VOUCHERS", "Vale Transporte"

    # Human Resources
    INTERN_REMUNERATION = "INTERN_REMUNERATION", "Remuneração de Estagiários"
    SERVICES_PF_THIRD_PARTIES = (
        "SERVICES_PF_THIRD_PARTIES",
        "Serviços Prestados por Terceiro - PF",
    )
    SERVICES_PJ_THIRD_PARTIES = (
        "SERVICES_PJ_THIRD_PARTIES",
        "Serviços Prestados por Terceiro - PJ",
    )

    # Medical services
    MEDICAL_SERVICES = "MEDICAL_SERVICES", "Serviços médicos (*)"
    MEDICAL_SERVICES_FOR_INDIVIDUALS = (
        "MEDICAL_SERVICES_FOR_INDIVIDUALS",
        "Serviços médicos pessoa física",
    )
    MEDICAL_SERVICES_FOR_ENTITIES = (
        "MEDICAL_SERVICES_FOR_ENTITIES",
        "Serviços médicos pessoa jurídica",
    )

    # Public Utilities (7)
    PUBLIC_ADMINISTRATIVE_EXPENSES = (
        "PUBLIC_ADMINISTRATIVE_EXPENSES",
        "Despesas Administrativas",
    )
    ELECTRICITY = "ELECTRICITY", "Energia Elétrica"
    INTERNET_TV = "INTERNET_TV", "Internet/TV a cabo"
    TELEPHONE = "TELEPHONE", "Telefone"
    PUBLIC_UTILITIES = "PUBLIC_UTILITIES", "Utilidade Publica"
    WATER_SEWAGE = "WATER_SEWAGE", "Água e Esgoto"


class NatureCategories:
    PERMANENT_GOODS = [
        NatureChoices.PERMANENT_GOODS_AND_MATERIALS,
        NatureChoices.COMPUTER_GOODS_AND_EQUIPMENT,
        NatureChoices.HOSPITAL_GOODS_AND_EQUIPMENT,
    ]

    FUEL = [
        NatureChoices.FUEL,
    ]

    FINANCIAL_AND_BANKING = [
        NatureChoices.BANKING_EXPENSES,
        NatureChoices.BANKING_IOF,
        NatureChoices.BANKING_IRRF,
        NatureChoices.INTEREST,
    ]

    FOODSTUFFS = [
        NatureChoices.FOODSTUFFS,
    ]

    REAL_STATE = [
        NatureChoices.REAL_ESTATE_LEASE,
    ]

    MISCELLANEOUS = [
        NatureChoices.AMBULANCES,
        NatureChoices.COMPUTER_EQUIPMENT,
        NatureChoices.HOSPITCAL_MEDICAL_EQUIPMENT,
        NatureChoices.LAUNDRY_LINEN,
        NatureChoices.CAR_LEASE,
        NatureChoices.MISCELLANOUS_LEASES,
        NatureChoices.SOFTWARE_SYSTEM,
    ]

    MEDICAL_AND_HOSPITAL = [
        NatureChoices.MEDICAL_HOSPITAL_SUPPLIES,
    ]

    MEDICINES = [
        NatureChoices.MEDICINES,
    ]

    WORKS = [
        NatureChoices.WORKS,
    ]

    OTHER_EXPENSES = [
        NatureChoices.OTHER_ADMINISTRATIVE_EXPENSES,
        NatureChoices.RETURN_OF_FUNDS,
        NatureChoices.PARKING_DRIVING_TAXI,
        NatureChoices.IPTU,
        NatureChoices.TAXES_FEES_CONTRIBUTIONS,
        NatureChoices.OTHER_EXPENSES,
        NatureChoices.INSURANCE,
        NatureChoices.TRAVEL_TICKET_STAY,
    ]

    OTHER_CONSUMABLES = [
        NatureChoices.COOKING_GAS,
        NatureChoices.COMPUTER_SUPPLIES,
        NatureChoices.MATERIALS_FOR_SMALL_REPAIRS,
        NatureChoices.EDUCATIONAL_MATERIAL,
        NatureChoices.HYGIENE_CLEANING_SUPPLIES_UNIFORMS,
        NatureChoices.SPORTS_EQUIPMENTS,
        NatureChoices.UTENSILS,
        NatureChoices.OFFICE_SUPPLIES_1,
        NatureChoices.OFFICE_SUPPLIES_2,
        NatureChoices.OFFICE_SUPPLIES_3,
        NatureChoices.OTHER_CONSUMABLES,
    ]

    OTHER_THIRD_PARTY = [
        NatureChoices.COMMON_WASTE_COLLECT,
        NatureChoices.HOSPITAL_WASTE_COLLECT,
        NatureChoices.CONSULTING_LEGAL_ADVICE,
        NatureChoices.CLEANING_MAINTENANCE,
        NatureChoices.MAINTENANCE_HOSPITAL_EQUIPMENT,
        NatureChoices.MAINTENANCE_COMPUTER_EQUIPMENT,
        NatureChoices.MAINTENANCE_BUILDING,
        NatureChoices.MAINTENANCE_VEHICLE,
        NatureChoices.CONSTRUCTION,
        NatureChoices.MAINTENANCE_OTHERS,
        NatureChoices.LEGAL_THIRD_PARTY_SERVICES,
        NatureChoices.ADVERTISING_PUBILICITY,
        NatureChoices.THERAPEUTIC_SUPPORT_SERVICE,
        NatureChoices.SERVICES_ACCOUNTING,
        NatureChoices.SERVICES_AUDITING,
        NatureChoices.SERVIECS_IT,
        NatureChoices.SERVICES_SURVEILLANCES,
    ]

    HUMAN_RESOURCES = [
        NatureChoices.THIRTHEENTH_SALARY,
        NatureChoices.APPRENTICES,
        NatureChoices.MEDICAL_ASSISTENCE,
        NatureChoices.ADVANCE_NOTICE,
        NatureChoices.BENEFITS,
        NatureChoices.INTERNSHIP_ALLOWANCE,
        NatureChoices.INSS_CONTRIBUTION_SHARE,
        NatureChoices.PIS_CONTRIBUTION,
        NatureChoices.SOCIAL_CONTRIBUTIONS,
        NatureChoices.COURSES_TRAINING_RETRAINING,
        NatureChoices.PERSONNEL_EXPENSES,
        NatureChoices.COLLECTIVE_BARGAINING,
        NatureChoices.SOCIAL_CHARGES,
        NatureChoices.FGTS,
        NatureChoices.RESERVE_FUND,
        NatureChoices.VACATIONS,
        NatureChoices.BONUSES,
        NatureChoices.HR_INSS,
        NatureChoices.HR_IRRF,
        NatureChoices.COMPENSATIONS,
        NatureChoices.TERMINATION_EMPLOYMENT_CONTRACT,
        NatureChoices.MISCELLANOUS_WITHHOLDINGS,
        NatureChoices.MANAGEMENT_SALARY,
        NatureChoices.SALARIES_AND_WAGES,
        NatureChoices.UNIFORMS,
        NatureChoices.FOOD_VOUCHERS,
        NatureChoices.MEAL_VOUCHERS,
        NatureChoices.TRANSPORTATION_VOUCHERS,
    ]

    OTHER_HUMAN_RESOURCES = [
        NatureChoices.INTERN_REMUNERATION,
        NatureChoices.SERVICES_PF_THIRD_PARTIES,
        NatureChoices.SERVICES_PJ_THIRD_PARTIES,
    ]

    MEDICAL_SERVICES = [
        NatureChoices.MEDICAL_SERVICES,
        NatureChoices.MEDICAL_SERVICES_FOR_INDIVIDUALS,
        NatureChoices.MEDICAL_SERVICES_FOR_ENTITIES,
    ]

    PUBLIC_UTILITIES = [
        NatureChoices.PUBLIC_ADMINISTRATIVE_EXPENSES,
        NatureChoices.ELECTRICITY,
        NatureChoices.INTERNET_TV,
        NatureChoices.TELEPHONE,
        NatureChoices.PUBLIC_UTILITIES,
        NatureChoices.WATER_SEWAGE,
    ]
