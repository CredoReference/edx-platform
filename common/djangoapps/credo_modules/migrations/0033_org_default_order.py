# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-12-18 08:54
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credo_modules', '0032_organizationtype_my_skills_page_lti_access'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organization',
            options={'ordering': ['org']},
        ),
    ]
