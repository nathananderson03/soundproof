#pylint: skip-file

from __future__ import absolute_import, print_function

import sys
import pickle
import time
import datetime
import re
import json
import urlparse
import traceback
from httplib import ResponseNotReady
from httplib2 import ServerNotFoundError

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.db import IntegrityError
from django.db.models import Max
from django.utils.timezone import now
from django.core.cache import cache

import requests
from instagram import InstagramAPI, InstagramAPIError, InstagramClientError
import pytz

from .models import (
    InstagramImage, InstagramTag, User, DisplayEngagementLog,
    DisplayFollowers, Display
)
from . import util

api = InstagramAPI(
    client_id=settings.INSTAGRAM_ID,
    client_secret=settings.INSTAGRAM_SECRET,
)

IGNORE_ERRORS = (
    'invalid media id',
    'you cannot view this resource',
)

class Subscriptions(dict):
    def __init__(self, api):
        super(Subscriptions, self).__init__()
        self.update(api.list_subscriptions())

    @property
    def tags(self):
        return set([d['object_id'] for d in self['data']])

    def tag_id(self, tag):
        for s in self['data']:
            if s['object_id'] == tag:
                return s['id']
        raise KeyError

def subscriptions():
    return Subscriptions(api)

def add_subscription(tag):
    site = Site.objects.get_current()
    kwargs = {
        'object':'tag',
        'object_id':str(tag),
        'aspect':'media',
        'callback_url':'http://{}{}'.format(site.domain, reverse('instagram_callback')),
        'verify_token':settings.INSTAGRAM_VERIFY_TOKEN,
    }
    api.create_subscription(**kwargs)

def remove_subscription(id):
    api.delete_subscriptions(id=int(id))

def _extract_max_tag_id(url):
    parms = urlparse.parse_qs(urlparse.urlparse(url).query)
    return int(parms.get('max_tag_id')[0])

def _update_max_tag_id(tag, max_tag_id):
    model_tag, _ = InstagramTag.objects.get_or_create(name=tag)
    if max_tag_id > model_tag.max_tag_id:
        model_tag.max_tag_id = max_tag_id
        model_tag.save(update_fields=['max_tag_id'])

def _iterate_tag(tag, max_tag_id):
    """A generator allowing iteration over new media for a tag.
    """
    '''I've hacked this up to just fetch 10 images then quit - it seemed like it
    was just running back through older and older images forever - max_tag_id is
    confusing :( 
    -dg'''

    max_tag = int(max_tag_id) if max_tag_id else None
    while True:
        images, next_url = api.tag_recent_media(tag_name=tag, min_tag_id=max_tag_id)
        # continue until we have no more images
        if not len(images):
            break

        for image in images:
            yield image

        try:
            if not next_url:
                break

            max_tag_id = _extract_max_tag_id(next_url)
            # we need to take the max tag id and make it our
            # new min tag id
            # so we go forwards

            # update the max id tag
            _update_max_tag_id(tag, max_tag_id)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print(traceback.format_exc())

        if max_tag_id < max_tag:
            raise ValueError('Going backwards')
        max_tag = max_tag_id

def _scrape_tag(tag, count):
    """A generator allowing iteration over historic media for a tag.
    """
    loaded = 0
    while count:
        images, next_url = api.tag_recent_media(tag_name=tag, count=count)
        loaded += len(images)
        count -= len(images)

        for image in images:
            yield image

        try:
            if not next_url:
                print("No more pages")
                break

            # max_tag_id will be max id for next page in PAST
            # ie max_tag_id will be decremented
            max_tag_id = _extract_max_tag_id(next_url)

            # update the max id tag
            _update_max_tag_id(tag, max_tag_id)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            print(traceback.format_exc())

def _add_instagram_image(tags, im_data):
    try:
        url = im_data.images['standard_resolution'].url
        url = url.replace('https://','http://')
        print('Instagram image: {url}'.format(url=url))
        cached_url = util.cache_image(url)

        meta = {}
        try: meta['user'] = im_data.user.username
        except: pass
        try: meta['caption'] = im_data.caption.text
        except: pass

        user, _ = User.objects.get_or_create(username=im_data.user.username)
        user.set_mug_url(im_data.user.profile_picture)

        print('Creating DB instagram image')
        im = InstagramImage.objects.create(
            page_url=im_data.link,
            url=url,
            cached_url=cached_url,
            instagram_id=im_data.id,
            meta=json.dumps(meta),
            user=user,
            remote_timestamp=im_data.created_time.replace(tzinfo=pytz.utc),
            like_count=im_data.like_count,
            comment_count=im_data.comment_count,
        )

        tag_image(im, im_data)

        print('Done')
        return im
    except IntegrityError:
        pass
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        print(traceback.format_exc())
        raise

