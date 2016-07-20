#!/usr/bin/env bash

set -e

if [ -f ../env/bin/activate ]; then
    . ../env/bin/activate
fi

DATABASE_NAME=`python -c "
import soundproof
soundproof.initialise_django()
from django.conf import settings
print settings.DATABASES['default']['NAME']
"`
DATABASE_USER=`python -c "
import soundproof
soundproof.initialise_django()
from django.conf import settings
print settings.DATABASES['default']['USER']
"`

echo "drop database if exists ${DATABASE_NAME}" | mysql -u ${DATABASE_USER}
echo "create database ${DATABASE_NAME}" | mysql -u ${DATABASE_USER}

python manage.py syncdb --noinput

FIXTURES=(
    auth
    sites
    user
    image
    instagram_image
    instagram_tag
    display
    display_image
    photo_frame
    printed_photo
)

python manage.py loaddata ${FIXTURES[@]}
