# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('cals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BuckCategory',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.TextField()),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Buck category',
                'ordering': ('id',),
                'verbose_name_plural': 'Buck categories',
            },
        ),
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('concepticon_id', models.IntegerField(blank=True, null=True)),
                ('name', models.CharField(max_length=40)),
                ('slug', models.SlugField()),
                ('pos', models.CharField(blank=True, null=True, max_length=16)),
                ('definition', models.TextField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('added', models.DateTimeField(blank=True, null=True)),
                ('see_also', models.ManyToManyField(related_name='_concept_see_also_+', blank=True, to='wordlist.Concept')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='Sense',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('entry', models.CharField(max_length=40)),
                ('slug', models.SlugField()),
                ('pos', models.CharField(blank=True, null=True, max_length=16)),
                ('notes', models.TextField(blank=True, null=True)),
                ('swadesh_100', models.BooleanField(default=False)),
                ('swadesh_207', models.IntegerField(blank=True, null=True)),
                ('yakhontov', models.BooleanField(default=False)),
                ('holman_rank', models.IntegerField(blank=True, null=True)),
                ('holman_list', models.BooleanField(default=False)),
                ('buck', models.BooleanField(default=False)),
                ('buck_number', models.CharField(blank=True, null=True, max_length=12)),
                ('wold', models.BooleanField(default=False)),
                ('wold_number', models.CharField(blank=True, null=True, max_length=12)),
                ('ids', models.BooleanField(default=False)),
                ('ids_number', models.CharField(blank=True, null=True, max_length=12)),
                ('uld2', models.CharField(blank=True, null=True, max_length=3)),
                ('concepticon_id', models.IntegerField(blank=True, null=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('buck_category', models.ForeignKey(blank=True, null=True, to='wordlist.BuckCategory')),
                ('see_also', models.ManyToManyField(related_name='_sense_see_also_+', blank=True, to='wordlist.Sense')),
                ('suggested_by', models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='SkippedWord',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(related_name='skipped_words', to=settings.AUTH_USER_MODEL)),
                ('language', models.ForeignKey(related_name='skipped_words', to='cals.Language')),
                ('sense', models.ForeignKey(related_name='skipped_words', to='wordlist.Sense')),
            ],
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('word', models.CharField(blank=True, null=True, max_length=40)),
                ('notes', models.TextField(blank=True, null=True)),
                ('not_applicable', models.NullBooleanField(default=False)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('added_by', models.ForeignKey(related_name='words_added', to=settings.AUTH_USER_MODEL)),
                ('language', models.ForeignKey(related_name='words', to='cals.Language')),
                ('last_modified_by', models.ForeignKey(related_name='words_modified', to=settings.AUTH_USER_MODEL)),
                ('see_also', models.ManyToManyField(related_name='_word_see_also_+', blank=True, to='wordlist.Word')),
                ('senses', models.ManyToManyField(related_name='words', blank=True, to='wordlist.Sense')),
            ],
        ),
    ]
