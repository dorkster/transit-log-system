# Generated by Django 2.2.6 on 2019-10-09 22:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0006_auto_20191008_2042'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trip',
            old_name='client_ambulatory',
            new_name='ambulatory',
        ),
        migrations.RenameField(
            model_name='trip',
            old_name='client_elderly',
            new_name='elderly',
        ),
    ]
