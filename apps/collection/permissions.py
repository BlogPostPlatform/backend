from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """
    Object-level permission:
    - Collection.owner == request.user
    - CollectionItem.collection.owner == request.user
    """

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        owner = getattr(obj, "owner", None)
        if owner is not None:
            return owner == request.user

        # CollectionItem case
        collection = getattr(obj, "collection", None)
        if collection is not None:
            return collection.owner == request.user

        return False
