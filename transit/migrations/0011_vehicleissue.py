# Generated by Django 2.2.6 on 2019-10-25 13:19

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0010_auto_20191020_1318'),
    ]

    operations = [
        migrations.CreateModel(
            name='VehicleIssue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('description', models.TextField(blank=True, max_length=4096)),
                ('priority', models.IntegerField(choices=[(2, 'High'), (1, 'Medium'), (0, 'Low')], default=1)),
                ('resolved', models.BooleanField(default=False)),
                ('driver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transit.Driver')),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transit.Vehicle')),
            ],
        ),
    ]