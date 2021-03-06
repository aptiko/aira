# Generated by Django 2.2.12 on 2020-04-19 06:51

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0029_rename_irrigationlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="appliedirrigation",
            name="flowmeter_reading_end",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="appliedirrigation",
            name="flowmeter_reading_start",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
            ),
        ),
        migrations.AddField(
            model_name="appliedirrigation",
            name="flowmeter_water_percentage",
            field=models.PositiveSmallIntegerField(
                blank=True,
                default=100,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
        migrations.AddField(
            model_name="appliedirrigation",
            name="irrigation_type",
            field=models.CharField(
                choices=[
                    ("VOLUME_OF_WATER", "Volume of water"),
                    ("DURATION_OF_IRRIGATION", "Duration of irrigation"),
                    ("FLOWMETER_READINGS", "Flowmeter readings"),
                ],
                default="VOLUME_OF_WATER",
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="appliedirrigation",
            name="supplied_duration",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Duration in minutes"
            ),
        ),
        migrations.AddField(
            model_name="appliedirrigation",
            name="supplied_flow_rate",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(0.0)],
                verbose_name="Flow rate (m3/h)",
            ),
        ),
    ]
