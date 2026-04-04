from rest_framework.permissions import BasePermission, IsAuthenticated


class IsStaffUser(IsAuthenticated):
    """Admin / support: Django User with is_staff=True (spec.md §3)."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return bool(request.user and request.user.is_staff)


class IsSubscriptionOwnerOrStaff(BasePermission):
    """
    Object-level: staff may access any subscription row; regular users only rows
    where owner_id matches request.user (spec.md §3).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        owner_id = getattr(obj, 'owner_id', None)
        return owner_id is not None and owner_id == request.user.pk
