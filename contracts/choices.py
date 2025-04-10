from django.db.models import TextChoices


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
