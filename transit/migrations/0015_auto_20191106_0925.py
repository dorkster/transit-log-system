# Generated by Django 2.2.6 on 2019-11-06 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0014_auto_20191104_1827'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='template',
            options={'ordering': ['sort_index']},
        ),
    ]