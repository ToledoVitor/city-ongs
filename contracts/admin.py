from django.contrib import admin

from contracts.models import (
    Company,
    Contract,
    ContractAddress,
    ContractGoal,
    ContractItem,
    ContractSubGoal,
)

admin.site.register(Company)
admin.site.register(Contract)
admin.site.register(ContractAddress)
admin.site.register(ContractGoal)
admin.site.register(ContractItem)
admin.site.register(ContractSubGoal)
