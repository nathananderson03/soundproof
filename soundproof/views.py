# pylint: skip-file

from __future__ import absolute_import, print_function
import traceback
import json
import pytz
import random
from StringIO import StringIO
from collections import namedtuple

from django.db.models import Q, Sum, Min, Max, Count
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.timezone import get_current_timezone
from django.views.generic.base import View, TemplateResponseMixin
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test

from . import instagram
from .models import *

def is_superuser(user):
    return user.is_superuser

@csrf_exempt
def instagram_callback(request):
    if request.GET.get('hub.mode') == 'subscribe':
        if request.GET.get('hub.verify_token') == settings.INSTAGRAM_VERIFY_TOKEN:
            return HttpResponse(request.GET.get('hub.challenge'))
        return HttpResponse()
    if request.method == 'POST':
        data = json.loads(request.body)
        state = cache.get(settings.CACHE_KEY_INSTAGRAM_UPDATE,[])
        for obj in data:
            if obj['object'] != 'tag':
                continue
            tag = obj['object_id']
            print('Instagram callback for {}'.format(tag))
            # treat the list as an ordered set
            # remove any existing instance of the tag
            try: state.remove(tag)
            except: pass
            # add the tag
            state.append(tag)
        cache.set(settings.CACHE_KEY_INSTAGRAM_UPDATE, state, settings.CACHE_TIMEOUT)
    return HttpResponse()

def feed(request, slug):
    display = get_object_or_404(Display, slug=slug)
    return render_to_response('soundproof/pages/feed.html',
        {'display':display})

def moderate(display, images):
    if display.moderation == 'whitelist':
        images = images.filter(displayimage__approved=True,
            displayimage__display=display)
    elif display.moderation == 'blacklist':
        images = images.filter(
            Q(displayimage=None)|
            (
                Q(displayimage__approved=True)
                &Q(displayimage__display=display)
            )
        )
    return images

def warmup(request):
    display = Display.objects.get(id=request.GET.get('display_id'))
    tags = display.get_split_tags()
    images = Image.objects\
        .filter(Q(instagramimage__tags__name__in=tags)|Q(displayimage__display=display))\
        .order_by('-remote_timestamp')\
        .distinct()
    images = moderate(display, images)
    return render_to_response('soundproof/components/image.html',
        {'images':images[:int(request.GET.get('count'))]})

def update(request):
    '''serve images/directives to a feed

    restrict to images that are newer that gt_ts
    also send maintenance directives (ie reload the page)
    and moderation directives (replace image x with image y)'''

    cutoff = datetime.datetime.fromtimestamp(float(request.POST.get('gt_ts')))
    cutoff = pytz.UTC.localize(cutoff)
    display_id = request.POST.get('display_id')
    display = Display.objects.get(id=display_id)
    tags = display.get_split_tags()
    images = Image.objects.filter(Q(instagramimage__tags__name__in=tags)|Q(displayimage__display=display))
    if request.POST.get('image_ids'):
        images = images.exclude(id__in=request.POST.get('image_ids').split(","))

    if images.filter(remote_timestamp__gt=cutoff).count() == 0:
        images = images.order_by('?')  # grab some random images if there are no new ones
    else:
        images = images.filter(remote_timestamp__gt=cutoff).distinct().order_by('-remote_timestamp')

    images = moderate(display, images)

    images = set(images[0:int(request.POST.get('count'))])

    if request.POST.get('format','html') == 'json':
        resp = {
            'images':[img.as_dict() for img in images],
            'moderated':get_moderated(display),
            'directives':get_directives(request),
        }
        return HttpResponse(json.dumps(resp))
    else:
        return render_to_response('soundproof/components/image.html',
            {'images':images})

def get_moderated(display):
    '''return recently moderated images for this display and a substitution'''

    cutoff = now() - datetime.timedelta(hours=1)
    moderated = DisplayImage.objects\
        .filter(
            display=display,
            approved=False,
            timestamp__gte=cutoff
        )
    return [{
        'id':di.image.id,
        'sub':get_sub(display).as_dict(),
    } for di in moderated]

