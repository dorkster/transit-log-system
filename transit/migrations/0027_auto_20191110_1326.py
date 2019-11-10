# Generated by Django 2.2.6 on 2019-11-10 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0026_auto_20191110_1326'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='client',
            name='phone_default',
        ),
        migrations.AlterField(
            model_name='client',
            name='phone_cell',
            field=models.CharField(blank=True, max_length=16, verbose_name='Phone (Cell)'),
        ),
    ]
