from dj_rest_auth.forms import AllAuthPasswordResetForm
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

if "allauth" in settings.INSTALLED_APPS:
    from allauth.account import app_settings
    from allauth.account.adapter import get_adapter
    from allauth.account.forms import default_token_generator
    from allauth.account.utils import user_username


class AppHubPasswordResetForm(AllAuthPasswordResetForm):
    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", default_token_generator)

        for user in self.users:

            temp_key = token_generator.make_token(user)

            # save it to the password reset model
            # password_reset = PasswordReset(user=user, temp_key=temp_key)
            # password_reset.save()

            # send the password reset email
            url = (
                settings.EXTERNAL_WEB_URL
                + "/users/"
                + user.username
                + "/password/reset/confirm/"
                + temp_key
            )

            context = {
                "current_site": current_site,
                "user": user,
                "password_reset_url": url,
                "request": request,
            }
            if (
                app_settings.AUTHENTICATION_METHOD
                != app_settings.AuthenticationMethod.EMAIL
            ):
                context["username"] = user_username(user)
            get_adapter(request).send_mail(
                "account/email/password_reset_key", email, context
            )
        return self.cleaned_data["email"]
