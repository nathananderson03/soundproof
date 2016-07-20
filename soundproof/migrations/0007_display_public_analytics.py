# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0006_auto_20150507_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='display',
            name='public_analytics',
            field=models.BooleanField(default=False, help_text=b'Can anyone with the URL access the analytics page?'),
            preserve_default=True,
        ),
    ]
