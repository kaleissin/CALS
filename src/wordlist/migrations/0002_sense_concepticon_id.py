# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wordlist', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sense',
            name='concepticon_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
