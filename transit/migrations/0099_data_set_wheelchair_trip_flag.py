from django.db import migrations

def get_tag_list(tag_string):
    tags = tag_string.split(',')
    for i in range(0, len(tags)):
        tags[i] = tags[i].strip()
    return tags

def set_wheelchair_flag(apps, schema_editor):
    Trip = apps.get_model('transit', 'Trip')
    for trip in Trip.objects.all():
        tag_list = get_tag_list(trip.tags)
        if 'Wheelchair' in tag_list:
            trip.wheelchair = True
        else:
            trip.wheelchair = False
        trip.save()

    TemplateTrip = apps.get_model('transit', 'TemplateTrip')
    for trip in TemplateTrip.objects.all():
        tag_list = get_tag_list(trip.tags)
        if 'Wheelchair' in tag_list:
            trip.wheelchair = True
        else:
            trip.wheelchair = False
        trip.save()

class Migration(migrations.Migration):
    dependencies = [
        ('transit', '0098_auto_20230217_0956'),
    ]

    operations = [
        migrations.RunPython(set_wheelchair_flag),
    ]

