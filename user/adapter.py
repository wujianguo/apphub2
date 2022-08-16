from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpResponseRedirect


class AppHubAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        return (
            settings.EXTERNAL_WEB_URL
            + "/user/register/verify_email/"
            + emailconfirmation.key
        )

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_web_url": settings.EXTERNAL_WEB_URL,
            "key": emailconfirmation.key,
        }
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)

    def respond_email_verification_sent(self, request, user):
        return HttpResponseRedirect(settings.EXTERNAL_WEB_URL)

    def get_signup_redirect_url(self, request):
        return settings.EXTERNAL_WEB_URL


class AppHubSoialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        request.new_user = not sociallogin.is_existing
        return super().pre_social_login(request, sociallogin)

    def is_auto_signup_allowed(self, request, sociallogin):
        ret = super().is_auto_signup_allowed(request, sociallogin)
        if not ret:
            sociallogin.user.email = ""
            sociallogin.email_addresses = []
        return True
