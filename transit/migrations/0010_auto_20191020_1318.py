# Generated by Django 2.2.6 on 2019-10-20 17:18

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0009_auto_20191020_1237'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='triptype',
            options={'ordering': ['sort_index']},
        ),
        migrations.AddField(
            model_name='triptype',
            name='sort_index',
            field=models.IntegerField(default=0, editable=False),
        ),
        migrations.AlterField(
            model_name='triptype',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]