# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('method', models.CharField(max_length=20, verbose_name='method')),
                ('domain', models.CharField(max_length=100, verbose_name='domain')),
                ('port', models.PositiveSmallIntegerField(default=80)),
                ('path', models.CharField(max_length=250, verbose_name='path')),
                ('date', models.DateTimeField(auto_now=True)),
                ('querykey', models.CharField(verbose_name='query key', max_length=255, editable=False)),
            ],
            options={
                'get_latest_by': 'date',
                'verbose_name': 'request',
                'verbose_name_plural': 'requests',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RequestParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(default=b'G', max_length=1, choices=[(b'G', b'GET'), (b'P', b'POST')])),
                ('order', models.PositiveSmallIntegerField(default=1)),
                ('name', models.CharField(max_length=100, verbose_name='naam')),
                ('value', models.CharField(max_length=250, null=True, verbose_name='value', blank=True)),
                ('request', models.ForeignKey(related_name='parameters', verbose_name='request', to='httpproxy.Request')),
            ],
            options={
                'ordering': ('order',),
                'verbose_name': 'request parameter',
                'verbose_name_plural': 'request parameters',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.PositiveSmallIntegerField(default=200)),
                ('content_type', models.CharField(max_length=200, verbose_name='inhoudstype')),
                ('content', models.TextField(verbose_name='inhoud')),
                ('request', models.OneToOneField(verbose_name='request', to='httpproxy.Request')),
            ],
            options={
                'verbose_name': 'response',
                'verbose_name_plural': 'responses',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='request',
            unique_together=set([('method', 'domain', 'port', 'path', 'querykey')]),
        ),
    ]
