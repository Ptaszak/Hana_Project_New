# Generated by Django 3.0.6 on 2020-07-04 00:54

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hana', '0011_task_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='info',
            name='date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
