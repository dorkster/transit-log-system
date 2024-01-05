from django.db import migrations, models

import datetime
from django.utils import timezone


def backup_data(apps, schema_editor):
    Trip = apps.get_model('transit', 'Trip')
    for trip in Trip.objects.all():
        if trip.cancel_date:
            trip.cancel_date_old = trip.cancel_date
            trip.save()

def update_data(apps, schema_editor):
    Trip = apps.get_model('transit', 'Trip')
    for trip in Trip.objects.all():
        if trip.cancel_date_old:
            trip.cancel_date = timezone.make_aware(datetime.datetime.combine(trip.cancel_date_old, datetime.datetime.min.time()))
            trip.save()

class Migration(migrations.Migration):
    dependencies = [
        ('transit', '0103_alter_sitesettings_simple_daily_logs'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='cancel_date_old',
            field=models.DateField(default=None, null=True),
        ),
        migrations.RunPython(backup_data),
        migrations.AlterField(
            model_name='trip',
            name='cancel_date',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.RunPython(update_data),
        migrations.RemoveField(
            model_name='trip',
            name='cancel_date_old',
        ),
    ]
