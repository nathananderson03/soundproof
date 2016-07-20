# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0008_auto_20150514_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='display',
            name='images_to_load',
            field=models.CharField(default=b'5,10', help_text=b'How many images to load at a time, for example "5,10" means\n        load 5 images, then 10, then 5, then 10, repeating', max_length=50),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='display',
            name='minimum_flips',
            field=models.PositiveIntegerField(default=3, help_text=b'Always flip this many images per load, even if there are no new images'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='display',
            name='speed',
            field=models.PositiveIntegerField(default=5, help_text=b'Minimum time between loading new images'),
            preserve_default=True,
        ),
    ]
