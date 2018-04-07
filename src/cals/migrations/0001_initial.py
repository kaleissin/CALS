# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone
import cals.tools.models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('blog', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taggit', '0002_auto_20150616_2121'),
        ('countries', '__first__'),
        ('calsaccount', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20, unique=True)),
                ('active', models.BooleanField(editable=False, default=False)),
            ],
            options={
                'db_table': 'cals_category',
                'ordering': ['id'],
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Description',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('freetext', models.TextField(default='', blank=True, null=True)),
                ('freetext_xhtml', models.TextField(editable=False, null=True)),
                ('freetext_type', models.CharField(max_length=20, choices=[('rst', 'RestructuredText'), ('plaintext', 'plaintext')], blank=True, default='plaintext')),
                ('freetext_link', models.URLField(blank=True, null=True)),
                ('last_modified', models.DateTimeField(editable=False, default=django.utils.timezone.now)),
                ('current', models.BooleanField(default=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'db_table': 'cals_description',
                'get_latest_by': 'last_modified',
            },
        ),
        migrations.CreateModel(
            name='ExternalInfo',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=20, choices=[('homepage', 'Homepage'), ('dictionary', 'Dictionary')])),
                ('on_request', models.BooleanField(default=False)),
                ('link', models.URLField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=96, unique=True)),
                ('wals', models.BooleanField(editable=False, default=False)),
                ('active', models.BooleanField(editable=False, default=False)),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('position', models.IntegerField(null=True)),
                ('feature', models.ForeignKey(related_name='values', to='cals.Feature')),
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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='External name', help_text='Anglified name, safe for computing. ASCII!')),
                ('internal_name', models.CharField(max_length=64, verbose_name='Internal name', blank=True, help_text='What the speakers call their language. All of unicode OK')),
                ('slug', models.SlugField(max_length=64, editable=False, blank=True, null=True)),
                ('author', models.CharField(max_length=128, verbose_name='Author(s)')),
                ('homepage', models.URLField(blank=True, null=True)),
                ('background', models.CharField(max_length=256, blank=True, help_text='A short summary of the history/background of\n            your language. 4 lines (256 letters) inc. formatting, no HTML.')),
                ('background_type', models.CharField(max_length=20, choices=[('rst', 'RestructuredText'), ('plaintext', 'plaintext')], blank=True)),
                ('from_earth', models.NullBooleanField(help_text="Example: Klingon and Barsoomian (from Mars!) would set 'No' here, while\n            Brithenig and Esperanto would set 'Yes'. As for Sindarin, it\n            depends on whether you consider Arda to be the Earth")),
                ('greeting', models.CharField(max_length=64, db_column='greeting', blank=True)),
                ('vocabulary_size', models.PositiveIntegerField(null=True, blank=True, help_text='Estimated vocabulary size')),
                ('natlang', models.BooleanField(editable=False, default=False)),
                ('average_score', models.IntegerField(editable=False, default=0)),
                ('num_features', models.IntegerField(editable=False, default=0)),
                ('num_avg_features', models.IntegerField(editable=False, default=0)),
                ('visible', models.BooleanField(default=True)),
                ('public', models.BooleanField(verbose_name='Editable by all', default=True, help_text='If yes/on, all logged in may edit. If no/off, only the\n            manager and editors may edit.')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_modified', models.DateTimeField(editable=False, default=django.utils.timezone.now, blank=True, null=True)),
            ],
            options={
                'db_table': 'cals_language',
                'ordering': ['name'],
                'get_latest_by': 'last_modified',
            },
        ),
        migrations.CreateModel(
            name='LanguageFamily',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('path', models.CharField(max_length=255, default='', blank=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(editable=False, blank=True, null=True)),
                ('part_of', models.ForeignKey(to='cals.LanguageFamily', default=None, blank=True, null=True)),
            ],
            options={
                'db_table': 'cals_languagefamily',
                'ordering': ('name',),
                'verbose_name_plural': 'language families',
            },
        ),
        migrations.CreateModel(
            name='LanguageFeature',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('feature', models.ForeignKey(related_name='languages', to='cals.Feature')),
            ],
            options={
                'db_table': 'cals_languagefeature',
            },
            bases=(models.Model, cals.tools.models.DescriptionMixin),
        ),
        migrations.CreateModel(
            name='LanguageName',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('added', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField(max_length=64, editable=False, blank=True)),
                ('internal', models.BooleanField(verbose_name='Internal name?', default=False)),
                ('alternate', models.BooleanField(verbose_name='Additional?', default=False)),
                ('previous', models.BooleanField(verbose_name='No longer in use?', default=False)),
            ],
            options={
                'db_table': 'cals_languagenames',
                'verbose_name_plural': 'language names',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL, serialize=False, primary_key=True)),
                ('username', models.CharField(max_length=30, editable=False, unique=True)),
                ('display_name', models.CharField(null=True, max_length=32, blank=True, help_text='Replaces username everywhere but in urls.')),
                ('slug', models.SlugField(max_length=64, editable=False, unique=True)),
                ('show_username', models.NullBooleanField(verbose_name='Always show username', help_text='Show username everywhere, even if display name have been set.')),
                ('homepage', models.URLField(blank=True, null=True)),
                ('homepage_title', models.CharField(max_length=64, blank=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('altitude', models.IntegerField(default=0, blank=True, null=True)),
                ('date_format', models.CharField(max_length=16, default='Y-m-d H:i O')),
                ('is_visible', models.BooleanField(default=True)),
                ('is_lurker', models.BooleanField(default=True)),
                ('seen_profile', models.BooleanField(editable=False, default=False)),
                ('seen_ipv6', models.DateTimeField(editable=False, null=True)),
                ('country', models.ForeignKey(to='countries.Country', blank=True, null=True)),
            ],
            options={
                'db_table': 'cals_profile',
                'ordering': ('display_name',),
            },
        ),
        migrations.CreateModel(
            name='Glottocode',
            fields=[
                ('language', models.OneToOneField(related_name='glottocode', to='cals.Language', serialize=False, primary_key=True)),
                ('glottocode', models.CharField(max_length=8, unique=True)),
            ],
            options={
                'db_table': 'cals_glottocode',
            },
        ),
        migrations.CreateModel(
            name='ISO639_3',
            fields=[
                ('language', models.OneToOneField(related_name='iso639_3', to='cals.Language', serialize=False, primary_key=True)),
                ('iso639_3', models.CharField(max_length=3, unique=True)),
            ],
            options={
                'db_table': 'cals_iso639_3',
                'verbose_name_plural': 'ISO 639-3',
                'verbose_name': 'ISO 639-3',
            },
        ),
        migrations.CreateModel(
            name='WALSCode',
            fields=[
                ('language', models.OneToOneField(related_name='walscode', to='cals.Language', serialize=False, primary_key=True)),
                ('walscode', models.CharField(max_length=3, unique=True)),
            ],
            options={
                'db_table': 'cals_walscodes',
            },
        ),
        migrations.AddField(
            model_name='profile',
            name='native_tongue',
            field=models.ForeignKey(to='cals.Language', blank=True, help_text="If your L1 is not in the list, or you are multilingual, don't select anything.", null=True),
        ),
        migrations.AddField(
            model_name='languagename',
            name='language',
            field=models.ForeignKey(related_name='alternate_names', to='cals.Language'),
        ),
        migrations.AddField(
            model_name='languagefeature',
            name='language',
            field=models.ForeignKey(related_name='features', to='cals.Language'),
        ),
        migrations.AddField(
            model_name='languagefeature',
            name='value',
            field=models.ForeignKey(related_name='languages', to='cals.FeatureValue'),
        ),
        migrations.AddField(
            model_name='language',
            name='added_by',
            field=models.ForeignKey(related_name='languages', to=settings.AUTH_USER_MODEL, blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='language',
            name='blogentries',
            field=models.ManyToManyField(related_name='languages', to='blog.Entry', blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='editors',
            field=models.ManyToManyField(related_name='edits', to=settings.AUTH_USER_MODEL, blank=True, help_text='People who get to change the description of this language.'),
        ),
        migrations.AddField(
            model_name='language',
            name='family',
            field=models.ForeignKey(related_name='languages', to='cals.LanguageFamily', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='last_modified_by',
            field=models.ForeignKey(related_name='languages_modified', to=settings.AUTH_USER_MODEL, blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='language',
            name='manager',
            field=models.ForeignKey(related_name='manages', to=settings.AUTH_USER_MODEL, blank=True, help_text='The person who controls who gets to\n            change the description of this language. This makes \n            it possible to hand a language over to another person.', null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='tags',
            field=taggit.managers.TaggableManager(verbose_name='Tags', to='taggit.Tag', blank=True, help_text='A comma-separated list of tags.', through='taggit.TaggedItem'),
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
            field=models.ForeignKey(to='cals.Feature', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='externalinfo',
            name='language',
            field=models.ForeignKey(related_name='externalinfo', to='cals.Language'),
        ),
        migrations.AddField(
            model_name='description',
            name='last_modified_by',
            field=models.ForeignKey(related_name='descriptions', to=settings.AUTH_USER_MODEL, blank=True, null=True, editable=False),
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
