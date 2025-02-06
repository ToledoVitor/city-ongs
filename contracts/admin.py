from django.contrib import admin

from contracts.models import (
    Company,
    Contract,
    ContractAddendum,
    ContractGoal,
    ContractItem,
    ContractStep,
    ContractExecution,
    ContractExecutionActivity,
    ContractExecutionFile,
    ContractGoalReview,
    ContractItemReview,
)

admin.site.register(Company)
admin.site.register(Contract)
admin.site.register(ContractAddendum)
admin.site.register(ContractGoal)
admin.site.register(ContractStep)
admin.site.register(ContractItem)
admin.site.register(ContractExecution)
admin.site.register(ContractExecutionActivity)
admin.site.register(ContractExecutionFile)
admin.site.register(ContractGoalReview)
admin.site.register(ContractItemReview)
