# Generated by Django 2.2 on 2019-11-01 21:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rmg', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fluxdiagram',
            name='java',
        ),
    ]
