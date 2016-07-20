# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0003_auto_20150507_1200'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='follower',
            name='followee',
        ),
        migrations.RemoveField(
            model_name='follower',
            name='follower',
        ),
        migrations.DeleteModel(
            name='Follower',
        ),
    ]
