import datetime as dt

from django.db import migrations

from aira.models import DayAndMonth


def get_day_and_month(date):
    if date:
        return DayAndMonth(date.day, date.month)


def date_to_day_and_month(apps, schema_editor):
    CropType = apps.get_model("aira", "CropType")
    for crop_type in CropType.objects.all():
        crop_type.nplanting_date = get_day_and_month(crop_type.planting_date)
        crop_type.save()

    Agrifield = apps.get_model("aira", "Agrifield")
    for agrifield in Agrifield.objects.all():
        agrifield.ncustom_planting_date = get_day_and_month(
            agrifield.custom_planting_date
        )
        agrifield.save()


def get_date_from_day_and_month(day_and_month):
    if day_and_month:
        return dt.date(1970, day_and_month.month, day_and_month.day)


def day_and_month_to_date(apps, schema_editor):
    CropType = apps.get_model("aira", "CropType")
    for crop_type in CropType.objects.all():
        crop_type.planting_date = get_date_from_day_and_month(crop_type.nplanting_date)
        crop_type.save()

    Agrifield = apps.get_model("aira", "Agrifield")
    for agrifield in Agrifield.objects.all():
        agrifield.custom_planting_date = get_date_from_day_and_month(
            agrifield.ncustom_planting_date
        )
        agrifield.save()


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0043_planting_date"),
    ]

    operations = [migrations.RunPython(date_to_day_and_month, day_and_month_to_date)]
