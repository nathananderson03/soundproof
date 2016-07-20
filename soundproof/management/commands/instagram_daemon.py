#pylint: skip-file

from __future__ import absolute_import, print_function

import datetime
import time

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from django.utils.timezone import now, get_current_timezone

from ...models import *
from ...instagram import (
    update_instagram_tag,
    scrape_instagram_tag,
    refresh_users,
    refresh_images,
    log_engagement,
)

min_fetch_interval = datetime.timedelta(seconds=5)
tz = get_current_timezone()
beginning = now() - datetime.timedelta(days=365)

class Command(BaseCommand):
    def __init__(self):
        self.last_fetch = beginning
        self.more_work = False
        super(Command, self).__init__()

    def update(self):
        current_time = now()
        if self.more_work or current_time - self.last_fetch > min_fetch_interval:
            self.more_work = False
            if getattr(settings, 'FETCH_FOLLOWERS', False):
                self.more_work |= refresh_users()

            self.more_work |= refresh_images()

            log_engagement()

            # check for display seeding
            display_seed = cache.get(settings.CACHE_KEY_SEED_DISPLAY,[])
            if display_seed:
                print('Daemon found seed urls')
                cache.delete(settings.CACHE_KEY_SEED_DISPLAY)
                for display_id in display_seed:
                    try:
                        print('Seeding display "{}"'.format(display_id))
                        display = Display.objects.get(id=display_id)
                        display.process_seed_urls()
                    except:
                        pass

            # check for historic scraping
            historic_scrape = cache.get(settings.CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE, [])
            if historic_scrape:
                print('Daemon found historic tags')
                cache.delete(settings.CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE)
                for tag in historic_scrape:
                    try:
                        print('Scraping tag "{}"'.format(tag))
                        scrape_instagram_tag(tag, settings.INSTAGRAM_HISTORIC_IMAGE_COUNT)
                    except:
                        pass

            # check for instagram tags
            # TODO: this should probably just check all tags all the time
            instagram_update = cache.get(settings.CACHE_KEY_INSTAGRAM_UPDATE,[])
            if instagram_update:
                print('Daemon found update tags')
                cache.delete(settings.CACHE_KEY_INSTAGRAM_UPDATE)
                # iterate backwards through the tags
                for tag in instagram_update[::-1]:
                    try:
                        print('Updating tag "{}"'.format(tag))
                        model_tag = InstagramTag.objects.get(name=tag)
                        update_instagram_tag(tag, model_tag.max_tag_id)
                    except:
                        pass

    def handle(self, *args, **kwargs):
        while True:
            self.update()            
            if not self.more_work:
                time.sleep(1)
