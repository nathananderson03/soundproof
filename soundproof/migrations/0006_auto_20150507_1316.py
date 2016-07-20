# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0005_user_follower_count'),
    ]

    operations = [
        migrations.RenameField(
            model_name='displayengagementlog',
            old_name='inverval_image_count',
            new_name='interval_image_count',
        ),
    ]