def tag_image(im, im_data):
    print('Creating DB instagram tags')
    # we need all of the tags for reporting
    if not hasattr(im_data,'tags'):
        return
    for tag_data in im_data.tags:
        try:
            print('Creating DB instagram tag {}'.format(tag_data.name))
            im.tags.add(InstagramTag.objects.get_or_create(name=tag_data.name)[0])
        except:
            pass

def update_instagram_tag(tag, max_tag_id=None, limit=None):
    if not max_tag_id:
        try:
            # attempt to get the max tag id
            it = InstagramTag.objects.get(name=tag)
            max_tag_id = it.max_tag_id
        except:
            pass

    print('Updating {tag}'.format(tag=tag))
    for im_data in _iterate_tag(tag, max_tag_id):
        try:
            _add_instagram_image([tag], im_data)
            pass
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

def scrape_instagram_tag(tag, count=200):
    print('Scraping {tag} for {count} images'.format(tag=tag, count=count))
    for im_data in _scrape_tag(tag, count):
        try:
            _add_instagram_image([tag], im_data)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

def instagram_url_to_instagram_id(url):
    query_url = "http://api.instagram.com/oembed?url={}".format(url)
    data = requests.get(query_url).json()
    id = data['media_id']
    return id

def iconosquare_url_to_instagram_id(url):
    id = iconosquare_url_to_instagram_id.re.match(url).group('id')
    return id
"http://iconosquare.com/p/947328653831618359_1692452990"
iconosquare_url_to_instagram_id.re = re.compile(r"http://iconosquare.com/p/(?P<id>[\d_]+)")

def url_to_instagram_id(url):
    try: return instagram_url_to_instagram_id(url)
    except: pass
    try: return iconosquare_url_to_instagram_id(url)
    except: pass
    raise ValueError('Unrecognised URL')

def add_instagram_image(tags, id=None, url=None):
    if url:
        id = url_to_instagram_id(url)

    data = api.media(id)
    return _add_instagram_image(tags, data)

