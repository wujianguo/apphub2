from django.contrib.auth.models import User
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from user.serializers import *
from util.reserved import reserved_names


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
    email = serializer.validated_data.get('email')
    first_name = serializer.validated_data.get('first_name', '')
    last_name = serializer.validated_data.get('last_name', '')
    user = User.objects.create_user(username=username, email=email)
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.set_password(password)
    user.save()
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

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)
