from django.conf.urls import patterns, url

from .views import (
    MicrositeView,
    SnippetView,
)

urlpatterns = patterns(
    '',
    url('site/(.+)$', MicrositeView.as_view(), name='microsite_basic'),
    url('snippet/(.+)$', SnippetView.as_view(), name='microsite_snippet'),
)