def get_report(tags, period):
    if True:
        with open('fdsa.pickle') as fp:
            state = pickle.load(fp)
    else:
        state = {
            'posters': set(),
            'followers': set(),
            'follower_counts': {},

            'commenters': set(),
            'likers': set(),
            'comment_count': 0,
            'like_count': 0,

            'last_processed': 0,

            'deleted_count': 0,
            'img_inaccessible_count': 0,
            'followers_inaccessible_count': 0,

            'like_distribution':{},
            'comment_distribution':{},

            'most_commented':[],
            'most_liked':[],
        }

    images = InstagramImage.objects\
        .filter(tags__name__in=tags)\
        .filter(created__gte=period[0])\
        .filter(created__lte=period[1])\
        .filter(id__gt=state['last_processed'])\
        .order_by('id')

    def serialise(state):
        with open('fdsa.pickle','w') as fp:
            pickle.dump(state, fp)

    def process_image(image, state):
        try:
            data = wrap_api(api.media, (image.instagram_id,))
        except InstagramAPIError as e:
            msg = getattr(e, 'error_message', None)
            if msg == 'invalid media id':
                state['deleted_count'] += 1
                return
            elif msg == 'you cannot view this resource':
                state['img_inaccessible_count'] += 1
                return
            else:
                raise
        except:
            print(image.instagram_id)
            raise

        # TODO instagram API only returns subset of likes/comments?

        #print(data.comments)
        #for comment in data.comments:
        #    date = comment.created_at.replace(tzinfo=pytz.utc)
        #    if date >= period[0] and date <= period[1]:
        #        state['comment_count'] += 1
        #        state['commenters'].add(comment.user.id)

        #count = len(data.comments)
        #if count not in state['comment_distribution']:
        #    state['comment_distribution'][count] = 0
        #state['comment_distribution'][count] += 1

        #print(data.likes)
        #for like in data.likes:
        #    #likes dont have dates on them
        #    state['like_count'] += 1
        #    state['likers'].add(like.id)

        #count = len(data.likes)
        #if count not in state['like_distribution']:
        #    state['like_distribution'][count] = 0
        #state['like_distribution'][count] += 1

        state['comment_count'] += data.comment_count
        state['like_count'] += data.like_count

        state['most_commented'].append({
            'url':image.page_url,
            'count':data.comment_count,
        })
        state['most_liked'].append({
            'url':image.page_url,
            'count':data.like_count,
        })
        state['most_commented'].sort(key=lambda x:x['count'], reverse=True)
        state['most_liked'].sort(key=lambda x:x['count'], reverse=True)
        state['most_commented'] = state['most_commented'][0:10]
        state['most_liked'] = state['most_liked'][0:10]

        if image.user.username not in state['posters']:
            state['posters'].add(image.user.username)
            #try:
            #    state['follower_counts'][image.user.username] =\
            #        count_followers2(image.user.username)
            #except InstagramAPIError as e:
            #    pass

        state['last_processed'] = image.id

    processed = 0
    #for image in images:
    #    process_image(image, state)
    #    serialise(state)

    #    processed += 1
    #    if processed % 100 == 0:
    #        sys.stdout.write(str(processed))
    #    else:
    #        sys.stdout.write('.')
    #    sys.stdout.flush()

    print('images',images.count())
    print('commenters',len(state['commenters']))
    print('comments',state['comment_count'])
    print('likers',len(state['likers']))
    print('likes',state['like_count'])
    print('followers',len(state['followers']))
    print('posters',len(state['posters']))

    print('most commented')
    print('\n'.join([str(x) for x in state['most_commented']]))
    print('most liked')
    print('\n'.join([str(x) for x in state['most_liked']]))

    #print('\n'.join([str(x) for x in state['comment_distribution'].items()]))
    #print('\n'.join([str(x) for x in state['like_distribution'].items()]))
    if len(state['follower_counts']):
        print(
            'average followers per poster',
            sum(state['follower_counts'].values())/len(state['follower_counts'])
        )
        print(
            'max followers',
            max(state['follower_counts'].values())
        )
        followers = state['follower_counts'].items()
        followers.sort(key=lambda x: x[1], reverse=True)
        for follower_id, count in followers[:10]:
            print(follower_id)
            continue
            user_data = wrap_api(api.user, (follower_id,))
            #print(user_data.


def count_followers(user, cursor=None, page_limit=None):
    print('count followers {}'.format(user.username))
    print('got cursor {}'.format(cursor))
    user_id = get_id_from_username(user.username)
    pages_parsed = 0
    ret = set()
    while True:
        try:
            if cursor:
                followers, next_page_url = wrap_api(
                    api.user_followed_by,
                    (user_id,),
                    {'cursor':cursor},
                )
            else:
                followers, next_page_url = wrap_api(
                    api.user_followed_by,
                    (user_id,),
                )
        except InstagramAPIError as e:
            if e.error_message in (
                    'you cannot view this resource',):
                break
            else:
                print(traceback.format_exc())
                break
        # storing followers in db is too slow
        # for follower_data in followers:
        #     follower, _ = User.objects.get_or_create(
        #         username=follower_data.username,
        #     )
        #     follower.set_mug_url(follower_data.profile_picture)
        #     Follower.objects.create(
        #         follower=follower,
        #         followee=user,
        #     )
        [ret.add(f.id) for f in followers]
        if next_page_url:
            pages_parsed += 1
            parms = urlparse.parse_qs(urlparse.urlparse(next_page_url).query)
            new_cursor = parms.get('cursor')[0]
            if new_cursor == cursor:
                cursor = None
                break
            else:
                cursor = new_cursor
                if pages_parsed == page_limit:
                    break
        else:
            cursor = None
            break
    return cursor, ret

def wrap_api(f, args, kwargs={}):
    while True:
        try:
            data = f(*args, **kwargs)
            break
        except (ResponseNotReady, ServerNotFoundError):
            print('bad response')
            time.sleep(1)
        except InstagramAPIError as e:
            if e.error_message == 'Your client is making too many request per second':
                print('limited')
                time.sleep(60)
            else:
                raise
        except InstagramClientError as e:
            if e.error_message == 'Unable to parse response, not valid JSON.':
                print('json error')
                time.sleep(1)
            else:
                raise
    return data

