from django.contrib import admin

from accountability.models import (
    Accountability,
    AccountabilityFile,
    Expense,
    ExpenseAnalysis,
    ExpenseFile,
    Favored,
    ResourceSource,
    Revenue,
    RevenueFile,
)

admin.site.register(Accountability)
admin.site.register(AccountabilityFile)
admin.site.register(ResourceSource)
admin.site.register(Expense)
admin.site.register(ExpenseAnalysis)
admin.site.register(Revenue)
admin.site.register(ExpenseFile)
admin.site.register(RevenueFile)
admin.site.register(Favored)
