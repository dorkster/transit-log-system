# Generated by Django 2.2.6 on 2019-10-26 19:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0012_auto_20191025_2006'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vehicleissue',
            options={'ordering': ['-priority', '-date']},
        ),
    ]
