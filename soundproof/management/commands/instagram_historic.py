from __future__ import absolute_import, print_function
from django.core.management.base import BaseCommand
from django.conf import settings
from ... import instagram

class Command(BaseCommand):
    def __init__(self):
        super(Command, self).__init__()

    def handle(self, *args, **kwargs):
        for tag in args:
            print('Loading tag "{}"'.format(tag))
            instagram.scrape_instagram_tag(tag, settings.INSTAGRAM_HISTORIC_IMAGE_COUNT)