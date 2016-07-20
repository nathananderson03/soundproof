from __future__ import absolute_import
from django.conf import settings
import kvstore

_image_store = None
def image_store():
    global _image_store
    if not _image_store:
        _image_store = kvstore.create(**settings.STORES['image']['kvstore'])
    return _image_store
