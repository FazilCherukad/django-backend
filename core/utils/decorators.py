from functools import wraps

from django.core.exceptions import PermissionDenied
from graphql.execution.base import ResolveInfo


def permission_required(permissions):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 2:
                info = args[2]
            elif len(args) == 2:
                info = args[1]
            else:
                info = args[0]
            assert isinstance(info, ResolveInfo)
            user = info.context.user
            if not user.is_authenticated:
                raise PermissionDenied(
                    'You have no permission to use %s' % info.field_name)
                return func(*args, **kwargs)
            if not user.has_permission(permissions):
                raise PermissionDenied(
                    'You have no permission to use %s' % info.field_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def role_required(roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 2:
                info = args[2]
            elif len(args) == 2:
                info = args[1]
            else:
                info = args[0]
            assert isinstance(info, ResolveInfo)
            user = info.context.user
            if not user.is_authenticated:
                raise PermissionDenied(
                    'You have no permission to use %s' % info.field_name)
                return func(*args, **kwargs)
            if not user.has_role(roles):
                raise PermissionDenied(
                    'You have no permission to use %s' % info.field_name)
            return func(*args, **kwargs)
        return wrapper
    return decorator