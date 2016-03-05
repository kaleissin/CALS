# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wordlist', '0002_sense_concepticon_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('concepticon_id', models.IntegerField(null=True, blank=True)),
                ('name', models.CharField(max_length=40)),
                ('slug', models.SlugField()),
                ('pos', models.CharField(null=True, max_length=16, blank=True)),
                ('definition', models.TextField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('added', models.DateTimeField(null=True, blank=True)),
                ('see_also', models.ManyToManyField(related_name='_concept_see_also_+', blank=True, to='wordlist.Concept')),
            ],
            options={
                'ordering': ('id',),
            },
        ),
    ]
