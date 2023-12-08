# Generated by Django 4.2.7 on 2023-12-08 11:13

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_alter_savingsgoal_target_date_delete_useraim'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savingsgoal',
            name='target_date',
            field=models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(2024, 1, 7))]),
        ),
    ]