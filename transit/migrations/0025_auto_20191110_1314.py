# Generated by Django 2.2.6 on 2019-11-10 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0024_templatetrip_phone_cell'),
    ]

    operations = [
        migrations.AlterField(
            model_name='templatetrip',
            name='phone_cell',
            field=models.CharField(blank=True, max_length=16, verbose_name='Phone (Cell)'),
        ),
        migrations.AlterField(
            model_name='templatetrip',
            name='phone_home',
            field=models.CharField(blank=True, max_length=16, verbose_name='Phone (Home)'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='phone_cell',
            field=models.CharField(blank=True, max_length=16, verbose_name='Phone (Cell)'),
        ),
        migrations.AlterField(
            model_name='trip',
            name='phone_home',
            field=models.CharField(blank=True, max_length=16, verbose_name='Phone (Home)'),
        ),
    ]
