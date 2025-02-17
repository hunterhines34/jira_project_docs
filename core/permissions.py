from rest_framework import permissions

class IsProjectMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a project to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to project members
        return request.user.has_perm('core.change_project', obj)

class IsInstanceAdmin(permissions.BasePermission):
    """
    Custom permission to only allow Jira instance admins to modify instances.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to instance admins
        return request.user.has_perm('core.change_jirainstance', obj) 