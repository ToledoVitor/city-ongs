from django.contrib import admin

from accountability.models import (
    Accountability,
    AccountabilityFile,
    ResourceSource,
    Expense,
    ExpenseAnalysis,
    Revenue,
)

admin.site.register(Accountability)
admin.site.register(AccountabilityFile)
admin.site.register(ResourceSource)
admin.site.register(Expense)
admin.site.register(ExpenseAnalysis)
admin.site.register(Revenue)
