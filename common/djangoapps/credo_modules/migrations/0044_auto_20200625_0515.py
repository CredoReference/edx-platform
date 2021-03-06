# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-06-25 09:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credo_modules', '0043_auto_20200619_1329'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trackinglog',
            name='answer_id',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='trackinglog',
            unique_together=set([('answer_id', 'attempt_ts')]),
        ),
    ]
