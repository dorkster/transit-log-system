# Generated by Django 3.0 on 2020-08-07 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0065_templatetrip_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='fare',
            field=models.IntegerField(default=0),
        ),
    ]
