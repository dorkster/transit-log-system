from django.db import migrations

def clean_trips(apps, schema_editor):
    Trip = apps.get_model('transit', 'Trip')
    for trip in Trip.objects.all():
        if trip.format > 0: # i.e. not FORMAT_NORMAL
            trip.name = ''
            trip.address = ''
            trip.destination = ''
            trip.phone_home = ''
            trip.phone_cell = ''
            trip.elderly = None
            trip.ambulatory = None
        trip.save()

    TemplateTrip = apps.get_model('transit', 'TemplateTrip')
    for trip in TemplateTrip.objects.all():
        if trip.format > 0: # i.e. not FORMAT_NORMAL
            trip.name = ''
            trip.address = ''
            trip.destination = ''
            trip.phone_home = ''
            trip.phone_cell = ''
            trip.elderly = None
            trip.ambulatory = None
        trip.save()

class Migration(migrations.Migration):
    dependencies = [
        ('transit', '0090_auto_20220802_1341'),
    ]

    operations = [
        migrations.RunPython(clean_trips),
    ]

