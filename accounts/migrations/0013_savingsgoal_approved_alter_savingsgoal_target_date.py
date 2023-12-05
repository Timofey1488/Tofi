# Generated by Django 4.2.7 on 2023-12-05 11:28

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_savingsgoal_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='savingsgoal',
            name='approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='savingsgoal',
            name='target_date',
            field=models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(2023, 12, 5))]),
        ),
    ]
