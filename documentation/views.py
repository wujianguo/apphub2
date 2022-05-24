from django.shortcuts import render
from django.views import View
from django.conf import settings

class SwaggerJsonView(View):
    template_name = 'swagger.json'
    def get(self, request):
        url = settings.EXTERNAL_API_URL + '/' + settings.API_URL_PREFIX
        return render(
            request,
            self.template_name,
            {'url': url},
            content_type='application/json')
