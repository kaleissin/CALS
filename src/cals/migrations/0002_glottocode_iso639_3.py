# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Glottocode',
            fields=[
                ('language', models.OneToOneField(to='cals.Language', primary_key=True, related_name='glottocode', serialize=False)),
                ('glottocode', models.CharField(unique=True, max_length=8)),
            ],
            options={
                'db_table': 'cals_glottocode',
            },
        ),
        migrations.CreateModel(
            name='ISO639_3',
            fields=[
                ('language', models.OneToOneField(to='cals.Language', primary_key=True, related_name='iso639_3', serialize=False)),
                ('iso639_3', models.CharField(unique=True, max_length=3)),
            ],
            options={
                'db_table': 'cals_iso639_3',
            },
        ),
    ]
