# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-07-17 17:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('block_structure', '0012_apicoursestructuretags_block_tag_id'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE api_course_structure_tags ADD COLUMN `org_id` varchar(80) DEFAULT NULL"
        )
    ]
