# Generated by Django 3.2 on 2021-04-08 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0037_wetted_area"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agrifield",
            name="is_virtual",
            field=models.BooleanField(default=False),
        ),
    ]