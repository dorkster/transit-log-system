# Generated by Django 4.2.11 on 2025-04-08 20:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0107_auto_20240312_0052'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='default_vehicle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transit.vehicle'),
        ),
    ]
