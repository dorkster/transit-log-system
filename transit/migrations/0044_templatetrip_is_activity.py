# Generated by Django 2.2.6 on 2019-11-26 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0043_auto_20191125_1938'),
    ]

    operations = [
        migrations.AddField(
            model_name='templatetrip',
            name='is_activity',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]