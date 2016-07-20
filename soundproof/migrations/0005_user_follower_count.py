# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0004_auto_20150507_1204'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='follower_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]
