# Generated by Django 3.2.10 on 2024-03-12 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0105_sitesettings_trip_cancel_late_threshold'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
