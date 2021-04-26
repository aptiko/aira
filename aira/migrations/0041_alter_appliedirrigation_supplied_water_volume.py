# Generated by Django 3.2 on 2021-04-26 19:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0040_agrifield_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appliedirrigation",
            name="supplied_water_volume",
            field=models.FloatField(
                blank=True,
                help_text=(
                    "If empty, an automatically calculated default will be assumed"
                ),
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
    ]
