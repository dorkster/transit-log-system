# Generated by Django 2.2.6 on 2019-11-18 18:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0037_auto_20191118_1315'),
    ]

    operations = [
        migrations.RenameField(
            model_name='trip',
            old_name='donated_cash',
            new_name='collected_cash',
        ),
        migrations.RenameField(
            model_name='trip',
            old_name='donated_check',
            new_name='collected_check',
        ),
    ]
