# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cals', '0002_glottocode_iso639_3'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='iso639_3',
            options={'verbose_name': 'ISO 639-3', 'verbose_name_plural': 'ISO 639-3'},
        ),
        migrations.AlterField(
            model_name='walscode',
            name='language',
            field=models.OneToOneField(primary_key=True, serialize=False, to='cals.Language', related_name='walscode'),
        ),
    ]
