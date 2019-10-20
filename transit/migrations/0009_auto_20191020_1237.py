# Generated by Django 2.2.6 on 2019-10-20 16:37

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0008_auto_20191020_1209'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='vehicle',
            options={'ordering': ['sort_index']},
        ),
        migrations.AddField(
            model_name='vehicle',
            name='is_logged',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='vehicle',
            name='sort_index',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
