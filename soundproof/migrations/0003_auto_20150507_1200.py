# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0002_follower'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisplayEngagementLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('interval_like_count', models.PositiveIntegerField()),
                ('interval_comment_count', models.PositiveIntegerField()),
                ('inverval_image_count', models.PositiveIntegerField()),
                ('total_like_count', models.PositiveIntegerField()),
                ('total_comment_count', models.PositiveIntegerField()),
                ('total_image_count', models.PositiveIntegerField()),
                ('display', models.ForeignKey(to='soundproof.Display')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DisplayFollowers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('followers', models.TextField()),
                ('display', models.ForeignKey(to='soundproof.Display')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='display',
            name='active',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='display',
            name='last_updated',
            field=models.DateTimeField(default=datetime.datetime(2014, 5, 7, 2, 0, 49, 403720, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='last_updated',
            field=models.DateTimeField(blank=True),
            preserve_default=True,
        ),
    ]
