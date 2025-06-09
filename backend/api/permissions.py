from rest_framework.permissions import BasePermission

class IsCreator(BasePermission):
    """
    gives access only to authenticated creators
    """
    message = 'You are not a creator!'
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_creator