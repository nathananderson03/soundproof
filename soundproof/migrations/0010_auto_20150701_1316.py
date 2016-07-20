# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0009_auto_20150529_1535'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photoframe',
            name='url',
        ),
        migrations.AddField(
            model_name='photoframe',
            name='frame',
            field=models.ImageField(default='', upload_to=b'frames'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='display',
            name='seed_urls',
            field=models.TextField(help_text=b'image urls (instagram / iconosquare) to be automatically downloaded and approved, one per line', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='display',
            name='speed',
            field=models.PositiveIntegerField(default=5, help_text=b'Minimum time between loading new images (seconds)'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='display',
            name='tags',
            field=models.TextField(help_text=b'comma separated list, no spaces, all on one line, no # symbol (eg funny,fail)', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='photoframe',
            name='name_font',
            field=models.FileField(upload_to=b'fonts'),
            preserve_default=True,
        ),
    ]
