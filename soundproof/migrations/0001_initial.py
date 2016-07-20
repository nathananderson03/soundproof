# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import soundproof.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Display',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField()),
                ('tile_width', models.CharField(default=b'10vw', max_length=50, blank=True)),
                ('tile_margin', models.CharField(default=b'0%', max_length=50, blank=True)),
                ('background_color', models.CharField(max_length=50, blank=True)),
                ('css', models.TextField(blank=True)),
                ('tags', models.TextField(blank=True)),
                ('seed_urls', models.TextField(help_text=b'image urls (instagram / iconosquare) to be automatically downloaded and approved', blank=True)),
                ('moderation', models.CharField(default=b'off', max_length=50, choices=[(b'off', b'No moderation, all images are displayed'), (b'whitelist', b'Only show approved images'), (b'blacklist', b'Show all but rejected images')])),
                ('speed', models.PositiveIntegerField(default=5, help_text=b'minimum time between loading new images')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DisplayImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('display', models.ForeignKey(to='soundproof.Display')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page_url', models.URLField()),
                ('url', models.URLField(unique=True)),
                ('cached_url', models.URLField(blank=True)),
                ('meta', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('remote_timestamp', models.DateTimeField(db_index=True)),
            ],
            options={
            },
            bases=(soundproof.models.LoadableImage, models.Model),
        ),
        migrations.CreateModel(
            name='InstagramImage',
            fields=[
                ('image_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='soundproof.Image')),
                ('instagram_id', models.CharField(max_length=128)),
                ('like_count', models.PositiveIntegerField(default=0, db_index=True)),
                ('comment_count', models.PositiveIntegerField(default=0, db_index=True)),
            ],
            options={
            },
            bases=('soundproof.image',),
        ),
        migrations.CreateModel(
            name='InstagramTag',
            fields=[
                ('name', models.CharField(max_length=50, serialize=False, primary_key=True)),
                ('max_tag_id', models.BigIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PhotoFrame',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(unique=True)),
                ('inset_string', models.CommaSeparatedIntegerField(max_length=64, db_column=b'inset')),
                ('mug_string', models.CommaSeparatedIntegerField(max_length=64, db_column=b'mug')),
                ('name_string', models.CharField(max_length=64, db_column=b'name')),
                ('name_colour_string', models.CommaSeparatedIntegerField(max_length=12, db_column=b'name_colour')),
                ('name_font', models.CharField(max_length=256)),
                ('name_font_size', models.IntegerField()),
            ],
            options={
            },
            bases=(soundproof.models.LoadableImage, models.Model),
        ),
        migrations.CreateModel(
            name='PrintedPhoto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('frame', models.ForeignKey(to='soundproof.PhotoFrame')),
                ('image', models.ForeignKey(to='soundproof.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=50)),
                ('mug_url', models.URLField()),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='instagramimage',
            name='tags',
            field=models.ManyToManyField(to='soundproof.InstagramTag'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='user',
            field=models.ForeignKey(to='soundproof.User'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='displayimage',
            name='image',
            field=models.ForeignKey(related_name='displayimage', to='soundproof.Image'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='displayimage',
            unique_together=set([('display', 'image')]),
        ),
        migrations.AddField(
            model_name='display',
            name='admins',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
