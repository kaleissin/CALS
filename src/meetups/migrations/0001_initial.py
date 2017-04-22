# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badge', '__first__'),
        ('verification', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meetup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('badge', models.ForeignKey(to='badge.Badge')),
                ('keygroup', models.ForeignKey(to='verification.KeyGroup')),
                ('valid_from', models.DateField(null=True, blank=True)),
                ('valid_until', models.DateField(null=True, blank=True)),
                ('actual_number_of_attendees', models.IntegerField(default=0, null=True, blank=True)),
                ('estimated_number_of_attendees', models.IntegerField(default=0, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
