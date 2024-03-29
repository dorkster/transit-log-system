# Generated by Django 3.2.10 on 2023-03-30 05:03

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0099_data_set_wheelchair_trip_flag'),
    ]

    operations = [
        migrations.CreateModel(
            name='Volunteer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sort_index', models.IntegerField(default=0, editable=False)),
                ('name', models.CharField(max_length=128)),
                ('vehicle', models.CharField(blank=True, max_length=128)),
                ('vehicle_color', models.CharField(blank=True, max_length=64)),
                ('vehicle_plate', models.CharField(blank=True, max_length=64)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['sort_index'],
            },
        ),
        migrations.AddField(
            model_name='templatetrip',
            name='volunteer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transit.volunteer'),
        ),
        migrations.AddField(
            model_name='trip',
            name='volunteer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='transit.volunteer'),
        ),
    ]
