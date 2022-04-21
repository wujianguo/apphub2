import datetime
from django.http import Http404
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.files import File
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from user.models import EmailCode
from user.serializers import *
from util.reserved import reserved_names
from util.image import generate_icon_image
from util.url import build_absolute_uri
from util.storage import internal_file_response

UserModel = get_user_model()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    username = serializer.validated_data.get('username')
    if username in reserved_names:
        return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    password = serializer.validated_data.get('password')
    email = serializer.validated_data.get('email', '')
    first_name = serializer.validated_data.get('first_name', '')
    last_name = serializer.validated_data.get('last_name', '')
    if email and UserModel.objects.filter(email=email, email_verified=True).exists():
        return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
    user = UserModel.objects.create_user(username=username)
    if email:
        user.email = email
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.set_password(password)
    user.save()
    file = generate_icon_image(first_name if first_name else username)
    user.avatar.save('avatar.png', File(file.file))
    token, _ = Token.objects.get_or_create(user=user)
    response_serializer = UserSerializer(user)
    response_data = response_serializer.data
    response_data['token'] = token.key
    return Response(response_data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.validated_data['user']
    token, _ = Token.objects.get_or_create(user=user)
    response_serializer = UserSerializer(user)
    response_data = response_serializer.data
    response_data['token'] = token.key
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_verify_email(request):
    if not request.user.email:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    email_code = EmailCode.objects.create(email=request.user.email, type=EmailCode.EmailCodeType.VerifyEmail)
    message = str(email_code.code)
    send_mail('verify your email', message, None, [request.user.email])
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_email(request):
    serializer = VerifyEmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        email_code = EmailCode.objects.get(
            email=request.user.email,
            code=serializer.validated_data['code'],
            type=EmailCode.EmailCodeType.VerifyEmail,
            valid=True)
    except EmailCode.DoesNotExist:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    expire_time = email_code.create_time + datetime.timedelta(seconds=settings.CODE_EXPIRE_SECONDS)
    if timezone.now() > expire_time:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    request.user.email_verified = True
    request.user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def request_reset_password(request):
    serializer = RequestResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data['email']
    try:
        UserModel.objects.get(email=email, email_verified=True)
    except UserModel.DoesNotExist:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email_code = EmailCode.objects.create(email=email, type=EmailCode.EmailCodeType.ResetPassword)
    message = str(email_code.code)
    send_mail('reset password', message, None, [email])
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    try:
        email_code = EmailCode.objects.get(
            code=serializer.validated_data['code'], 
            type=EmailCode.EmailCodeType.ResetPassword,
            valid=True)
    except EmailCode.DoesNotExist:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    expire_time = email_code.create_time + datetime.timedelta(seconds=settings.CODE_EXPIRE_SECONDS)
    if timezone.now() > expire_time:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = email_code.email
    try:
        user = UserModel.objects.get(email=email, email_verified=True)
    except UserModel.DoesNotExist:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user.auth_token.delete()
    user.set_password(serializer.validated_data['password'])
    user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(username=request.user.username, password=serializer.validated_data['password'])
    if not user:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    request.user.auth_token.delete()
    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


class MeUser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data.get('email'):
            instance = serializer.save(email_verified=False)
        else:
            instance = serializer.save()
        response_serializer = UserSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class UserAvatar(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UserAvatarSerializer(request.user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        request.user.avatar.delete()
        instance = serializer.save()
        # todo response no content
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response['Location'] = build_absolute_uri(instance.avatar.url)
        return response

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_info(request, username):
    try:
        user = UserModel.objects.get(username=username)
    except UserModel.DoesNotExist:
        raise Http404
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def user_avatar(request, username, name):
    try:
        user = UserModel.objects.get(username=username)
    except UserModel.DoesNotExist:
        raise Http404
    return internal_file_response(user.avatar, name)
