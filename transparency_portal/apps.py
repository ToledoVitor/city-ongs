from django.apps import AppConfig
from django.db.models.signals import post_save


class TransparencyPortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "transparency_portal"
    verbose_name = "Portal de Transparência"

    def ready(self):
        from accountability.models import Accountability
        from contracts.models import Contract
        from transparency_portal import signals

        post_save.connect(
            signals.update_partnership_transparency,
            sender=Contract,
        )
        post_save.connect(signals.update_accountability_report, sender=Accountability)
