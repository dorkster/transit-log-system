# Generated by Django 3.2 on 2021-04-15 16:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0078_auto_20210414_0819'),
    ]

    operations = [
        migrations.AddField(
            model_name='destination',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]