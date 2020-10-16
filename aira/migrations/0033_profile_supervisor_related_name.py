# Generated by Django 2.2.12 on 2020-10-22 13:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0032_kc_plantingdate"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="supervisor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="supervisees",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]