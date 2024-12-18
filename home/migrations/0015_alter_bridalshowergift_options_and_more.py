# Generated by Django 5.1.1 on 2024-09-24 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_gallery_hide_gallery_hide_title'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='bridalshowergift',
            options={'ordering': ['-category', 'name'], 'verbose_name': 'Presente do Chá de Panela', 'verbose_name_plural': 'Presentes do Chá de Panela'},
        ),
        migrations.AddField(
            model_name='settings',
            name='hide_about_us',
            field=models.BooleanField(default=False, verbose_name='Esconder Sobre Nós'),
        ),
    ]
