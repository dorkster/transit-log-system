# Generated by Django 3.0 on 2019-12-20 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0045_trip_phone_destination'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='phone_address',
            field=models.CharField(blank=True, max_length=16, verbose_name='Phone (Address)'),
        ),
    ]
