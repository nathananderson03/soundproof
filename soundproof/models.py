#pylint: skip-file

from __future__ import absolute_import, print_function

import hashlib
import re
import os
import string
import json
import time
import datetime

from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.utils.timezone import now
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.cache import cache
from django.contrib.auth.models import User as AuthUser

from . import util


MODERATION_TYPES = (
    ('off','No moderation, all images are displayed'),
    ('whitelist','Only show approved images'),
    ('blacklist','Show all but rejected images'),
)

try:
    if settings.DEFAULT_FILE_STORAGE == 'storages.backends.s3boto.S3BotoStorage':
        import boto.s3
        s3_conn = boto.s3.connect_to_region(settings.AWS['REGION'])
        s3_bucket = s3_conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
except:
    pass

class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    mug_url = models.URLField()
    follower_count = models.PositiveIntegerField(default=0)

    # this is when the users follower set was last fetched
    last_updated = models.DateTimeField(blank=True)

    def set_mug_url(self, url):
        if url != self.mug_url:
            self.mug_url = url
            self.save(update_fields=['mug_url'])

    @property
    def mug(self):
        return MugImage(self.mug_url)

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        # prioritize fetching followers for new users
        if not self.last_updated:
            self.last_updated = now() - datetime.timedelta(weeks=10*52)
        super(User, self).save(*args, **kwargs)

    def instagram_page_url(self):
        return 'https://instagram.com/{}'.format(self.username)

class DisplayFollowers(models.Model):
    display = models.ForeignKey('Display')
    followers = models.TextField() # comma separated list

    def __unicode__(self):
        count = len(self.followers.split(','))
        return '{} {}'.format(self.display.name, count)

class LoadableImage(object):
    def load(self):
        return util.load_image_url(self.get_absolute_url())

class MugImage(LoadableImage):
    """Convenience class, doesn't do any DB calls
    """
    def __init__(self, url):
        self.url = url

    def get_absolute_url(self):
        return self.url

class Image(LoadableImage, models.Model):
    page_url = models.URLField()
    url = models.URLField(unique=True)
    cached_url = models.URLField(blank=True)
    meta = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(User)
    remote_timestamp = models.DateTimeField(db_index=True)

    def as_dict(self):
        return {
            'id':self.id,
            'src':self.get_image_url,
            'meta':json.loads(self.meta),
            'remote_ts':self.remote_unixtime,
            'page_url':self.page_url,
            'age': self.get_pretty_age(),
            'user_mug': self.user.mug_url,
        }

    @property
    def get_image_url(self):
        return self.cached_url or self.url

    @property
    def remote_unixtime(self):
        return time.mktime(self.remote_timestamp.timetuple())

    def get_pretty_age(self):
        delta = now() - self.remote_timestamp
        seconds = delta.total_seconds()
        days = round(seconds/86400)
        weeks = round(days/7)
        months = round(days/30)

        created = self.remote_timestamp
        if months > 1:
            compareto = created + datetime.timedelta(days=30*months)
        elif weeks > 1:
            compareto = created + datetime.timedelta(days=7*weeks)
        elif days > 1:
            compareto = created + datetime.timedelta(days=days)
        else:
            compareto = now()

        template = Template('{{created|timesince:compareto}} ago')
        context = Context({'created':created, 'compareto':compareto})
        return template.render(context)

    def get_absolute_url(self):
        return self.get_image_url

class InstagramImage(Image):
    instagram_id = models.CharField(max_length=128)
    tags = models.ManyToManyField('InstagramTag')
    like_count = models.PositiveIntegerField(default=0, db_index=True)
    comment_count = models.PositiveIntegerField(default=0, db_index=True)

    def __unicode__(self):
        return self.tag_str()

    def tag_str(self):
        return ', '.join(self.tags.all().values_list('name',flat=True))

