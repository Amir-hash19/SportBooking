from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """
    A Custom permission for admins

    check this permission that
    is the user is admin or not
    and check that the user is in the
    group or not

    return = Boolean

    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name="SuperAdmin").exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name="SuperAdmin").exists()


class IsComplexManager(permissions.BasePermission):
    """
        check users is the member of the manager complex or not
        user must be authenticated
        user must not be a superuser 
        
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_complex_manager
            and not request.user.is_super_admin
        )


class IsRegularUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and not request.user.is_super_admin
            and not request.user.is_complex_manager
        )


class IsProfileComplete(permissions.BasePermission):
    """

    Docstring for IsProfileComplete
    This Class check that
    the user has a completed
    profile or not

    using a property method in models
    """

    def has_permission(self, request, view):
        try:
            return request.user.profile.is_complete
        except:
            return False
