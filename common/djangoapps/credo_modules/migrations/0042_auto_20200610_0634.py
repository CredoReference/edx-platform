# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-06-10 10:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credo_modules', '0041_auto_20200609_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trackinglogprop',
            name='org_id',
            field=models.CharField(db_index=True, max_length=80),
        ),
    ]
