# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-03-25 13:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('credo_modules', '0019_copy_section_task'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseStaffExtended',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255)),
            ],
            options={
                'verbose_name': 'user role',
                'verbose_name_plural': 'extended user roles',
            },
        ),
        migrations.CreateModel(
            name='CustomUserRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='Title')),
                ('alias', models.SlugField(max_length=255, unique=True, verbose_name='Slug')),
                ('course_outline_create_new_section', models.BooleanField(
                    default=True, verbose_name='Course Outline: Can create new Section')),
                ('course_outline_create_new_subsection', models.BooleanField(
                    default=True, verbose_name='Course Outline: Can create new Subsection')),
                ('course_outline_duplicate_section', models.BooleanField(
                    default=True, verbose_name='Course Outline: Can duplicate Section')),
                ('course_outline_duplicate_subsection', models.BooleanField(
                    default=True, verbose_name='Course Outline: Can duplicate Subsection')),
                ('course_outline_copy_to_other_course', models.BooleanField(
                    default=True, verbose_name='Course Outline: Can copy Section to other course')),
                ('top_menu_tools', models.BooleanField(default=True, verbose_name='Top Menu: Tools Dropdown menu')),
                ('unit_add_advanced_component', models.BooleanField(
                    default=True, verbose_name='Unit: Can add advanced components to a unit')),
                ('unit_add_discussion_component', models.BooleanField(
                    default=True, verbose_name='Unit: Can add discussion components to a unit')),
                ('view_tags', models.BooleanField(default=True, verbose_name='Unit: Can view tags')),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'custom user role',
                'verbose_name_plural': 'custom user roles',
            },
        ),
        migrations.AddField(
            model_name='coursestaffextended',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='credo_modules.CustomUserRole'),
        ),
        migrations.AddField(
            model_name='coursestaffextended',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='organizationtype',
            name='available_roles',
            field=models.ManyToManyField(to='credo_modules.CustomUserRole'),
        ),
        migrations.AlterUniqueTogether(
            name='coursestaffextended',
            unique_together=set([('user', 'course_id')]),
        ),
    ]
