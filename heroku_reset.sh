#!/usr/bin/env bash

set -e

APP="vast-springs-5239"
URL="vast-springs-5239.herokuapp.com"

heroku ps:stop web -a ${APP}
heroku pg:reset DATABASE -a ${APP} --confirm ${APP}

git push heroku master

echo "set -e && python manage.py syncdb --noinput && python manage.py createcachetable && python manage.py loaddata auth sites photoframe adam && exit" | heroku run bash -a ${APP}

echo 'echo "
from django.contrib.sites.models import *
s = Site.objects.all()[0]
s.domain = '\'${URL}\''
s.save()
" | python manage.py shell && exit' | heroku run bash -a ${APP}

heroku ps:restart web -a ${APP}
