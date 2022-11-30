# Generated by Django 3.2.10 on 2022-10-19 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0094_client_is_transit_policy_acknowledged'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='reminder_instructions',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='templatetrip',
            name='reminder_instructions',
            field=models.CharField(blank=True, max_length=256),
        ),
        migrations.AddField(
            model_name='trip',
            name='reminder_instructions',
            field=models.CharField(blank=True, max_length=256),
        ),
    ]