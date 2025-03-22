from django.db import migrations, models


def handle_duplicates(apps, schema_editor):
    Favored = apps.get_model("accountability", "Favored")
    # Get all duplicates
    duplicates = (
        Favored.objects.values("organization", "document")
        .annotate(count=models.Count("id"))
        .filter(count__gt=1)
    )

    for dup in duplicates:
        # Get all records for this organization/document combination
        records = Favored.objects.filter(
            organization_id=dup["organization"], document=dup["document"]
        ).order_by("created_at")

        # Keep the oldest record and delete others
        oldest = records.first()
        records.exclude(id=oldest.id).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accountability", "0013_alter_accountability_organization_and_more"),
    ]

    operations = [
        migrations.RunPython(handle_duplicates),
    ]
