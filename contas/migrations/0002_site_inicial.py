import os

from django.db import migrations


def criar_site_inicial(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Site.objects.get_or_create(
        pk=1,
        defaults={
            "domain": os.environ.get("SITE_DOMAIN", "localhost:8000"),
            "name": "Manutenção UCM-FEG",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("contas", "0001_initial"),
        ("sites", "0002_alter_domain_unique"),
    ]

    operations = [
        migrations.RunPython(criar_site_inicial, migrations.RunPython.noop),
    ]
