# Generated by Django 5.2.1 on 2025-05-29 14:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ingredient',
            old_name='fats_per_100g',
            new_name='fat_per_100g',
        ),
    ]
