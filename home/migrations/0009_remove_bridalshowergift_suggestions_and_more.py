# Generated by Django 5.1.1 on 2024-09-15 17:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_settings_bridal_shower_address_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bridalshowergift',
            name='suggestions',
        ),
        migrations.AddField(
            model_name='bridalshowergiftsuggestion',
            name='gift',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='suggestions', to='home.bridalshowergift'),
            preserve_default=False,
        ),
    ]
