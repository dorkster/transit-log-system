# Generated by Django 3.0 on 2020-01-08 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0049_helppage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='helppage',
            name='body',
            field=models.TextField(blank=True, max_length=8192),
        ),
    ]