def get_sub(display):
    '''pick random substitution image for this display
    take from 50 most recent non-rejected images'''
    tags = display.get_split_tags()
    images = Image.objects.order_by('-remote_timestamp')
    images = images.filter(instagramimage__tags__name__in=tags)
    images = moderate(display, images)
    return random.choice(list(images[:50]))

def json_images(request):
    '''serve images to microsite as JSON

    restrict to images older than lt_ts'''

    lt_ts = request.GET.get('lt_ts')
    if lt_ts:
        cutoff = datetime.datetime.fromtimestamp(float(lt_ts))
        cutoff = pytz.UTC.localize(cutoff)
    else:
        cutoff = now()

    images = Image.objects.all()
    images = images.filter(remote_timestamp__lt=cutoff)
    display = Display.objects.get(slug=request.GET.get('display_slug'))
    tags = display.tags.split(',')
    images = images.filter(instagramimage__tags__name__in=tags)

    if request.GET.get('moderation') == 'whitelist':
        images = images.filter(displayimage__approved=True,
            displayimage__display=display)
    elif request.GET.get('moderation') == 'blacklist':
        images = images.filter(Q(displayimage=None)|(Q(displayimage__approved=True)&Q(displayimage__display=display)))

    images = images.order_by('-remote_timestamp')[0:request.GET.get('count')]

    resp = HttpResponse(json.dumps([img.as_dict() for img in images]))
    resp['Access-Control-Allow-Origin'] = '*'
    return resp

class SubscriptionsView(View, TemplateResponseMixin):
    template_name = 'soundproof/pages/subs.html'

    @method_decorator(user_passes_test(is_superuser))
    def dispatch(self, *args, **kwargs):
        return super(SubscriptionsView, self).dispatch(*args, **kwargs)    

    def get(self, request):
        return self.render_to_response({
            'subs':instagram.subscriptions(),
        })

    def post(self, request):
        # this functionality is superseded by the Display save logic
        # it is left in for manual over-ride
        # use at own risk
        tag_name = request.POST.get('tag_name')
        if tag_name:
            instagram.add_subscription(tag_name)

        delete = request.POST.get('delete')
        if delete:
            instagram.remove_subscription(int(delete))
            
        return HttpResponseRedirect(reverse('subs'))

class ModerateView(View, TemplateResponseMixin):
    template_name = 'soundproof/pages/moderate.html'
    limit = 100 

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ModerateView, self).dispatch(*args, **kwargs)    

    def get(self, request, slug):
        display = get_object_or_404(Display, slug=slug)
        if not display.auth_user(request.user):
            raise Http404
        tags = display.get_split_tags()

        # get the N latest images
        images = Image.objects\
            .filter(instagramimage__tags__name__in=tags)\
            .distinct()\
            .order_by('-remote_timestamp')[:self.limit]

        return self.render_to_response({
            'display':display,
            'images':images,
        })

    def post(self, request, slug):
        display = get_object_or_404(Display, slug=slug)
        if not display.auth_user(request.user):
            raise Http404
        image = get_object_or_404(Image, id=request.POST.get('img_id'))
        di = DisplayImage.objects.get_or_create(display=display, image=image)[0]
        if request.POST.get('approved') == 'true':
            di.approved = True
        else:
            di.approved = False
        di.save()
        return HttpResponse('')

