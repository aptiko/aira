from django.db import migrations

import aira.models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0042_alter_appliedirrigation_supplied_flow_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="agrifield",
            name="ncustom_planting_date",
            field=aira.models.DayAndMonthField(blank=True),
        ),
        migrations.AddField(
            model_name="croptype",
            name="nplanting_date",
            field=aira.models.DayAndMonthField(),
        ),
    ]
