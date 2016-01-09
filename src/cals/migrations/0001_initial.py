# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers
import django.utils.timezone
from django.conf import settings
import cals.tools.models


class Migration(migrations.Migration):

    dependencies = [
        ('countries', '__first__'),
        ('auth', '0006_require_contenttypes_0002'),
        ('taggit', '0002_auto_20150616_2121'),
        ('blog', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('active', models.BooleanField(default=False, editable=False)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'db_table': 'cals_category',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Description',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('freetext', models.TextField(null=True, blank=True, default='')),
                ('freetext_xhtml', models.TextField(null=True, editable=False)),
                ('freetext_type', models.CharField(max_length=20, choices=[('rst', 'RestructuredText'), ('plaintext', 'plaintext')], blank=True, default='plaintext')),
                ('freetext_link', models.URLField(blank=True, null=True)),
                ('last_modified', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('current', models.BooleanField(default=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'get_latest_by': 'last_modified',
                'db_table': 'cals_description',
            },
        ),
        migrations.CreateModel(
            name='ExternalInfo',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('category', models.CharField(max_length=20, choices=[('homepage', 'Homepage'), ('dictionary', 'Dictionary')])),
                ('on_request', models.BooleanField(default=False)),
                ('link', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=96, unique=True)),
                ('wals', models.BooleanField(default=False, editable=False)),
                ('active', models.BooleanField(default=False, editable=False)),
            ],
            options={
                'db_table': 'cals_feature',
                'ordering': ['id'],
            },
            bases=(models.Model, cals.tools.models.DescriptionMixin),
        ),
        migrations.CreateModel(
            name='FeatureValue',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=64)),
                ('position', models.IntegerField(null=True)),
                ('feature', models.ForeignKey(to='cals.Feature', related_name='values')),
            ],
            options={
                'db_table': 'cals_featurevalue',
                'ordering': ['feature__id', 'position'],
            },
            bases=(models.Model, cals.tools.models.DescriptionMixin),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('name', models.CharField(max_length=64, help_text='Anglified name, safe for computing. ASCII!', verbose_name='External name')),
                ('internal_name', models.CharField(max_length=64, help_text='What the speakers call their language. All of unicode OK', blank=True, verbose_name='Internal name')),
                ('slug', models.SlugField(max_length=64, null=True, blank=True, editable=False)),
                ('author', models.CharField(verbose_name='Author(s)', max_length=128)),
                ('homepage', models.URLField(blank=True, null=True)),
                ('background', models.CharField(help_text='A short summary of the history/background of\n            your language. 4 lines (256 letters) inc. formatting, no HTML.', blank=True, max_length=256)),
                ('background_type', models.CharField(max_length=20, blank=True, choices=[('rst', 'RestructuredText'), ('plaintext', 'plaintext')])),
                ('from_earth', models.NullBooleanField(help_text="Example: Klingon and Barsoomian (from Mars!) would set 'No' here, while\n            Brithenig and Esperanto would set 'Yes'. As for Sindarin, it\n            depends on whether you consider Arda to be the Earth")),
                ('greeting', models.CharField(db_column='greeting', blank=True, max_length=64)),
                ('vocabulary_size', models.PositiveIntegerField(help_text='Estimated vocabulary size', blank=True, null=True)),
                ('natlang', models.BooleanField(default=False, editable=False)),
                ('average_score', models.IntegerField(default=0, editable=False)),
                ('num_features', models.IntegerField(default=0, editable=False)),
                ('num_avg_features', models.IntegerField(default=0, editable=False)),
                ('visible', models.BooleanField(default=True)),
                ('public', models.BooleanField(verbose_name='Editable by all', help_text='If yes/on, all logged in may edit. If no/off, only the\n            manager and editors may edit.', default=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_modified', models.DateTimeField(default=django.utils.timezone.now, null=True, blank=True, editable=False)),
            ],
            options={
                'get_latest_by': 'last_modified',
                'db_table': 'cals_language',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='LanguageFamily',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('path', models.CharField(max_length=255, blank=True, default='')),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(null=True, blank=True, editable=False)),
                ('part_of', models.ForeignKey(default=None, to='cals.LanguageFamily', null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'language families',
                'db_table': 'cals_languagefamily',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='LanguageFeature',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('feature', models.ForeignKey(to='cals.Feature', related_name='languages')),
            ],
            options={
                'db_table': 'cals_languagefeature',
            },
            bases=(models.Model, cals.tools.models.DescriptionMixin),
        ),
        migrations.CreateModel(
            name='LanguageName',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('added', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(max_length=64, blank=True, editable=False)),
                ('internal', models.BooleanField(verbose_name='Internal name?', default=False)),
                ('alternate', models.BooleanField(verbose_name='Additional?', default=False)),
                ('previous', models.BooleanField(verbose_name='No longer in use?', default=False)),
            ],
            options={
                'verbose_name_plural': 'language names',
                'db_table': 'cals_languagenames',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='profile', primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=30, unique=True, editable=False)),
                ('display_name', models.CharField(max_length=32, help_text='Replaces username everywhere but in urls.', blank=True, null=True)),
                ('slug', models.SlugField(max_length=64, unique=True, editable=False)),
                ('show_username', models.NullBooleanField(verbose_name='Always show username', help_text='Show username everywhere, even if display name have been set.')),
                ('homepage', models.URLField(blank=True, null=True)),
                ('homepage_title', models.CharField(blank=True, max_length=64)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('altitude', models.IntegerField(null=True, blank=True, default=0)),
                ('date_format', models.CharField(max_length=16, default='Y-m-d H:i O')),
                ('is_visible', models.BooleanField(default=True)),
                ('is_lurker', models.BooleanField(default=True)),
                ('seen_profile', models.BooleanField(default=False, editable=False)),
                ('seen_ipv6', models.DateTimeField(null=True, editable=False)),
                ('country', models.ForeignKey(to='countries.Country', null=True, blank=True)),
            ],
            options={
                'db_table': 'cals_profile',
                'ordering': ('display_name',),
            },
        ),
        migrations.CreateModel(
            name='WALSCode',
            fields=[
                ('language', models.OneToOneField(to='cals.Language', related_name='wals_code', primary_key=True, serialize=False)),
                ('walscode', models.CharField(max_length=3, unique=True)),
            ],
            options={
                'db_table': 'cals_walscodes',
            },
        ),
        migrations.AddField(
            model_name='profile',
            name='native_tongue',
            field=models.ForeignKey(to='cals.Language', help_text="If your L1 is not in the list, or you are multilingual, don't select anything.", null=True, blank=True),
        ),
        migrations.AddField(
            model_name='languagename',
            name='language',
            field=models.ForeignKey(to='cals.Language', related_name='alternate_names'),
        ),
        migrations.AddField(
            model_name='languagefeature',
            name='language',
            field=models.ForeignKey(to='cals.Language', related_name='features'),
        ),
        migrations.AddField(
            model_name='languagefeature',
            name='value',
            field=models.ForeignKey(to='cals.FeatureValue', related_name='languages'),
        ),
        migrations.AddField(
            model_name='language',
            name='added_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='languages', null=True, blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='language',
            name='blogentries',
            field=models.ManyToManyField(to='blog.Entry', related_name='languages', blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='editors',
            field=models.ManyToManyField(related_name='edits', to=settings.AUTH_USER_MODEL, help_text='People who get to change the description of this language.', blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='family',
            field=models.ForeignKey(to='cals.LanguageFamily', related_name='languages', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='last_modified_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='languages_modified', null=True, blank=True, editable=False),
        ),
        migrations.AddField(
            model_name='language',
            name='manager',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, help_text='The person who controls who gets to\n            change the description of this language. This makes \n            it possible to hand a language over to another person.', related_name='manages', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='tags',
            field=taggit.managers.TaggableManager(through='taggit.TaggedItem', help_text='A comma-separated list of tags.', to='taggit.Tag', verbose_name='Tags', blank=True),
        ),
        migrations.AddField(
            model_name='feature',
            name='added_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='feature',
            name='category',
            field=models.ForeignKey(to='cals.Category'),
        ),
        migrations.AddField(
            model_name='feature',
            name='overrides',
            field=models.ForeignKey(to='cals.Feature', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='externalinfo',
            name='language',
            field=models.ForeignKey(to='cals.Language', related_name='externalinfo'),
        ),
        migrations.AddField(
            model_name='description',
            name='last_modified_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='descriptions', null=True, blank=True, editable=False),
        ),
        migrations.AlterUniqueTogether(
            name='languagename',
            unique_together=set([('language', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='languagefeature',
            unique_together=set([('language', 'feature')]),
        ),
        migrations.AlterUniqueTogether(
            name='featurevalue',
            unique_together=set([('feature', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='feature',
            unique_together=set([('id', 'name', 'category')]),
        ),
    ]