class PhotoSelectView(View, TemplateResponseMixin):
    template_name = 'soundproof/pages/print.html'
    limit = 30

    def get(self, request, slug):
        if not settings.PRINTER_ENABLED:
            raise Http404

        if request.GET.get('action') == 'preview':
            image_id = int(request.GET.get('photo'))
            frame_id = int(request.GET.get('frame'))

            frame = PhotoFrame.objects.get(id=frame_id)
            image = Image.objects.get(id=image_id)

            photo = frame.frame_image(image)
            buf = StringIO()
            photo.save(buf, format='JPEG', quality=85)
            resp = HttpResponse(buf.getvalue())
            resp['Content-Type'] = 'image/jpeg'
            return resp
        elif request.GET.get('action') == 'images':
            display = get_object_or_404(Display, slug=slug)
            tags = display.get_split_tags()

            images = Image.objects\
                .filter(instagramimage__tags__name__in=tags)\
                .order_by('-remote_timestamp')[:self.limit]
            return render_to_response('soundproof/components/printer-photos.html', {'images':images})
        else:
            display = get_object_or_404(Display, slug=slug)
            tags = display.get_split_tags()

            images = Image.objects\
                .filter(instagramimage__tags__name__in=tags)\
                .order_by('-remote_timestamp')[:self.limit]

            frames = PhotoFrame.objects.all()

            return self.render_to_response({
                'display':display,
                'images':images,
                'frames':frames,
                'override_tools': 'Insta Printer',
            })

    def post(self, request, slug):
        if not settings.PRINTER_ENABLED:

            raise Http404

        try:
            image_id = int(request.POST.get('photo'))
            frame_id = int(request.POST.get('frame'))

            frame = PhotoFrame.objects.get(id=frame_id)
            image = Image.objects.get(id=image_id)

            photo = frame.frame_image(image)

            # print the photo
            #photo.save('test_photo.png')
            util.print_image(photo)

            # store details of the printed image
            PrintedPhoto(image=image, frame=frame).save()
        except Exception:
            print(traceback.format_exc())
            raise

        return HttpResponse()

def get_directives(request):
    status = cache.get('browser-status',{})
    ip = request.META.get('REMOTE_ADDR')
    ret = {}
    if ip:
        browser = status.get(ip,{})
        browser['ip'] = ip
        browser['last seen'] = now()
        browser['gt_ts'] = request.GET.get('gt_ts')
        if 'directives' in browser:
            ret = browser['directives']
            del browser['directives']
        status[ip] = browser
    cache.set('browser-status', status, 86400)
    return ret

@csrf_exempt
def status(request):
    if request.method == 'POST':
        ip = request.POST.get('ip')
        status = cache.get('browser-status',{})
        browser = status.get(ip,{})
        if request.POST.get('action') == 'reload':
            browser['directives'] = {'reload':True}
        if request.POST.get('action') == 'rename':
            browser['name'] = request.POST.get('name')
        status[ip] = browser
        cache.set('browser-status', status)
    if not request.user.is_superuser:
        return HttpResponse('')

    status = cache.get('browser-status',{})
    for data in status.values():
	if 'last seen' in data:
            data['delta'] = now() - data['last seen']
    return render_to_response('soundproof/pages/status.html', {
        'status': status,
    })

