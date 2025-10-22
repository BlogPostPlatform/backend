from rest_framework.permissions import BasePermission

from apps.users.models.user import Role


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.is_superuser or request.user.role == Role.ADMIN


class IsAuthorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.role == Role.AUTHOR

    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser or obj.author == request.user
