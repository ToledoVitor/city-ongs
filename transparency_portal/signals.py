from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AccountabilityReport, PartnershipTransparency


@receiver(post_save)
def update_partnership_transparency(sender, instance, created, **kwargs):
    from contracts.models import Contract

    if sender != Contract:
        return

    partnership, _ = PartnershipTransparency.objects.get_or_create(
        contract=instance,
        organization=instance.organization,
    )
    partnership.last_updated = timezone.now()
    partnership.save()


@receiver(post_save)
def update_accountability_report(sender, instance, created, **kwargs):
    from accountability.models import Accountability

    if sender != Accountability:
        return

    partnership = PartnershipTransparency.objects.filter(
        contract=instance.contract,
        organization=instance.organization,
    ).first()

    if partnership:
        report, _ = AccountabilityReport.objects.get_or_create(
            partnership=partnership, accountability=instance
        )
        report.save()

        partnership.last_updated = timezone.now()
        partnership.save()
