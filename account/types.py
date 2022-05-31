import django.contrib.auth.models as auth_model

import graphene
from graphene import relay

from core.utils.connection import CountableDjangoObjectType
from core.enums.enum import UserType
from . import models

class Group(CountableDjangoObjectType):

    class Meta:
        description = 'Represents a group.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = auth_model.Group

class User(CountableDjangoObjectType):
    email = graphene.String(description='Email id  of a user')
    mobile = graphene.String(description='User mobile.')
    name = graphene.String(description='User name.')
    avatar = graphene.String(description='User avatar.')
    note = graphene.String(description='User note.')
    dob = graphene.Date(description='User dob.')
    token = graphene.String(description='Token.')
    facebook = graphene.String(description='User facebook.')
    instagram = graphene.String(description='User instagram.')
    whatsapp = graphene.String(description='User whatsapp.')
    admin_groups = graphene.List(Group, description="groups")
    store_groups = graphene.List(Group, description="groups")

    class Meta:
        description = 'Represents a user.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.User

    def resolve_admin_groups(self, info):
        if hasattr(self, 'admin_user'):
            admin = self.admin_user
            is_super = admin.is_super
            groups = models.UserTypeGroup.objects.filter(user_type=UserType.ADMIN.value).values_list('group')
            if is_super:
                return auth_model.Group.objects.filter(pk__in=groups)
            else:
                return self.groups.filter(pk__in=groups)
        return []

    def resolve_store_groups(self, info):

        if hasattr(self, 'store_user'):
            store = self.store_user
            is_super = store.is_super
            groups = models.UserTypeGroup.objects.filter(user_type=UserType.STORE.value).values_list('group')
            if is_super:
                return auth_model.Group.objects.filter(pk__in=groups)
            else:
                return self.groups.filter(pk__in=groups)
        return []



class Admin(CountableDjangoObjectType):
    is_super = graphene.Boolean(description='Is super admin.')
    date_joined = graphene.Date(description='Admin joined date.')
    status = graphene.String(description='Admin status.')

    class Meta:
        description = 'Represents a admin.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Admin


class UserRole(CountableDjangoObjectType):

    user_type = graphene.String(description='User role type')

    class Meta:
        description = 'Represents a user role.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.UserRole

class UserTypeGroup(CountableDjangoObjectType):
    group = Group()
    user_type = graphene.String(description='User role type')
    class Meta:
        description = 'Represents a user type permission group.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.UserTypeGroup

class Otp(CountableDjangoObjectType):
    class Meta:
        description = 'Represents a otp.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Otp