# Generated by Django 2.2.6 on 2019-11-10 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0023_auto_20191110_1302'),
    ]

    operations = [
        migrations.AddField(
            model_name='templatetrip',
            name='phone_cell',
            field=models.CharField(blank=True, max_length=16),
        ),
    ]