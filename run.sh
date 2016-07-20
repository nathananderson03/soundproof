#!/bin/sh
set -e

if [ -f ../env/bin/activate ]; then
    . ../env/bin/activate
fi

IP=0.0.0.0
PORT=$1
if [ -z ${PORT} ]; then
    PORT=9002
fi

python manage.py runserver ${IP}:${PORT}