class AnalyticsView(View, TemplateResponseMixin):
    template_name = 'soundproof/pages/analytics.html'

    def get(self, request, slug):
        display = get_object_or_404(Display, slug=slug)
        if not (display.public_analytics or display.auth_user(request.user)):
            raise Http404
        tags = display.get_split_tags()
        images = InstagramImage.objects\
            .filter(tags__name__in=tags)

        data = {
            'masthead_title': 'Insights Report',
        }
        if request.GET.get('date_from'):
            d = datetime.datetime.strptime(request.GET.get('date_from'), '%Y-%m-%d')
            d = get_current_timezone().localize(d)
            d = d.replace(hour=0, minute=0, second=0)
            images = images.filter(remote_timestamp__gte=d)
            data['date_from'] = d

        if request.GET.get('date_to'):
            d = datetime.datetime.strptime(request.GET.get('date_to'), '%Y-%m-%d')
            d = get_current_timezone().localize(d)
            d = d.replace(hour=23, minute=59, second=59)
            images = images.filter(remote_timestamp__lte=d)
            data['date_to'] = d

        dates = images.aggregate(
            date_from=Min('remote_timestamp'),
            date_to=Max('remote_timestamp'),
        )
        if 'date_from' not in data:
            data['date_from'] = dates['date_from']
        if 'date_to' not in data:
            data['date_to'] = dates['date_to']

        points = DisplayEngagementLog.objects\
            .filter(display=display)\
            .filter(timestamp__gte=data['date_from'])\
            .filter(timestamp__lte=data['date_to'])\
            .order_by('timestamp')

        data['graph_json'] = json.dumps([{
            'unixtime': time.mktime(point.timestamp.timetuple()),
            'timestamp': point.timestamp.strftime('%Y-%m-%d %H:%M'),
            'interval': {
                'likes': point.interval_like_count,
                'comments': point.interval_comment_count,
                'images': point.interval_image_count,
            },
            'total': {
                'likes': point.total_like_count,
                'comments': point.total_comment_count,
                'images': point.total_image_count,
            },
        } for point in points])

        data['tags'] = [{
            'label': '#{}'.format(tag.name),
            'value': 100*float(tag.name__count)/images.count(),
        } for tag in InstagramTag.objects\
            .filter(instagramimage__in=images)\
            .annotate(Count('name'))\
            .order_by('-name__count')[0:12]]
        data['tags_json'] = json.dumps(data['tags'])

        #dummy = []
        #start = now()
        #total = 0
        #for n in range(10):
        #    t = start + n * datetime.timedelta(minutes=15)
        #    c = int(random.uniform(5,50))
        #    total += c
        #    dummy.append({
        #        'unixtime': time.mktime(t.timetuple()),
        #        'timestamp': t.strftime('%y-%m-%d %H:%M'),
        #        'interval': {
        #            'images': c,
        #        },
        #        'total': {
        #            'images': total,
        #        },
        #    })
        #data['graph_json'] = json.dumps(dummy)

        tz = get_current_timezone()
        data['date_from'] = data['date_from'].astimezone(get_current_timezone())
        data['date_to'] = data['date_to'].astimezone(get_current_timezone())

        try:
            data['follower_count'] = len(DisplayFollowers.objects\
                .get(display=display).followers.split(','))
        except:
            data['follower_count'] = 0

        data['user_by_post_count'] = User.objects\
            .filter(image__in=images)\
            .annotate(image_count=Count('image'))\
            .order_by('-image_count')\
            .distinct()

        data['user_by_follower_count'] = User.objects\
            .filter(image__in=images)\
            .order_by('-follower_count')\
            .distinct()

        data['images_by_engagement'] = images\
            .extra(select={'points':'like_count+5*comment_count'})\
            .order_by('-points')\
            .distinct()

        data['images_by_likes'] = images.order_by('-like_count').distinct()
        data['images_by_comments'] = images.order_by('-comment_count').distinct()

        data['social_impressions'] = sum([image.user.follower_count
            for image in images])

        stale_cutoff = now() - \
            datetime.timedelta(seconds=settings.REFRESH_INSTAGRAM_USER_FREQUENCY)
        data.update({
            'display': display,
            'image_count': images.count(),
            'comment_count': images.distinct()\
                .aggregate(Sum('comment_count'))['comment_count__sum'],
            'like_count': images.distinct()\
                .aggregate(Sum('like_count'))['like_count__sum'],
            'poster_count': User.objects.filter(image__in=images)\
                .order_by().distinct().count(),
            'stale': User.objects\
                .filter(image__in=images)\
                .filter(last_updated__lt=stale_cutoff)\
                .count()
        })
        return self.render_to_response(data)

class GridConfigView(View, TemplateResponseMixin):
    template_name = 'soundproof/pages/grid.html'

    def get(self, request, slug):
        display = get_object_or_404(Display, slug=slug)
        if not display.auth_user(request.user):
            raise Http404
        OptStruct = namedtuple('OptStruct', 'app_label model_name')
        return self.render_to_response({
            'display': display,
            'opts': OptStruct(
                app_label='soundproof',
                model_name='display',
            ),
            'range':range(5000),
        })

    def post(self, request, slug):
        display = get_object_or_404(Display, slug=slug)
        if not display.auth_user(request.user):
            raise Http404
        try:
            hcount = int(request.POST.get('tile_hcount'))
            Display.objects.filter(id=display.id).update(
                tile_width='{}vw'.format(100.0/hcount)
            )
        except:
            raise
        return HttpResponseRedirect(reverse('admin:soundproof_display_change',
            args=(display.id,)))
