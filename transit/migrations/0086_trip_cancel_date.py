# Generated by Django 3.2.10 on 2022-06-30 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0085_clientpayment_notes'),
    ]

    operations = [
        migrations.AddField(
            model_name='trip',
            name='cancel_date',
            field=models.DateField(default=None, null=True),
        ),
    ]
