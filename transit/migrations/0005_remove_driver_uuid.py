# Generated by Django 2.2.6 on 2019-10-19 23:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0004_driver_uuid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='driver',
            name='uuid',
        ),
    ]