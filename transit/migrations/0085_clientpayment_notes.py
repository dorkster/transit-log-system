# Generated by Django 3.2.10 on 2022-03-23 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0084_auto_20211215_2323'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientpayment',
            name='notes',
            field=models.TextField(blank=True, max_length=256),
        ),
    ]
