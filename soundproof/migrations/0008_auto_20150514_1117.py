# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0007_display_public_analytics'),
    ]

    operations = [
        migrations.AddField(
            model_name='display',
            name='border_color',
            field=models.CharField(default=b'white', max_length=50),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='display',
            name='logo',
            field=models.ImageField(null=True, upload_to=b'logos', blank=True),
            preserve_default=True,
        ),
    ]
