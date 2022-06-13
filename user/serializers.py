from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers

UserModel = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        return obj.avatar.url

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'first_name', 'last_name', 'avatar', 'email_verified']


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}}

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['username', 'email', 'first_name', 'last_name']

class UserAvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['avatar']

class UserLoginSerializer(serializers.Serializer):
    account = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        fields = ['account', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        account = attrs.get('account', '')
        if account.find('@') != -1:
            username = ''
            email = account
        else:
            username = account
            email = ''
        password = attrs.get('password')
        user = authenticate(username=username, password=password, email=email)
        if user is None:
            raise serializers.ValidationError({'message': 'A user with this username/email and password is not found.'})
        return {
            'user': user
        }

class VerifyEmailSerializer(serializers.Serializer):
    code = serializers.UUIDField()

class RequestResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    code = serializers.UUIDField()
    password = serializers.CharField()

class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    new_password = serializers.CharField()
