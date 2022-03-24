from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from application.models import UniversalApp, UniversalAppUser
from application.serializers import *
from organization.models import OrganizationUser, Organization
from util.visibility import VisibilityType
from util.choice import ChoiceField
from util.reserved import reserved_names
from util.pagination import get_pagination_params

def viewer_query(user, path, ownername):
    if user.is_authenticated:
        allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
        q1 = Q(app__path=path, app__owner__username=ownername)
        q2 = Q(app__visibility__in=allow_visibility)
        q3 = Q(user=user)
        return (q2 | q3) & q1
    else:
        q1 = Q(app__path=path, app__owner__username=ownername)
        q2 = Q(app__visibility=VisibilityType.Public)
        return q1 & q2

def check_app_view_permission(user, path, ownername):
    app_user = UniversalAppUser.objects.filter(viewer_query(user, path, ownername))
    if not app_user.exists():
        raise Http404
    return app_user.first()

def check_app_manager_permission(user, path, ownername):
    try:
        manager_role = UniversalAppUser.ApplicationUserRole.Manager
        user_app = UniversalAppUser.objects.get(app__path=path, app__owner__username=ownername, user=user)
        if user_app.role != manager_role:
            raise PermissionDenied
        return user_app
    except UniversalAppUser.DoesNotExist:
        try:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            UniversalApp.objects.get(path=path, owner__username=ownername, visibility__in=allow_visibility)
            raise PermissionDenied
        except UniversalApp.DoesNotExist:
            raise Http404

class UniversalAppList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        # todo: order, filter
        page, per_page = get_pagination_params(request)
        if request.user.is_authenticated:
            # todo
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            apps = UniversalApp.objects.filter(visibility__in=allow_visibility)

            user_apps = UniversalAppUser.objects.filter(user=request.user).prefetch_related('app')
            def not_in_user_apps(app):
                return len(list(filter(lambda x: x.app.id==app.id, user_apps))) == 0
            apps = filter(not_in_user_apps, apps)

            orgs = OrganizationUser.objects.filter(user=request.user).values('org')
            org_apps = UniversalApp.objects.filter(org__in=orgs, visibility=VisibilityType.Private)
            org_apps = filter(not_in_user_apps, org_apps)

            app_data = UniversalAppSerializer(apps, many=True).data
            org_app_data = UniversalAppSerializer(org_apps, many=True).data
            user_apps_data = UserUniversalAppSerializer(user_apps, many=True).data
            app_data.extend(org_app_data)
            app_data.extend(user_apps_data)
            return Response(app_data[(page - 1) * per_page: page * per_page])
        else:
            apps = UniversalApp.objects.filter(visibility=VisibilityType.Public).order_by('path')[(page - 1) * per_page: page * per_page]
            serializer = UniversalAppSerializer(apps, many=True)
            return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        serializer = UniversalAppCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        path = serializer.validated_data['path']
        slug = serializer.validated_data['install_slug']
        if path in reserved_names or slug in reserved_names:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        if UniversalApp.objects.filter(path=path, owner=request.user).exists() or UniversalApp.objects.filter(install_slug=slug).exists():
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        instance = serializer.save(owner=request.user)
        app_user = UniversalAppUser.objects.create(app=instance, user=request.user, role=UniversalAppUser.ApplicationUserRole.Manager)
        data = UniversalAppSerializer(instance).data
        data['role'] = ChoiceField(choices=UniversalAppUser.ApplicationUserRole.choices).to_representation(app_user.role)
        response = Response(data, status=status.HTTP_201_CREATED)
        location = reverse('app-detail', args=(path, request.user.username))
        response['Location'] = request.build_absolute_uri(location)
        return response


class UserUniversalAppList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username):
        # todo: order, filter
        page, per_page = get_pagination_params(request)

        if request.user.is_authenticated:
            # todo
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            apps = UniversalApp.objects.filter(visibility__in=allow_visibility, owner__username=username)
            user_apps = UniversalAppUser.objects.filter(user=request.user, app__owner__username=username).prefetch_related('app')
            def not_in_user_apps(app):
                return len(list(filter(lambda x: x.app.path==app.path, user_apps))) == 0
            apps = filter(not_in_user_apps, apps)
            data = UniversalAppSerializer(apps, many=True).data
            user_apps_data = UserUniversalAppSerializer(user_apps, many=True).data
            data.extend(user_apps_data)
            return Response(data[(page - 1) * per_page: page * per_page])
        else:
            apps = UniversalApp.objects.filter(visibility=VisibilityType.Public, owner__username=username).order_by('path')[(page - 1) * per_page: page * per_page]
            serializer = UniversalAppSerializer(apps, many=True)
            return Response(serializer.data)


class AuthenticatedUserApplicationList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return UserUniversalAppList().get(request, request.user.username)


class UserUniversalAppDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, username, path):
        if request.user.is_authenticated:
            try:
                user_app = UniversalAppUser.objects.get(app__path=path, app__owner__username=username, user=request.user)
                serializer = UserUniversalAppSerializer(user_app)
                return Response(serializer.data)
            except UniversalAppUser.DoesNotExist:
                pass
        try:
            if request.user.is_authenticated:
                allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            else:
                allow_visibility = [VisibilityType.Public]
            app = UniversalApp.objects.get(path=path, owner__username=username, visibility__in=allow_visibility)
            serializer = UniversalAppSerializer(app)
            return Response(serializer.data)
        except UniversalApp.DoesNotExist:
            raise Http404

def org_viewer_query(user, path):
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
    org_user = OrganizationUser.objects.filter(org_viewer_query(user, path))
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

class OrganizationUniversalAppList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def post(self, request, org_path):
        user_org = check_org_admin_permission(org_path, request.user)
        serializer = UniversalAppCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        path = serializer.validated_data['path']
        slug = serializer.validated_data['install_slug']
        if path in reserved_names or slug in reserved_names:
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        if UniversalApp.objects.filter(path=path, org=user_org.org).exists() or UniversalApp.objects.filter(install_slug=slug).exists():
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        instance = serializer.save(org=user_org.org)
        data = UniversalAppSerializer(instance).data
        response = Response(data, status=status.HTTP_201_CREATED)
        location = reverse('app-detail', args=(path, request.user.username))
        response['Location'] = request.build_absolute_uri(location)
        return response


class OrganizationUniversalAppDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, org_path, app_path):
        if request.user.is_authenticated:
            try:
                user_app = UniversalAppUser.objects.get(app__path=app_path, app__org__name=org_path, user=request.user)
                serializer = UserUniversalAppSerializer(user_app)
                return Response(serializer.data)
            except UniversalAppUser.DoesNotExist:
                pass
        try:
            user_org = OrganizationUser.objects.get(org__path=org_path, user=request.user)
            try:
                app = UniversalApp.objects.get(path=app_path, org=user_org.org)
                serializer = UniversalAppSerializer(app)
                return Response(serializer.data)
            except UniversalApp.DoesNotExist:
                raise Http404
        except OrganizationUser.DoesNotExist:
            if request.user.is_authenticated:
                allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            else:
                allow_visibility = [VisibilityType.Public]
            try:
                app = UniversalApp.objects.get(path=app_path, org__path=org_path, visibility__in=allow_visibility)
                serializer = UniversalAppSerializer(app)
                return Response(serializer.data)
            except UniversalApp.DoesNotExist:
                raise Http404
