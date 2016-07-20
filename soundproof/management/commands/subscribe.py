import requests

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        r = requests.post('https://api.instagram.com/v1/subscriptions/',data={
            'client_id':settings.INSTAGRAM_ID,
            'client_secret':settings.INSTAGRAM_SECRET,
            'verify_token':settings.INSTAGRAM_VERIFY_TOKEN,
            'callback_url':'http://soundproof.alhazan.ath.cx/instagram',
            'object':'tag',
            'object_id':'soundproof',
            'aspect':'media',
        })
        print r.text
        print r.headers
