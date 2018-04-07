# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('badge', '__first__'),
        ('verification', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meetup',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('valid_from', models.DateField(blank=True, null=True)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('estimated_number_of_attendees', models.IntegerField(null=True, blank=True, default=0)),
                ('actual_number_of_attendees', models.IntegerField(null=True, blank=True, default=0)),
                ('badge', models.ForeignKey(to='badge.Badge')),
                ('keygroup', models.ForeignKey(to='verification.KeyGroup')),
            ],
        ),
    ]
