# Generated by Django 2.2.6 on 2019-11-07 00:33

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0016_auto_20191106_1434'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('message', models.CharField(blank=True, max_length=1024)),
            ],
        ),
    ]
