from django.db import migrations

def set_trip_format(apps, schema_editor):
    Trip = apps.get_model('transit', 'Trip')
    for trip in Trip.objects.all():
        if trip.is_activity:
            trip.format = 1 # Trip.FORMAT_ACTIVITY
        else:
            trip.format = 0 # Trip.FORMAT_NORMAL
        trip.save()

    TemplateTrip = apps.get_model('transit', 'TemplateTrip')
    for trip in TemplateTrip.objects.all():
        if trip.is_activity:
            trip.format = 1 # Trip.FORMAT_ACTIVITY
        else:
            trip.format = 0 # Trip.FORMAT_NORMAL
        trip.save()

class Migration(migrations.Migration):
    dependencies = [
        ('transit', '0088_auto_20220802_1207'),
    ]

    operations = [
        migrations.RunPython(set_trip_format),
    ]

