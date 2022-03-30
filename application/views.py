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
from util.url import build_absolute_uri

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

    def put(self, request, username, path):
        user_app = check_app_manager_permission(request.user, path, username)
        serializer = UniversalAppCreateSerializer(user_app.app, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.validated_data.get('path', None) and path != serializer.validated_data['path']:
            if serializer.validated_data['path'] in reserved_names:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            if UniversalApp.objects.filter(path=serializer.validated_data['path']).exists():
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

        instance = serializer.save()
        return Response(UniversalAppSerializer(instance).data)

    def delete(self, request, username, path):
        user_app = check_app_manager_permission(request.user, path, username)
        # todo
        user_app.app.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserUniversalAppIcon(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, username, path):
        user_app = check_app_view_permission(request.user, path, username)
        if not user_app.app.icon_file:
            raise Http404
        response = Response()
        response['X-Accel-Redirect'] = user_app.app.icon_file.url
        return response

    def post(self, request, username, path):
        user_app = check_app_manager_permission(request.user, path, username)
        serializer = UniversalAppIconSerializer(user_app.app, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        location = reverse('user-app-icon', args=(username, path))
        data = {
            'icon_file': build_absolute_uri(location)
        }
        # todo response no content
        response = Response(data)
        response['Location'] = build_absolute_uri(location)
        return response

# org
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

    def get(self, request, org_path):
        page, per_page = get_pagination_params(request)
        apps = []
        if request.user.is_authenticated:
            try:
                user_org = OrganizationUser.objects.get(org__path=org_path, user=request.user)
                apps = UniversalApp.objects.filter(org=user_org.org).order_by('path')[(page - 1) * per_page: page * per_page]
            except OrganizationUser.DoesNotExist:
                try:
                    allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
                    org = Organization.objects.get(org__path=org_path, visibility__in=allow_visibility)
                    apps = UniversalApp.objects.filter(org=org, visibility__in=allow_visibility).order_by('path')[(page - 1) * per_page: page * per_page]
                except Organization.DoesNotExist:
                    pass
        else:
            try:
                org = Organization.objects.get(org__path=org_path, visibility=VisibilityType.Public)
                apps = UniversalApp.objects.filter(org=org, visibility=VisibilityType.Public).order_by('path')[(page - 1) * per_page: page * per_page]
            except Organization.DoesNotExist:
                pass

        serializer = UniversalAppSerializer(apps, many=True)
        return Response(serializer.data)

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

    def put(self, request, org_path, app_path):
        user_org = check_org_admin_permission(org_path, request.user)
        try:
            app = UniversalApp.objects.get(path=app_path, org=user_org.org)
        except UniversalApp.DoesNotExist:
            raise Http404
        serializer = UniversalAppCreateSerializer(app, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.validated_data.get('path', None) and app_path != serializer.validated_data['path']:
            if serializer.validated_data['path'] in reserved_names:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            if UniversalApp.objects.filter(path=serializer.validated_data['path']).exists():
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

        instance = serializer.save()
        return Response(UniversalAppSerializer(instance).data)

    def delete(self, request, org_path, app_path):
        user_org = check_org_admin_permission(org_path, request.user)
        # todo
        try:
            app = UniversalApp.objects.get(path=app_path, org=user_org.org)
            app.delete()
        except UniversalApp.DoesNotExist:
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationUniversalAppIcon(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, org_path, app_path):
        user_org = check_org_view_permission(org_path, request.user)
        try:
            app = UniversalApp.objects.get(path=app_path, org=user_org.org)
        except UniversalApp.DoesNotExist:
            raise Http404
        if not app.icon_file:
            raise Http404
        response = Response()
        response['X-Accel-Redirect'] = app.icon_file.url
        return response

    def post(self, request, org_path, app_path):
        user_org = check_org_admin_permission(org_path, request.user)
        try:
            app = UniversalApp.objects.get(path=app_path, org=user_org.org)
        except UniversalApp.DoesNotExist:
            raise Http404

        serializer = UniversalAppIconSerializer(app, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        location = reverse('org-app-icon', args=(org_path, app_path))
        data = {
            'icon_file': build_absolute_uri(location)
        }
        # todo response no content
        response = Response(data)
        response['Location'] = build_absolute_uri(location)
        return response
