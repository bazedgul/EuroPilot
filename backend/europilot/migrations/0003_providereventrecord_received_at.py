from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("europilot", "0002_findingevidencerecord_and_more")]

    operations = [
        migrations.AddField(
            model_name="providereventrecord",
            name="received_at",
            field=models.DateTimeField(default="2026-01-04T00:00:00+00:00"),
            preserve_default=False,
        ),
    ]
