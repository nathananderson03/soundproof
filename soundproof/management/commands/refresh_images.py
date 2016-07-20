#pylint: skip-file

from __future__ import absolute_import, print_function

import datetime
import time

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now, get_current_timezone

from ...models import InstagramImage
from ...instagram import refresh_social

CUTOFF_SECONDS = 60*60*24

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        while True:
            self.refresh()

    def refresh(self):
        cutoff = now() - datetime.timedelta(seconds=CUTOFF_SECONDS)
        images = InstagramImage.objects\
            .filter(last_updated__lt=cutoff)
        for image in images[0:10]:
            refresh_social(image)
        if not images.count():
            print('up to date')
        time.sleep(5)
