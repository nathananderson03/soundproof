# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('soundproof', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Follower',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('followee', models.ForeignKey(related_name='+', to='soundproof.User')),
                ('follower', models.ForeignKey(related_name='+', to='soundproof.User')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
