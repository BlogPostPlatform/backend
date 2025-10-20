from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.cached_group_names in ["Admins"]


class IsAuthorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.cached_group_names in ["Authors"]

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or obj.author == request.user
