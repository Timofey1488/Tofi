# Generated by Django 4.2.7 on 2023-12-08 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credits', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditapplication',
            name='status',
            field=models.CharField(max_length=20),
        ),
    ]
