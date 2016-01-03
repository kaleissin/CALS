# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cals', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuckCategory',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.TextField()),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Buck categories',
                'ordering': ('id',),
                'verbose_name': 'Buck category',
            },
        ),
        migrations.CreateModel(
            name='Sense',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('entry', models.CharField(max_length=40)),
                ('slug', models.SlugField()),
                ('pos', models.CharField(max_length=16, blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('swadesh_100', models.BooleanField(default=False)),
                ('swadesh_207', models.IntegerField(blank=True, null=True)),
                ('yakhontov', models.BooleanField(default=False)),
                ('holman_rank', models.IntegerField(blank=True, null=True)),
                ('holman_list', models.BooleanField(default=False)),
                ('buck', models.BooleanField(default=False)),
                ('buck_number', models.CharField(max_length=12, blank=True, null=True)),
                ('wold', models.BooleanField(default=False)),
                ('wold_number', models.CharField(max_length=12, blank=True, null=True)),
                ('ids', models.BooleanField(default=False)),
                ('ids_number', models.CharField(max_length=12, blank=True, null=True)),
                ('uld2', models.CharField(max_length=3, blank=True, null=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('buck_category', models.ForeignKey(blank=True, null=True, to='wordlist.BuckCategory')),
                ('see_also', models.ManyToManyField(blank=True, to='wordlist.Sense', related_name='_sense_see_also_+')),
                ('suggested_by', models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='SkippedWord',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='skipped_words')),
                ('language', models.ForeignKey(to='cals.Language', related_name='skipped_words')),
                ('sense', models.ForeignKey(to='wordlist.Sense', related_name='skipped_words')),
            ],
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('word', models.CharField(max_length=40, blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('not_applicable', models.NullBooleanField(default=False)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='words_added')),
                ('language', models.ForeignKey(to='cals.Language', related_name='words')),
                ('last_modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='words_modified')),
                ('see_also', models.ManyToManyField(blank=True, to='wordlist.Word', related_name='_word_see_also_+')),
                ('senses', models.ManyToManyField(blank=True, to='wordlist.Sense', related_name='words')),
            ],
        ),
    ]
