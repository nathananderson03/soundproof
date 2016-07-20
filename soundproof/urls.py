from django.conf.urls import patterns, include, url
from django.contrib import admin

from .views import (
    SubscriptionsView,
    ModerateView,
    AnalyticsView,
    GridConfigView,
    PhotoSelectView,
)

urlpatterns = patterns(
    'soundproof.views',
    url(r'^instagram$', 'instagram_callback', name='instagram_callback'),
    url(r'^feed/(.+)$', 'feed', name='feed'),
    url(r'^moderate/(.+)$', ModerateView.as_view(), name='moderate'),
    url(r'^analytics/(.+)$', AnalyticsView.as_view(), name='analytics'),
    url(r'^grid/(.+)$', GridConfigView.as_view(), name='grid'),
    url(r'^update$', 'update', name='update'),
    url(r'^warmup$', 'warmup', name='warmup'),
    url(r'^subs$', SubscriptionsView.as_view(), name='subs'),
    url(r'^api/json-images$', 'json_images', name='json_images'),
    url(r'status', 'status'),

    url(r'^print/(?P<slug>[^/]+)$', PhotoSelectView.as_view(), name='photo_select'),

    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += patterns(
    '',
    url('r^microsite/', include('microsite.urls')),
)
