# Generated by Django 3.2.10 on 2022-11-08 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0095_auto_20221019_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='is_shown_in_notifications',
            field=models.BooleanField(default=True),
        ),
    ]