class InstagramTag(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    max_tag_id = models.BigIntegerField(default=0)

    def get_split_tags(self):
        # tokenise and strip the tags
        return [s.lower().strip() for s in self.tags.split(',') if s.strip()]

    def __unicode__(self):
        return self.name

class Display(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(db_index=True)

    admins = models.ManyToManyField(AuthUser)

    tile_width = models.CharField(max_length=50, default='10vw', blank=True)
    tile_margin = models.CharField(max_length=50, default='0%', blank=True)
    background_color = models.CharField(max_length=50, blank=True)

    border_color = models.CharField(max_length=50, default='white')
    logo = models.ImageField(upload_to='logos', blank=True, null=True)

    css = models.TextField(blank=True)

    tags = models.TextField(blank=True,
        help_text='comma separated list, no spaces, all on one line, no # symbol (eg funny,fail)')

    seed_urls = models.TextField(blank=True,
        help_text='image urls (instagram / iconosquare) to be automatically downloaded and approved, comma separated list')

    moderation = models.CharField(max_length=50, choices=MODERATION_TYPES,
        default='off')
    active = models.BooleanField(default=True)

    # image loading
    speed = models.PositiveIntegerField(default=5,
        help_text='Minimum time between loading new images (seconds)')
    minimum_flips = models.PositiveIntegerField(default=3,
        help_text='Always flip this many images per load, even if there are no new images')
    images_to_load = models.CharField(max_length=50, default='5,10',
        help_text='''How many images to load at a time, for example "5,10" means
        load 5 images, then 10, then 5, then 10, repeating''')

    # internal

    last_updated = models.DateTimeField(auto_now=True)

    public_analytics = models.BooleanField(default=False,
        help_text='Can anyone with the URL access the analytics page?')

    def auth_user(self, user):
        return user.is_superuser or user in self.admins.all()

    def tile_hcount(self):
        return int(100/float(re.sub(r'[^.\d]','',self.tile_width)))

    def get_absolute_url(self):
        return reverse('feed', args=(self.slug,))

    def get_highest_ts(self):
        try:
            tags = self.get_split_tags()
            img = Image.objects\
                .filter(instagramimage__tags__name__in=tags)\
                .order_by('-remote_timestamp')[0]
            return img.remote_unixtime
        except:
            return 0

    def get_split_tags(self):
        # tokenise and strip the tags
        return [s.lower().strip() for s in self.tags.split(',') if s.strip()]

    def get_split_seed_urls(self):
        return map(string.strip, self.seed_urls.split(','))

    @classmethod
    def get_unique_tags(cls):
        tags = set()
        for d in Display.objects.filter(active=True):
            tags.update(set(d.get_split_tags()))
        return tags

    @classmethod
    def update_subscriptions(cls):
        # compare local and subscribed tags
        # and get the added and removed tags
        subscriptions = instagram.subscriptions()

        model_tags = Display.get_unique_tags()
        sub_tags = subscriptions.tags

        added = model_tags - sub_tags
        removed = sub_tags - model_tags

        # convert removed tags to ids
        removed_ids = map(subscriptions.tag_id, removed)

        try:
            map(instagram.add_subscription, added)
            map(instagram.remove_subscription, removed_ids)
        except:
            pass

    def process_seed_urls(self):
        tags = self.get_split_tags()
        for url in self.get_split_seed_urls():
            print('Seed url {}'.format(url))
            image = instagram.add_instagram_image(tags=tags, url=url)
            if image:
                # approve the images
                print('Adding approval')
                di, _ = DisplayImage.objects.get_or_create(
                    display=self,
                    image=image
                )
                di.approved = True
                di.save()

    def __unicode__(self):
        return self.name

    def admin_links(self):
        return (
            (reverse('grid',args=(self.slug,)),'Grid config'),
            (reverse('moderate',args=(self.slug,)),'Moderate'),
            (reverse('analytics',args=(self.slug,)),'Analytics'),
            (self.get_absolute_url(),'View on site'),
        )

    def images(self, date_from=None, date_to=None):
        tags = self.get_split_tags()
        images = InstagramImage.objects\
            .filter(tags__name__in=tags)
        if date_from:
            images = images.filter(remote_timestamp__gte=date_from)
        if date_to:
            images = images.filter(remote_timestamp__lte=date_to)
        return images.distinct()

    def comment_count(self, date_from=None, date_to=None):
        return self.images(date_from, date_to)\
            .aggregate(models.Sum('comment_count'))['comment_count__sum']

    def like_count(self, date_from=None, date_to=None):
        return self.images(date_from, date_to)\
            .aggregate(models.Sum('like_count'))['like_count__sum']

    def log_stats(self):
        args = {
            'display': self,
            'total_like_count': self.like_count(),
            'total_comment_count': self.comment_count(),
            'total_image_count': self.images().count(),
        }
        if not args['total_like_count']:
            args['total_like_count'] = 0
        if not args['total_comment_count']:
            args['total_comment_count'] = 0
        if not args['total_image_count']:
            args['total_image_count'] = 0
        try:
            last = DisplayEngagementLog.objects\
                .filter(display=self)\
                .order_by('-timestamp')[0]
            args['interval_like_count'] = max(0, args['total_like_count']
                - last.total_like_count)
            args['interval_comment_count'] = max(0, args['total_comment_count']
                - last.total_comment_count)
            args['interval_image_count'] = max(0, args['total_image_count']
                - last.total_image_count)
        except:
            args['interval_like_count'] = args['total_like_count']
            args['interval_comment_count'] = args['total_comment_count']
            args['interval_image_count'] = args['total_image_count']

        DisplayEngagementLog.objects.create(**args)

@receiver(pre_save, sender=Display)
def display_asciify_tags(sender, instance, signal, *args, **kwargs):
    # ensure tags dont contain unicode
    instance.tags = util.asciify(instance.tags)

@receiver(post_save, sender=Display)
def display_update_subscriptions(sender, instance, signal, *args, **kwargs):
    # update our instagram subscriptions
    if settings.INSTAGRAM_ENABLE_SUBSCRIPTIONS:
        Display.update_subscriptions()

@receiver(post_save, sender=Display)
def display_seed_scrape(sender, instance, signal, *args, **kwargs):
    # seed our initial images
    seed = cache.get(settings.CACHE_KEY_SEED_DISPLAY, [])
    seed.append(instance.id)
    cache.set(settings.CACHE_KEY_SEED_DISPLAY, seed, settings.CACHE_TIMEOUT)

@receiver(post_save, sender=Display)
def display_historic_scrape(sender, instance, signal, *args, **kwargs):
    # perform a historic scrape
    #if settings.INSTAGRAM_ENABLE_HISTORIC_SCRAPE and \
    #        instance.images().count < settings.INSTAGRAM_HISTORIC_IMAGE_COUNT:
    if settings.INSTAGRAM_ENABLE_HISTORIC_SCRAPE:
        tags = instance.get_split_tags()
        # preferably this would be sent to a worker
        # saving too many displays could cause a number of issues
        #cmd = ["python", "manage.py", "instagram_historic"] + tags
        #Popen(cmd, shell=False, stdin=None, stdout=None, stderr=None, close_fds=True)
        historic = cache.get(settings.CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE,[])
        historic += tags
        cache.set(settings.CACHE_KEY_INSTAGRAM_HISTORIC_SCRAPE, historic, settings.CACHE_TIMEOUT)


class DisplayImage(models.Model):
    display = models.ForeignKey(Display, db_index=True)
    image = models.ForeignKey(Image, related_name='displayimage')
    approved = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('display', 'image',),)

class PhotoFrame(LoadableImage, models.Model):
    frame = models.ImageField(upload_to='frames')
    inset_string = models.CommaSeparatedIntegerField(max_length=64, db_column='inset')
    mug_string = models.CommaSeparatedIntegerField(max_length=64, db_column='mug')
    name_string = models.CharField(max_length=64, db_column='name')
    name_colour_string = models.CommaSeparatedIntegerField(max_length=12, db_column='name_colour')
    name_font = models.FileField(upload_to='fonts')
    name_font_size = models.IntegerField()

    class Box(object):
        """Parses a CommaSeparatedIntegerField.

        Provides convenient access to the values contained in the field.
        The field is stored in the format "x1,y1,x2,y2" ("left,top,right,bottom")
        as a string.
        The class provides properties to access these, and other convenient
        functions.
        """
        def __init__(self, str):
            self._str = str

        @property
        def size(self):
            return (self.width, self.height)

        @property
        def box(self):
            return (self.left, self.top, self.right, self.bottom)

        @property
        def values(self):
            return map(int, self._str.split(','))

        @property
        def left(self):
            return self.values[0]

        @property
        def right(self):
            return self.values[2]

        @property
        def top(self):
            return self.values[1]

        @property
        def bottom(self):
            return self.values[3]

        @property
        def width(self):
            return self.values[2] - self.values[0]

        @property
        def height(self):
            return self.values[3] - self.values[1]

        @property
        def top_left(self):
            return self.values[0], self.values[1]

        def __unicode__(self):
            return self._str

    def cache_font(self):
        # bullshit to work around PIL not being able to load fonts from
        # data/open file handlers (it only accepts a path, which doesnt work
        # with S3, so instead we make a local copy of the file and return the
        # path to *that*)

        # TODO hashing on name might not work if the user uploads a different
        # version of the file with the same name
        h = hashlib.md5(self.name_font.name).hexdigest()
        base, ext = os.path.splitext(os.path.basename(self.name_font.name))
        fn = os.path.join(settings.BASE_DIR, 'font-cache', '{}{}'.format(h, ext))

        if not os.path.exists(fn):
            # tried using FieldFile.open but it doesnt work, falling back to boto
            key = s3_bucket.get_key(self.name_font.name)
            with open(fn,'wb') as local_fp:
                local_fp.write(key.read())

        return fn

    def frame_image(self, photo):
        frame = self.load()
        img = photo.load()

        # resize the photo
        # paste the image
        img = img.resize(self.inset.size)
        frame.paste(img, self.inset.box)

        # get the user mug and name
        user = photo.user
        if self.name_string:
            username = user.username
            colour = self.name_colour
            font = self.cache_font()
            font_size = self.name_font_size
            util.draw_text(frame, username, self.name.top_left, colour, font=font, fontsize=font_size)

        if self.mug_string:
            mug = user.mug.load()
            mug = mug.resize(self.mug.size)
            frame.paste(mug, self.mug.box)

        return frame

    def get_absolute_url(self):
        return self.frame.url

    @property
    def inset(self):
        return PhotoFrame.Box(self.inset_string)

    @property
    def mug(self):
        return PhotoFrame.Box(self.mug_string)

    @property
    def name(self):
        return PhotoFrame.Box(self.name_string)

    @property
    def name_colour(self):
        return map(int, self.name_colour_string.split(','))


class DisplayEngagementLog(models.Model):
    display = models.ForeignKey(Display)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    interval_like_count = models.PositiveIntegerField()
    interval_comment_count = models.PositiveIntegerField()
    interval_image_count = models.PositiveIntegerField()

    total_like_count = models.PositiveIntegerField()
    total_comment_count = models.PositiveIntegerField()
    total_image_count = models.PositiveIntegerField()

    def __unicode__(self):
        return '{} {}'.format(self.display, self.timestamp)


class PrintedPhoto(models.Model):
    image = models.ForeignKey(Image)
    frame = models.ForeignKey(PhotoFrame)
    created = models.DateTimeField(auto_now_add=True)

from . import instagram
