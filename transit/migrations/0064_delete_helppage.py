# Generated by Django 3.0 on 2020-03-03 15:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0063_sitesettings_skip_weekends'),
    ]

    operations = [
        migrations.DeleteModel(
            name='HelpPage',
        ),
    ]