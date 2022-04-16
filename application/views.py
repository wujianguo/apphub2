import secrets
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
from organization.views import check_org_manager_permission
from util.visibility import VisibilityType
from util.reserved import reserved_names
from util.pagination import get_pagination_params
from util.url import build_absolute_uri
from util.role import Role
from util.storage import internal_file_response

UserModel = get_user_model()

class VisibleUniversalAppList(APIView):
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
            # app_data.sort(key=lambda x: x['create_time'])
            headers = {'x-total-count': len(app_data)}
            return Response(app_data[(page - 1) * per_page: page * per_page], headers=headers)
        else:
            query = UniversalApp.objects.filter(visibility=VisibilityType.Public)
            count = query.count()
            apps = query.order_by('create_time')[(page - 1) * per_page: page * per_page]
            serializer = UniversalAppSerializer(apps, many=True)
            headers = {'x-total-count': count}
            return Response(serializer.data, headers=headers)

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
            data.sort(key=lambda x: x['create_time'])
            headers = {'x-total-count': len(data)}
            return Response(data[(page - 1) * per_page: page * per_page], headers=headers)
        else:
            query = UniversalApp.objects.filter(visibility=VisibilityType.Public, owner__username=username)
            count = query.count()
            apps = query.order_by('create_time')[(page - 1) * per_page: page * per_page]
            serializer = UniversalAppSerializer(apps, many=True)
            headers = {'x-total-count': count}
            return Response(serializer.data, headers=headers)


class AuthenticatedUserApplicationList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return UserUniversalAppList().get(request, request.user.username)

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
        app_user = UniversalAppUser.objects.create(app=instance, user=request.user, role=Role.Owner)
        data = UniversalAppSerializer(instance).data
        data['role'] = UserRoleKind.application(app_user.role).response()
        response = Response(data, status=status.HTTP_201_CREATED)
        location = reverse('user-app-detail', args=(path, request.user.username))
        response['Location'] = build_absolute_uri(location)
        return response


class UserUniversalAppDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def path_exists(self, namespace, path):
        return UniversalApp.objects.filter(path=path, owner__username=namespace).exists()

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        data = UniversalAppSerializer(app).data
        if role:
            data['role'] = role.response()
        return Response(data)

    def put(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppCreateSerializer(app, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        to_path = serializer.validated_data.get('path', None)
        if to_path and path != to_path:
            if to_path in reserved_names:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            if self.path_exists(namespace, to_path):
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
        slug = serializer.validated_data.get('install_slug', None)
        if slug and app.install_slug != slug:
            if slug in reserved_names or UniversalApp.objects.filter(install_slug=slug).exists():
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)

        instance = serializer.save()
        data = UniversalAppSerializer(instance).data
        data['role'] = role.response()
        return Response(data)

    def delete(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        # todo
        app.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationUniversalAppDetail(UserUniversalAppDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def path_exists(self, namespace, path):
        return UniversalApp.objects.filter(path=path, org__path=namespace).exists()

class UserUniversalAppIcon(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def url_name(self):
        return 'user-app-icon'

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppIconSerializer(app, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        app.icon_file.delete()
        instance = serializer.save()
        location = reverse(self.url_name(), args=(namespace, path, os.path.basename(instance.icon_file.name)))
        data = {
            'icon_file': build_absolute_uri(location)
        }
        # todo response no content
        response = Response(data)
        response['Location'] = build_absolute_uri(location)
        return response

class OrganizationUniversalAppIcon(UserUniversalAppIcon):
    def get_namespace(self, path):
        return Namespace.organization(path)

    def url_name(self):
        return 'org-app-icon'

class UserUniversalAppIconDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get(self, request, namespace, path, icon_name):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        return internal_file_response(app.icon_file, icon_name)

class OrganizationUniversalAppIconDetail(UserUniversalAppIconDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)


class UserUniversalAppUserList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def url_name(self):
        return 'user-app-user'

    def get(self, request, namespace, path):
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        users = UniversalAppUser.objects.filter(app=app)
        serializer = UniversalAppUserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
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

class OrganizationUniversalAppUserList(UserUniversalAppUserList):
    def get_namespace(self, path):
        return Namespace.organization(path)
    
    def url_name(self):
        return 'org-app-user'


class UserUniversalAppUserDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, app, username):
        try:
            return UniversalAppUser.objects.get(app=app, user__username=username)
        except UniversalAppUser.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, username):
        # todo
        app, role = check_app_view_permission(request.user, path, self.get_namespace(namespace))
        app_user = self.get_object(app, username)
        serializer = UniversalAppUserSerializer(app_user)
        return Response(serializer.data)

    def put(self, request, namespace, path, username):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        app_user = self.get_object(app, username)
        serializer = UniversalAppUserSerializer(app_user, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        role = serializer.validated_data.get('role', None)
        if role == Role.Owner or (app.owner and app.owner.username == username):
            raise PermissionDenied
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, namespace, path, username):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        app_user = self.get_object(app, username)
        if app.owner and app.owner.username == username:
            raise PermissionDenied
        app_user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationUniversalAppUserDetail(UserUniversalAppUserDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

class UserUniversalAppTokenList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def url_name(self):
        return 'user-app-token'

    def get(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        tokens = AppAPIToken.objects.filter(app=app)
        serializer = UniversalAppTokenSerializer(tokens, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = UniversalAppTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(app=app, token=secrets.token_hex(16))
        response = Response(UniversalAppTokenSerializer(instance).data, status=status.HTTP_201_CREATED)
        location = reverse(self.url_name(), args=(namespace, path, instance.id))
        response['Location'] = build_absolute_uri(location)
        return response

class OrganizationUniversalAppTokenList(UserUniversalAppTokenList):
    def get_namespace(self, path):
        return Namespace.organization(path)
    
    def url_name(self):
        return 'org-app-token'


class UserUniversalAppTokenDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, token_id):
        try:
            return AppAPIToken.objects.get(id=token_id)
        except AppAPIToken.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, token_id):
        # todo
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        token = self.get_object(token_id)
        serializer = UniversalAppTokenSerializer(token)
        return Response(serializer.data)

    def put(self, request, namespace, path, token_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        token = self.get_object(token_id)
        serializer = UniversalAppTokenSerializer(token, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, namespace, path, token_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        token = self.get_object(token_id)
        token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationUniversalAppTokenDetail(UserUniversalAppTokenDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)

class UserUniversalAppWebhookList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def url_name(self):
        return 'user-app-webhook'

    def get(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        webhooks = Webhook.objects.filter(app=app)
        serializer = WebhookSerializer(webhooks, many=True)
        return Response(serializer.data)

    def post(self, request, namespace, path):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        serializer = WebhookSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save(app=app)
        response = Response(WebhookSerializer(instance).data, status=status.HTTP_201_CREATED)
        location = reverse(self.url_name(), args=(namespace, path, instance.id))
        response['Location'] = build_absolute_uri(location)
        return response

class OrganizationUniversalAppWebhookList(UserUniversalAppWebhookList):
    def get_namespace(self, path):
        return Namespace.organization(path)
    
    def url_name(self):
        return 'org-app-webhook'


class UserUniversalAppWebhookDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_namespace(self, path):
        return Namespace.user(path)

    def get_object(self, webhook_id):
        try:
            return Webhook.objects.get(id=webhook_id)
        except Webhook.DoesNotExist:
            raise Http404

    def get(self, request, namespace, path, webhook_id):
        # todo
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        webhook = self.get_object(webhook_id)
        serializer = WebhookSerializer(webhook)
        return Response(serializer.data)

    def put(self, request, namespace, path, webhook_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        webhook = self.get_object(webhook_id)
        serializer = WebhookSerializer(webhook, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, namespace, path, webhook_id):
        app, role = check_app_manager_permission(request.user, path, self.get_namespace(namespace))
        webhook = self.get_object(webhook_id)
        webhook.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class OrganizationUniversalAppWebhookDetail(UserUniversalAppWebhookDetail):
    def get_namespace(self, path):
        return Namespace.organization(path)


class OrganizationUniversalAppList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, org_path):
        page, per_page = get_pagination_params(request)
        apps = []
        if request.user.is_authenticated:
            try:
                user_org = OrganizationUser.objects.get(org__path=org_path, user=request.user)
                apps = UniversalApp.objects.filter(org=user_org.org).order_by('create_time')[(page - 1) * per_page: page * per_page]
            except OrganizationUser.DoesNotExist:
                try:
                    allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
                    org = Organization.objects.get(path=org_path, visibility__in=allow_visibility)
                    apps = UniversalApp.objects.filter(org=org, visibility__in=allow_visibility).order_by('create_time')[(page - 1) * per_page: page * per_page]
                except Organization.DoesNotExist:
                    pass
        else:
            try:
                org = Organization.objects.get(path=org_path, visibility=VisibilityType.Public)
                apps = UniversalApp.objects.filter(org=org, visibility=VisibilityType.Public).order_by('create_time')[(page - 1) * per_page: page * per_page]
            except Organization.DoesNotExist:
                pass

        serializer = UniversalAppSerializer(apps, many=True)
        headers = {'x-total-count': len(apps)}
        return Response(serializer.data, headers=headers)

    @transaction.atomic
    def post(self, request, org_path):
        user_org = check_org_manager_permission(org_path, request.user)
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
        data['role'] = UserRoleKind.organization(user_org.role).response()
        response = Response(data, status=status.HTTP_201_CREATED)
        location = reverse('org-app-detail', args=(path, request.user.username))
        response['Location'] = build_absolute_uri(location)
        return response
