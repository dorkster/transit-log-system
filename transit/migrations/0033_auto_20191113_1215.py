# Generated by Django 2.2.6 on 2019-11-13 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0032_recenttag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recenttag',
            name='id',
        ),
        migrations.AlterField(
            model_name='recenttag',
            name='tag',
            field=models.CharField(max_length=64, primary_key=True, serialize=False),
        ),
    ]