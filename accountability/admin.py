from django.contrib import admin

from accountability.models import (
    Accountability,
    AccountabilityFile,
    Expense,
    ExpenseAnalysis,
    ExpenseSource,
    Revenue,
    RevenueSource,
)

admin.site.register(Accountability)
admin.site.register(ExpenseSource)
admin.site.register(Expense)
admin.site.register(ExpenseAnalysis)
admin.site.register(RevenueSource)
admin.site.register(Revenue)
admin.site.register(AccountabilityFile)
