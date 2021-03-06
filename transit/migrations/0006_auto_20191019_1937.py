# Generated by Django 2.2.6 on 2019-10-19 23:37

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0005_remove_driver_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='color',
            field=models.CharField(blank=True, max_length=9),
        ),
        migrations.AlterField(
            model_name='driver',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
