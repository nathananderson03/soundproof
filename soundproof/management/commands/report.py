import datetime

from django.core.management.base import BaseCommand
from django.utils.timezone import get_current_timezone

from soundproof.models import InstagramImage
from soundproof.instagram import get_report

TAGS = ('udaustralia',)
PERIOD = (
    datetime.datetime(2015, 3, 27, 0, 0, tzinfo=get_current_timezone()),
    datetime.datetime(2015, 3, 28, 0, 0, tzinfo=get_current_timezone()),
)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        report_data = get_report(TAGS, PERIOD)
