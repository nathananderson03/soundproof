from django.views.generic.base import View, TemplateResponseMixin

class MicrositeView(View, TemplateResponseMixin):
    template_name = 'microsite/pages/basic.html'

    def get(self, request, slug):
        return self.render_to_response({})

class SnippetView(View, TemplateResponseMixin):
    template_name = 'microsite/pages/snippet.html'

    def get(self, request, slug):
        return self.render_to_response({})
