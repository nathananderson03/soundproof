#!/bin/bash

set -e

python manage.py dumpdata auth.User auth.permission | python -mjson.tool > soundproof/fixtures/auth.json
python manage.py dumpdata sites | python -mjson.tool > soundproof/fixtures/sites.json
python manage.py dumpdata soundproof.User | python -mjson.tool > soundproof/fixtures/user.json
python manage.py dumpdata soundproof.Image | python -mjson.tool > soundproof/fixtures/image.json
python manage.py dumpdata soundproof.InstagramImage | python -mjson.tool > soundproof/fixtures/instagram_image.json
python manage.py dumpdata soundproof.InstagramTag | python -mjson.tool > soundproof/fixtures/instagram_tag.json
python manage.py dumpdata soundproof.Display | python -mjson.tool > soundproof/fixtures/display.json
python manage.py dumpdata soundproof.DisplayImage | python -mjson.tool > soundproof/fixtures/display_image.json
python manage.py dumpdata soundproof.PhotoFrame | python -mjson.tool > soundproof/fixtures/photo_frame.json
python manage.py dumpdata soundproof.PrintedPhoto | python -mjson.tool > soundproof/fixtures/printed_photo.json
