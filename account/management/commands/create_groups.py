from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.utils.module_loading import import_module
from django.conf import settings

from account.models import UserTypeGroup

class Command(BaseCommand):
    help = 'Creates auth groups with permissions for each app'

    def handle(self, *args, **kwargs):

        for app in settings.INSTALLED_APPS:
            try:
                module = import_module(app+'.models')
                try:
                    user_types = module.PERMISSIONS_FOR
                    new_group, created = Group.objects.get_or_create(name=app)
                    permissions = Permission.objects.filter(content_type__app_label=app)
                    for type in user_types:
                        UserTypeGroup.objects.get_or_create(user_type=type, group=new_group)
                    for permission in permissions:
                        new_group.permissions.add(permission)
                except AttributeError:
                   pass
            except ImportError:
                pass
