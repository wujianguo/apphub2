from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import (PasswordChangeSerializer,
                                      PasswordResetSerializer)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from user.forms import AppHubPasswordResetForm

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        try:
            return obj.avatar.url
        except:  # noqa: E722
            return ""

    class Meta:
        model = UserModel
        fields = ["username", "email", "first_name", "last_name", "avatar"]


class UserRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)

    def validate_email(self, email):
        ret = super().validate_email(email)
        if settings.ACCOUNT_EMAIL_DOMAIN:
            if not ret.endswith("@" + settings.ACCOUNT_EMAIL_DOMAIN):
                raise serializers.ValidationError(
                    _("E-mail address should end with")
                    + " @"
                    + settings.ACCOUNT_EMAIL_DOMAIN,
                )
        return ret

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        first_name = self.validated_data.get("first_name", "")
        last_name = self.validated_data.get("last_name", "")

        if first_name:
            data["first_name"] = first_name
        if last_name:
            data["last_name"] = last_name
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ["username", "first_name", "last_name"]


class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ["avatar"]


class UserPasswordChangeSerializer(PasswordChangeSerializer):
    def save(self):
        ret = super().save()
        if self.logout_on_password_change:
            try:
                self.user.auth_token.delete()
            except:  # noqa: E722
                pass
        return ret


class UserPasswordResetSerializer(PasswordResetSerializer):
    @property
    def password_reset_form_class(self):
        if "allauth" in settings.INSTALLED_APPS:
            return AppHubPasswordResetForm
        return super().password_reset_form_class


class UserPasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming a password reset attempt.
    """

    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)
    username = serializers.CharField()
    token = serializers.CharField()

    set_password_form_class = SetPasswordForm

    _errors = {}
    user = None
    set_password_form = None

    def custom_validation(self, attrs):
        pass

    def validate(self, attrs):
        if "allauth" in settings.INSTALLED_APPS:
            from allauth.account.forms import default_token_generator

            # from allauth.account.utils import url_str_to_user_pk as uid_decoder
        else:
            from django.contrib.auth.tokens import default_token_generator

            # from django.utils.http import urlsafe_base64_decode as uid_decoder

        # Decode the uidb64 (allauth use base36) to uid to get User object
        try:
            self.user = UserModel._default_manager.get(username=attrs["username"])
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            raise ValidationError({"username": ["Invalid value"]})

        if not default_token_generator.check_token(self.user, attrs["token"]):
            raise ValidationError({"token": ["Invalid value"]})

        self.custom_validation(attrs)
        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user,
            data=attrs,
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        return self.set_password_form.save()
