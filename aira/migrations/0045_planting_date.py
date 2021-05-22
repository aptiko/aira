from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aira", "0044_planting_date_data"),
    ]

    operations = [
        # Add a default just to make the migration reversible (see
        # https://stackoverflow.com/questions/28878428/)
        migrations.AlterField(
            model_name="croptype",
            name="planting_date",
            field=models.DateField(default="1970-01-01"),
        ),
        migrations.RemoveField(
            model_name="agrifield",
            name="custom_planting_date",
        ),
        migrations.RemoveField(
            model_name="croptype",
            name="planting_date",
        ),
        migrations.RenameField(
            model_name="agrifield",
            old_name="ncustom_planting_date",
            new_name="custom_planting_date",
        ),
        migrations.RenameField(
            model_name="croptype",
            old_name="nplanting_date",
            new_name="planting_date",
        ),
    ]
