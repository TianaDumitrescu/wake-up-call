from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("main", "0001_initial"),
    ]
    operations = [
        migrations.AlterField(
            model_name="lucid",
            name="evolution",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="lucid",
            name="spawn_level_offset",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="lucid",
            name="spawn_rate",
            field=models.FloatField(blank=True, null=True),
        ),
    ]