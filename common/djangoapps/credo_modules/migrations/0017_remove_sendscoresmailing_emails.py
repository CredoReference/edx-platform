# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-13 16:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credo_modules', '0016_send_scores'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sendscoresmailing',
            name='emails',
        ),
    ]
