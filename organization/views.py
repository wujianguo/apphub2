from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from organization.models import OrganizationUser, Organization
from organization.serializers import *
from application.models import UniversalApp
from util.visibility import VisibilityType
from util.choice import ChoiceField
from util.reserved import reserved_names
from util.pagination import get_pagination_params

def viewer_query(user, path):
    if user.is_authenticated:
        allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
        q1 = Q(org__path=path)
        q2 = Q(org__visibility__in=allow_visibility)
        q3 = Q(user=user)
        return (q2 | q3) & q1
    else:
        q1 = Q(org__path=path)
        q2 = Q(org__visibility=VisibilityType.Public)
        return q1 & q2

def check_org_view_permission(path, user):
    org_user = OrganizationUser.objects.filter(viewer_query(user, path))
    if not org_user.exists():
        raise Http404
    return org_user.first()

def check_org_admin_permission(path, user):
    try:
        admin_role = OrganizationUser.OrganizationUserRole.Admin
        user_org = OrganizationUser.objects.get(org__path=path, user=user)
        if user_org.role != admin_role:
            raise PermissionDenied
        return user_org
    except OrganizationUser.DoesNotExist:
        try:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            Organization.objects.get(path=path, visibility__in=allow_visibility)
            raise PermissionDenied
        except Organization.DoesNotExist:
            raise Http404

class OrganizationList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # todo: order, filter, search
        # filter: username, role
        # example
        # - current user's orgs: username is my name and role is not null
        # - some user's orgs: username is user's name and role is not null
        page, per_page = get_pagination_params(request)

        if request.user.is_authenticated:
            # todo
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            orgs = Organization.objects.filter(visibility__in=allow_visibility)
            user_orgs = OrganizationUser.objects.filter(user=request.user).prefetch_related('org')
            def not_in_user_orgs(org):
                return len(list(filter(lambda x: x.org.id==org.id, user_orgs))) == 0
            orgs = filter(not_in_user_orgs, orgs)
            data = OrganizationSerializer(orgs, many=True).data
            user_orgs_data = UserOrganizationSerializer(user_orgs, many=True).data
            data.extend(user_orgs_data)
            return Response(data[(page - 1) * per_page: page * per_page])
        else:
            orgs = Organization.objects.filter(visibility=VisibilityType.Public).order_by('path')[(page - 1) * per_page: page * per_page]
            serializer = OrganizationSerializer(orgs, many=True)
            return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        path = serializer.validated_data['path']
        if path in reserved_names:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        if Organization.objects.filter(path=path).exists():
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

        instance = serializer.save()
        org_user = OrganizationUser.objects.create(org=instance, user=request.user, role=OrganizationUser.OrganizationUserRole.Admin)
        data = serializer.data
        data['role'] = ChoiceField(choices=OrganizationUser.OrganizationUserRole.choices).to_representation(org_user.role)
        response = Response(data, status=status.HTTP_201_CREATED)
        location = reverse('org-detail', args=(path,))
        response['Location'] = request.build_absolute_uri(location)
        return response

class OrganizationDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, path):
        if request.user.is_authenticated:
            try:
                user_org = OrganizationUser.objects.get(org__path=path, user=request.user)
                serializer = UserOrganizationSerializer(user_org)
                return Response(serializer.data)
            except OrganizationUser.DoesNotExist:
                pass
        try:
            if request.user.is_authenticated:
                allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            else:
                allow_visibility = [VisibilityType.Public]
            org = Organization.objects.get(path=path, visibility__in=allow_visibility)
            serializer = OrganizationSerializer(org)
            return Response(serializer.data)
        except Organization.DoesNotExist:
            raise Http404

    def put(self, request, path):
        user_org = check_org_admin_permission(path, request.user)
        serializer = OrganizationSerializer(user_org.org, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.validated_data.get('path', None) and path != serializer.validated_data['path']:
            if serializer.validated_data['path'] in reserved_names:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            if Organization.objects.filter(path=serializer.validated_data['path']).exists():
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

        serializer.save()
        data = serializer.data
        data['role'] = ChoiceField(choices=OrganizationUser.OrganizationUserRole.choices).to_representation(user_org.role)
        return Response(data)

    def delete(self, request, path):
        user_org = check_org_admin_permission(path, request.user)
        if UniversalApp.objects.filter(org=user_org.org).exists():
            raise PermissionDenied
        user_org.org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationIcon(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, path):
        user_org = check_org_view_permission(path, request.user)
        if not user_org.org.icon_file:
            raise Http404
        response = Response()
        response['X-Accel-Redirect'] = user_org.org.icon_file.url
        return response

    def post(self, request, path):
        user_org = check_org_admin_permission(path, request.user)
        serializer = OrganizationIconSerializer(user_org.org, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        location = reverse('org-icon', args=(path,))
        data = {
            'icon_file': request.build_absolute_uri(location)
        }
        # todo response no content
        response = Response(data)
        response['Location'] = request.build_absolute_uri(location)
        return response

    def delete(self, request, path):
        user_org = check_org_admin_permission(path, request.user)
        storage = user_org.org.icon_file.storage
        icon_file = user_org.org.icon_file
        user_org.org.icon_file = None
        user_org.org.save()
        storage.delete(icon_file.name)
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationUserList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, path):
        check_org_view_permission(path, request.user)
        users = OrganizationUser.objects.filter(org__path=path)
        serializer = OrganizationUserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, path):
        user_org = check_org_admin_permission(path, request.user)
        serializer = OrganizationUserAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username']
        role = serializer.validated_data['role']
        try:
            OrganizationUser.objects.get(org__path=path, user__username=username)
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        except OrganizationUser.DoesNotExist:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            instance = OrganizationUser.objects.create(org=user_org.org, role=role, user=user)
            serializer = OrganizationUserSerializer(instance)
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            location = reverse('org-user', args=(path, username))
            response['Location'] = request.build_absolute_uri(location)
            return response

class OrganizationUserDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_object(self, path, username):
        try:
            return OrganizationUser.objects.get(org__path=path, user__username=username)
        except OrganizationUser.DoesNotExist:
            raise Http404

    def get(self, request, path, username):
        # todo
        check_org_view_permission(path, request.user)
        org_user = self.get_object(path, username)
        serializer = OrganizationUserSerializer(org_user)
        return Response(serializer.data)

    def put(self, request, path, username):
        admin_role = OrganizationUser.OrganizationUserRole.Admin
        check_org_admin_permission(path, request.user)
        org_user = self.get_object(path, username)
        serializer = OrganizationUserSerializer(org_user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if request.user.username == username:
            if serializer.validated_data.get('role', admin_role) != admin_role:
                exists = OrganizationUser.objects.filter(org__path=path, role=admin_role).exclude(user=request.user).exists()
                if not exists:
                    raise PermissionDenied
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, path, username):
        admin_role = OrganizationUser.OrganizationUserRole.Admin
        check_org_admin_permission(path, request.user)
        org_user = self.get_object(path, username)

        if request.user.username == username:
            exists = OrganizationUser.objects.filter(org__path=path, role=admin_role).exclude(user=request.user).exists()
            if not exists:
                raise PermissionDenied

        org_user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
