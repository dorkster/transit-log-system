# Generated by Django 3.2.10 on 2023-02-17 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0097_driver_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='templatetrip',
            name='wheelchair',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='trip',
            name='wheelchair',
            field=models.BooleanField(default=False),
        ),
    ]
