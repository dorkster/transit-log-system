# Generated by Django 3.1.4 on 2021-02-06 23:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0075_loggedevent'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loggedevent',
            name='event_type',
        ),
        migrations.AddField(
            model_name='loggedevent',
            name='event_action',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='loggedevent',
            name='event_model',
            field=models.IntegerField(default=0),
        ),
    ]