from django.contrib import admin

from bank.models import (
    BankAccount,
    BankStatement,
    Transaction,
)


admin.site.register(BankAccount)
admin.site.register(BankStatement)
admin.site.register(Transaction)
