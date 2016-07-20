# pylint: skip-file

from __future__ import absolute_import, print_function
import os
import StringIO
import hashlib
import unicodedata
import subprocess
import tempfile
import requests
import PIL.Image
import PIL.ImageFile
import PIL.ImageFont
import PIL.ImageDraw
from django.conf import settings
from .data_store import image_store

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36'

def hash_string(string):
    hash_object = hashlib.md5(bytes(string))
    return hash_object.hexdigest()

def download_image(url):
    headers = {
        'User-Agent': user_agent,
    }

    r = requests.get(url, headers=headers, stream=True)
    r.raise_for_status()

    # process in PIL
    parser = PIL.ImageFile.Parser()
    for chunk in r.iter_content(1024):
        parser.feed(chunk)
    im = parser.close()
    return im

def download_image_raw(url):
    headers = {
        'User-Agent': user_agent,
    }

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    return r.content

def serialise_image(im, format=None):
    format = format or im.format
    output = StringIO.StringIO()
    im.save(output, format=format)
    data = output.getvalue()
    output.close()
    return data

def url_for_key(path, key, *args, **kwargs):
    if path.startswith('file://'):
        return fs_url(path, key, *args, **kwargs)
    elif path.startswith('s3://'):
        return s3_url(path, key, *args, **kwargs)

def fs_url(path, key, fs_path, *args, **kwargs):
    if key.startswith('/'):
        key = key[1:]
    return os.path.join(fs_path, key)

def s3_url(path, key, bucket, region='s3', **kwargs):
    return 'https://{region}.amazonaws.com/{bucket}/{key}'.format(
        region=region, key=key, bucket=bucket,
    )

def cache_image(url):
    url_hash = hash_string(url)

    # get the file extension from the url
    # we could use PIL to get the file type, but it cannot give us
    # an extension, better to default to nothing
    ext = os.path.splitext(url)[1] or ''

    # for s3, its good to use a hash to distribute s3 requests
    # so use a small part of the hash as the dir
    key = '{dir}/{filename}{ext}'.format(
        dir=url_hash[-5:],
        filename=url_hash,
        ext=ext,
    )

    # get the url for the key
    store_url = url_for_key(
        settings.STORES['image']['kvstore']['path'],
        key,
        fs_path=settings.STORES['image'].get('fs_path'),
        bucket=settings.STORES['image'].get('bucket'),
        region=settings.STORES['image'].get('region')
    )

    # download and cache if the image isn't already in our file store
    if not image_store().exists(key):
        if settings.USE_PIL:
            print('Downloading image {}'.format(url))
            im = download_image(url)
            print('Serialising image {}'.format(url))
            data = serialise_image(im)
            print('Caching image {}'.format(url))
            image_store().put(key, data)
            print('Done')
        else:
            # just pass raw image data through - added this because sometimes
            # PIL seems to produce a black image
            data = download_image_raw(url)
            image_store().put(key, data)

    return store_url

def asciify(string):
    return unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')

def print_image(image):
    # resize the image
    # get the format now because it disappears if we resize it
    format = image.format
    print_size = map(lambda (x,y): x*y, zip(settings.PRINT_DPI, settings.PRINT_SIZE_INCHES))
    image = image.resize(print_size)


    if settings.PRINTER_USE_LPR:
        # serialise the image
        print('Serialising')
        data = serialise_image(image, format)

        # put the image into stdin
        print('Creating lpr')
        options = ' '.join(settings.PRINTER_OPTIONS)

        cmd = [
            'lpr',
            # printer to print to
            '-P', settings.PRINTER_NAME,
        ] + options.split(' ') + [
            # read from stdin
            '-s'
        ]
        print(cmd)
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        print('Writing data')
        proc.stdin.write(data)
        proc.stdin.flush()
        proc.stdin.close()
    else:
        # serialise the image
        # as a jpeg!
        print('Serialising')
        data = serialise_image(image, 'jpeg')

        # save the image somewhere
        print('Writing temp file')
        f = tempfile.NamedTemporaryFile(delete=False)
        f.file.write(data)
        f.file.flush()

        print('Running selphy')
        proc = subprocess.Popen([
            './soundproof/scripts/selphy.sh',
            # arg1 is the printer ip
            settings.PRINTER_SELPHY_PRINTER_IP,
            # arg2 is the file to print
            f.name,
        ])

    print('Done')

def load_image_url(url):
    if url.startswith('http://') or url.startswith('https://'):
        return download_image(url)
    if url.startswith('/'):
        url = url[1:]
    path = os.path.join('soundproof', url)
    return PIL.Image.open(path)

def draw_text(image, string, pos, colour=None, font=None, fontsize=12):
    if colour:
        colour = tuple(colour)
    print(image, string, pos, colour, font, fontsize)
    default_font = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'weblysleek_ui', 'weblysleekuil.ttf')
    font = font or default_font
    draw = PIL.ImageDraw.Draw(image)
    font = PIL.ImageFont.truetype(font, fontsize)

    draw.text(pos, string, fill=colour, font=font)
