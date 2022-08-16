from django.conf import settings
from django.shortcuts import render
from django.views import View


class SwaggerJsonView(View):
    template_name = "swagger.json"

    def get(self, request):
        url = settings.EXTERNAL_API_URL
        return render(
            request, self.template_name, {"url": url}, content_type="application/json"
        )
