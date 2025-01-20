from django.contrib import admin

from contracts.models import (
    Company,
    Contract,
    ContractAddendum,
    ContractAddress,
    ContractGoal,
    ContractStep,
    ContractItem,
)


admin.site.register(Company)
admin.site.register(Contract)
admin.site.register(ContractAddendum)
admin.site.register(ContractAddress)
admin.site.register(ContractGoal)
admin.site.register(ContractStep)
admin.site.register(ContractItem)
