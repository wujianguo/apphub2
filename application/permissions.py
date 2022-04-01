from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from application.models import UniversalApp, UniversalAppUser
from organization.models import Organization, OrganizationUser
from util.visibility import VisibilityType

def is_user_namespace(namespace):
    return namespace['kind'] == 'User'

def is_organization_namespace(namespace):
    return namespace['kind'] == 'Organization'

def get_namespace_path(namespace):
    return namespace['path']

def user_namespace(path):
    return {
        'kind': 'User',
        'path': path
    }

def organization_namespace(path):
    return {
        'kind': 'Organization',
        'path': path
    }

def user_app_viewer_query(user, path, ownername):
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

def check_user_app_view_permission(user, path, ownername):
    app_user = UniversalAppUser.objects.filter(user_app_viewer_query(user, path, ownername))
    if not app_user.exists():
        raise Http404
    return app_user.first().app

def check_org_app_view_permission(user, path, org_path):
    try:
        app = UniversalApp.objects.get(org__path=org_path, path=path)
    except UniversalApp.DoesNotExist:
        raise Http404

    if user.is_authenticated and (app.visibility == VisibilityType.Public or app.visibility == VisibilityType.Internal):
        return app

    if not user.is_authenticated and app.visibility == VisibilityType.Public:
        return app

    try:
        OrganizationUser.objects.get(org__path=org_path, user=user)
        return app
    except OrganizationUser.DoesNotExist:
        pass

    try:
        UniversalAppUser.objects.get(app=app, user=user)
        return app
    except UniversalAppUser.DoesNotExist:
        pass
        
    raise Http404

def check_app_view_permission(user, path, namespace):
    if is_user_namespace(namespace):
        return check_user_app_view_permission(user, path, get_namespace_path(namespace))
    if is_organization_namespace(namespace):
        return check_org_app_view_permission(user, path, get_namespace_path(namespace))

def check_user_app_manager_permission(user, path, ownername):
    try:
        manager_role = UniversalAppUser.ApplicationUserRole.Manager
        user_app = UniversalAppUser.objects.get(app__path=path, app__owner__username=ownername, user=user)
        if user_app.role != manager_role:
            raise PermissionDenied
        return user_app.app
    except UniversalAppUser.DoesNotExist:
        try:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            UniversalApp.objects.get(path=path, owner__username=ownername, visibility__in=allow_visibility)
            raise PermissionDenied
        except UniversalApp.DoesNotExist:
            raise Http404

def check_org_app_manager_permission(user, path, org_path):
    try:
        app = UniversalApp.objects.get(path=path, org__path=org_path)
    except UniversalApp.DoesNotExist:
        raise Http404

    try:
        manager_role = UniversalAppUser.ApplicationUserRole.Manager
        user_app = UniversalAppUser.objects.get(app=app, user=user)
        if user_app.role != manager_role:
            raise PermissionDenied
        return app
    except UniversalAppUser.DoesNotExist:
        pass

    try:
        admin_role = OrganizationUser.OrganizationUserRole.Admin
        user_org = OrganizationUser.objects.get(org__path=org_path, user=user)
        if user_org.role != admin_role:
            raise PermissionDenied
        return app
    except OrganizationUser.DoesNotExist:
        try:
            allow_visibility = [VisibilityType.Public, VisibilityType.Internal]
            Organization.objects.get(path=org_path, visibility__in=allow_visibility)
            raise PermissionDenied
        except Organization.DoesNotExist:
            raise Http404

def check_app_manager_permission(user, path, namespace):
    if is_user_namespace(namespace):
        return check_user_app_manager_permission(user, path, get_namespace_path(namespace))
    if is_organization_namespace(namespace):
        return check_org_app_manager_permission(user, path, get_namespace_path(namespace))
