# Generated by Django 2.2.17 on 2021-02-04 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0034_automatic_flowmeter"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agrifield",
            name="name",
            field=models.CharField(max_length=255),
        ),
    ]