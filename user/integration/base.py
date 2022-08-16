from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import status
from rest_framework.response import Response

from user.serializers import UserSerializer


class BaseSocialLoginView(SocialLoginView):
    def get_response(self):
        if self.token:
            response_serializer = UserSerializer(self.user)
            response_data = response_serializer.data
            response_data["token"] = self.token.key
            return Response(response_data, status=status.HTTP_200_OK)
        return super().get_response()

    def register_provider(self):
        pass

    def authorize_extra_params(self):
        return {}

    def get(self, request):
        self.register_provider()
        adapter = self.adapter_class(request)
        app = adapter.get_provider().get_app(request)
        provider = adapter.get_provider()
        scope = provider.get_scope(request)

        client = self.client_class(
            request,
            app.client_id,
            app.secret,
            adapter.access_token_method,
            adapter.access_token_url,
            self.callback_url,
            scope,
            scope_delimiter=adapter.scope_delimiter,
            headers=adapter.headers,
            basic_auth=adapter.basic_auth,
        )
        data = {
            "url": client.get_redirect_url(
                adapter.authorize_url, self.authorize_extra_params()
            )
        }
        return Response(data)

    def post(self, request, *args, **kwargs):
        self.register_provider()
        response = super().post(request, *args, **kwargs)
        try:
            from django.http import HttpRequest

            if not isinstance(request, HttpRequest):
                request = request._request
            response.data["new_user"] = request.new_user
        except:  # noqa: E722
            response.data["new_user"] = False

        return response
