from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Enable the `unaccent` extension.

    Powers accent-insensitive search in ComboboxSearchView: users type "saude"
    or "convenio" and still match "Saúde" and "Convênio". Lives in `accounts`
    because it is the foundational app — the extension is database-wide, not
    specific to any model here.
    """

    dependencies = [
        ("accounts", "0002_cityhall_audesp_municipality_code_and_more"),
    ]

    operations = [
        UnaccentExtension(),
    ]
