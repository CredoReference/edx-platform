# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-12-05 20:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lti_provider', '0009_gradedassignment_lis_result_sourcedid_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='lticontextid',
            name='properties',
            field=models.TextField(blank=True, null=True),
        ),
    ]
