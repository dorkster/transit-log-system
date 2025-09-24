from django.db import migrations, models

def update_shift_sorting(apps, schema_editor):
    Shift = apps.get_model('transit', 'Shift')

    shifts = Shift.objects.all()

    for shift in shifts:
        if shift.sort_index == 0:
            day_shifts = Shift.objects.filter(date=shift.date)
            sort_index = 0
            for day_shift in day_shifts:
                day_shift.sort_index = sort_index
                day_shift.save()
                sort_index += 1

class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0115_alter_shift_options_shift_sort_index'),
    ]

    operations = [
        migrations.RunPython(update_shift_sorting)
    ]