def get_id_from_username(username):
    key = 'id_for_user_{}'.format(username)
    ret = cache.get(key)
    if not ret:
        try:
            for hit in wrap_api(api.user_search, (username,)):
                if hit.username == username:
                    ret = hit.id
                    cache.set(key, ret, 3600)
        except:
            pass
    return ret

def refresh_social(img):
    print('refreshing like/comment counts for {}'.format(img.page_url))
    try:
        data = wrap_api(api.media, (img.instagram_id,))
        InstagramImage.objects.filter(id=img.id).update(
            like_count=data.like_count,
            comment_count=data.comment_count,
            last_updated=now(),
        )
        tag_image(img, data)
    except InstagramAPIError as e:
        msg = getattr(e, 'error_message', None)
        if msg not in IGNORE_ERRORS:
            print(msg)
            #raise
        InstagramImage.objects.filter(id=img.id).update(
            last_updated=now(),
        )

followers_state = {}
def refresh_users():
    '''keep user follower sets up to date
    only process one page of one user at a time
    return True to indicate more work to be done'''

    cutoff = now() - datetime.timedelta(
        seconds=settings.REFRESH_INSTAGRAM_USER_FREQUENCY)

    morework = False
    for display in Display.objects.filter(active=True):
        users = User.objects\
            .filter(image__instagramimage__tags__in=display.get_split_tags())\
            .filter(last_updated__lt=cutoff)\
            .order_by('last_updated')\
            .distinct()

        if users.count():
            user = users[0]
            next_page_cursor, new_followers = count_followers(
                user, page_limit=10,
                cursor=followers_state.get(user.id)
            )
            key = 'display-followers-{}'.format(display.id)
            display_followers = cache.get(key)
            if display_followers is None:
                display_followers = unserialise_followers(display)
            display_followers = display_followers.union(new_followers)
            cache.set(key, display_followers, 86400) #one day
            if not next_page_cursor:
                print('no more pages')
                # no more pages

                # store numeric user count per user
                try:
                    user_id = get_id_from_username(user.username)
                    user_data = wrap_api(api.user, (user_id,))
                    user.follower_count = user_data.counts['followed_by']
                    print(user.follower_count)
                except:
                    print(traceback.format_exc())
                    pass

                user.last_updated = now()
                user.save(update_fields=('last_updated','follower_count'))
                # delete this user's cursor from state
                if user.id in followers_state:
                    del followers_state[user.id]
            else:
                print('next page is {}'.format(next_page_cursor))
                followers_state[user.id] = next_page_cursor
        serialise_followers(display)
        morework = morework or users.count() > 1
    return morework or len(followers_state)

def unserialise_followers(display):
    try:
        return set(DisplayFollowers.objects\
            .get(display=display).followers.split(','))
    except:
        return set()

def serialise_followers(display):
    control_key = 'serialised-followers-{}'.format(display.id)
    if not cache.get(control_key):
        print('serialising display followers to db')
        key = 'display-followers-{}'.format(display.id)
        followers = cache.get(key, set())

        db_item, created = DisplayFollowers.objects.get_or_create(display=display)
        db_item.followers = ','.join(followers)
        db_item.save()
            
        cache.set(control_key, True, 60*5) #serialise every 5 mins

def refresh_images():
    '''keep image like/comment counts up to date'''
    cutoff = now() - \
        datetime.timedelta(seconds=settings.REFRESH_INSTAGRAM_IMAGE_FREQUENCY)
    morework = False
    for display in Display.objects.filter(active=True):
        images = display.images()\
            .filter(last_updated__lte=cutoff)\
            .order_by('last_updated')
        if images.count():
            refresh_social(images[0])
        morework |= images.count() > 1
    return morework

def log_engagement():
    '''save a snapshot of like/comment counts for each display every 15
    minutes'''
    if not cache.get('logged_engagement_time'):
        for display in Display.objects.filter(active=True):
            display.log_stats()
        cache.set('logged_engagement_time', True, settings.LOG_ENGAGEMENT_FREQUENCY)
