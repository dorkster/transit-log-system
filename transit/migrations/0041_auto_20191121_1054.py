# Generated by Django 2.2.6 on 2019-11-21 15:54

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0040_pretrip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pretrip',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
