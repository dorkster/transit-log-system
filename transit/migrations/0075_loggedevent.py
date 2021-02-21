# Generated by Django 3.1.4 on 2021-02-03 20:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0074_templatetrip_passenger'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoggedEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('username', models.CharField(default='{unknown user}', max_length=128)),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True)),
                ('event_type', models.IntegerField(default=0)),
                ('event_desc', models.CharField(blank=True, default='', max_length=512)),
            ],
        ),
    ]