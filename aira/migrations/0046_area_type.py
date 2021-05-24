import django.core.validators
from django.db import migrations, models


def ensure_nonzero_wetted_area(apps, schema_editor):
    Agrifield = apps.get_model("aira", "Agrifield")
    for agrifield in Agrifield.objects.filter(wetted_area=0):
        agrifield.wetted_area = 1
        agrifield.save()


def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0045_planting_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agrifield",
            name="irrigated_area",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Irrigated area"
            ),
        ),
        migrations.AlterField(
            model_name="agrifield",
            name="total_area",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Total area"
            ),
        ),
        migrations.AlterField(
            model_name="agrifield",
            name="wetted_area",
            field=models.PositiveIntegerField(
                validators=[django.core.validators.MinValueValidator(1)]
            ),
        ),
        migrations.RunPython(ensure_nonzero_wetted_area, do_nothing),
    ]
