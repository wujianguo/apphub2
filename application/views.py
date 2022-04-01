from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from application.models import UniversalApp, UniversalAppUser
from application.serializers import *
from application.permissions import *
from organization.models import OrganizationUser, Organization
from organization.views import check_org_admin_permission
from util.visibility import VisibilityType
from util.reserved import reserved_names
from util.pagination import get_pagination_params
from util.url import build_absolute_uri

UserModel = get_user_model()

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
        # data['role'] = ChoiceField(choices=UniversalAppUser.ApplicationUserRole.choices).to_representation(app_user.role)
        response = Response(data, status=status.HTTP_201_CREATED)
        location = reverse('app-detail', args=(path, request.user.username))
        response['Location'] = build_absolute_uri(location)
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


class UniversalAppDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        pass

    def path_exists(self, namespace, path):
        pass

    def get(self, request, namespace, path):
        app = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppSerializer(app)
        return Response(serializer.data)

    def put(self, request, namespace, path):
        app = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppCreateSerializer(app, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.validated_data.get('path', None) and path != serializer.validated_data['path']:
            if serializer.validated_data['path'] in reserved_names:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            if self.path_exists(namespace, serializer.validated_data['path']):
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

        instance = serializer.save()
        return Response(UniversalAppSerializer(instance).data)

    def delete(self, request, namespace, path):
        app = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        # todo
        app.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserUniversalAppDetail(UniversalAppDetail):
    def get_namespace(self, path):
        return user_namespace(path)

    def path_exists(self, namespace, path):
        return UniversalApp.objects.filter(path=path, owner__username=namespace).exists()

class OrganizationUniversalAppDetail(UniversalAppDetail):
    def get_namespace(self, path):
        return organization_namespace(path)

    def path_exists(self, namespace, path):
        return UniversalApp.objects.filter(path=path, org__path=namespace).exists()

class UniversalAppIcon(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_namespace(self, path):
        pass

    def url_name(self):
        pass

    def get(self, request, namespace, path):
        app = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        if not app.icon_file:
            raise Http404
        response = Response()
        response['X-Accel-Redirect'] = app.icon_file.url
        return response

    def post(self, request, namespace, path):
        app = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppIconSerializer(app, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        location = reverse(self.url_name(), args=(namespace, path))
        data = {
            'icon_file': build_absolute_uri(location)
        }
        # todo response no content
        response = Response(data)
        response['Location'] = build_absolute_uri(location)
        return response

class UserUniversalAppIcon(UniversalAppIcon):
    def get_namespace(self, path):
        return user_namespace(path)

    def url_name(self):
        return 'user-app-icon'

class OrganizationUniversalAppIcon(UniversalAppIcon):
    def get_namespace(self, path):
        return organization_namespace(path)
    
    def url_name(self):
        return 'org-app-icon'


class UniversalAppUserList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        pass

    def url_name(self):
        pass

    def get(self, request, namespace, path):
        app = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        users = UniversalAppUser.objects.filter(app=app)
        serializer = UniversalAppUserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppUserAddSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        username = serializer.validated_data['username']
        role = serializer.validated_data['role']
        try:
            UniversalAppUser.objects.get(app__path=path, user__username=username)
            return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        except UniversalAppUser.DoesNotExist:
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            instance = UniversalAppUser.objects.create(app=app, role=role, user=user)
            serializer = UniversalAppUserSerializer(instance)
            response = Response(serializer.data, status=status.HTTP_201_CREATED)
            location = reverse(self.url_name(), args=(namespace, path, username))
            response['Location'] = build_absolute_uri(location)
            return response

class UserUniversalAppUserList(UniversalAppUserList):
    def get_namespace(self, path):
        return user_namespace(path)

    def url_name(self):
        return 'user-app-user'

class OrganizationUniversalAppUserList(UniversalAppUserList):
    def get_namespace(self, path):
        return organization_namespace(path)
    
    def url_name(self):
        return 'org-app-user'


class UniversalAppUserDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        pass

    def get_object(self, app, username):
        try:
            return UniversalAppUser.objects.get(app=app, user__username=username)
        except UniversalAppUser.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, username):
        # todo
        app = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        app_user = self.get_object(app, username)
        serializer = UniversalAppUserSerializer(app_user)
        return Response(serializer.data)

    def put(self, request, namespace, path, username):
        app = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        manager_role = UniversalAppUser.ApplicationUserRole.Manager
        app_user = self.get_object(app, username)
        serializer = UniversalAppUserSerializer(app_user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        if request.user.username == username:
            if serializer.validated_data.get('role', manager_role) != manager_role:
                exists = UniversalAppUser.objects.filter(app=app, role=manager_role).exclude(user=request.user).exists()
                if not exists:
                    raise PermissionDenied
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, namespace, path, username):
        app = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        manager_role = UniversalAppUser.ApplicationUserRole.Manager
        app_user = self.get_object(app, username)
        if request.user.username == username:
            exists = UniversalAppUser.objects.filter(app=app, role=manager_role).exclude(user=request.user).exists()
            if not exists:
                raise PermissionDenied
        app_user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserUniversalAppUserDetail(UniversalAppUserDetail):
    def get_namespace(self, path):
        return user_namespace(path)

class OrganizationUniversalAppUserDetail(UniversalAppUserDetail):
    def get_namespace(self, path):
        return organization_namespace(path)


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

    @transaction.atomic
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
        response['Location'] = build_absolute_uri(location)
        return response
