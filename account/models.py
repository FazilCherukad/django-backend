import uuid
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,

)
from django.db import models
from django.utils import timezone
from django.utils.translation import pgettext_lazy
from django.contrib.auth.models import Group, Permission
from versatileimagefield.fields import VersatileImageField
from simple_history import register

from core.enums.enum import (
    UserType,
    Status,
    AuthType
)
from core.models import (
    BaseModel,
    SoftDeleteHistoryModel,
    ExportModel
)
from refs.models import Country

PERMISSIONS_FOR = [UserType.ADMIN.value]

class UserManager(BaseUserManager):

    def validate_mobile(self, mobile):
        return True

    def create_user(
            self, mobile, password=None, **extra_fields):
        """Create a user instance with the given email and password."""
        # mobile = UserManager.no(email)
        # Google OAuth2 backend send unnecessary username field
        extra_fields.pop('username', None)

        user = self.model(
            mobile=mobile, **extra_fields)
        if password:
            user.set_password(password)
        user.save()
        return user

    def create_superuser(self, mobile, password=None, **extra_fields):
        return self.create_user(
            mobile, password, is_superuser=False, **extra_fields)


def get_token():
    return str(uuid.uuid4())

class UserTypeGroup(BaseModel):
    user_type = models.CharField(max_length=10, choices=[(type.name, type.value) for type in UserType])
    group = models.ForeignKey(
        Group,
        related_name='user_types',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("group", "user_type"),)

class User(PermissionsMixin, AbstractBaseUser):
    country = models.ForeignKey(
        Country,
        related_name='users',
        on_delete=models.DO_NOTHING,
        null=True, blank=True
    )
    mobile = models.CharField(max_length=12, unique=True)
    code = models.CharField(max_length=15, unique=True)
    email = models.EmailField(null=True, blank=True, unique=True)
    name = models.CharField(max_length=256)
    token = models.UUIDField(default=get_token, editable=False, unique=True)
    note = models.TextField(null=True, blank=True)
    avatar = VersatileImageField(
        upload_to='user-avatars', blank=True, null=True)
    dob = models.DateField(null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    instagram = models.URLField(null=True, blank=True)
    whatsapp = models.CharField(max_length=12,  null=True, blank=True)

    USERNAME_FIELD = 'mobile'

    objects = UserManager()

    class Meta:
        permissions = (
            (
                'manage_users', pgettext_lazy(
                    'Permission description', 'Manage customers.')),
            (
                'manage_staff', pgettext_lazy(
                    'Permission description', 'Manage staff.')),
            (
                'impersonate_users', pgettext_lazy(
                    'Permission description', 'Impersonate customers.')))

    def has_role(self, roles, user_status=Status.ACTIVE.value):
        for role in roles:
            try:
                user_role = self.roles.get(user_type=role)
                if user_role:
                    status = ''
                    role_model = self.get_role_model(role)
                    if role_model:
                        if hasattr(role_model, 'status'):
                            status = role_model.status
                    if user_status:
                        if status == Status.ACTIVE.value:
                            return True
                    else:
                        return True
            except ObjectDoesNotExist:
                pass
        return False;

    def has_super_perms(self, perm):
        exist = False
        for role in self.roles.all().values_list('user_type', flat=True):
            is_super = False
            role_model = self.get_role_model(role)
            if role_model:
                if hasattr(role_model, 'is_super'):
                    is_super = role_model.is_super
            if is_super:
                if isinstance(perm, list):
                    for per in perm:
                        group = Group.objects.get(name=per)
                        exist = UserTypeGroup.objects.filter(user_type=role, group=group.id).exists()
                        if exist:
                            return exist
                else:
                    group = Group.objects.get(name=perm)
                    exist = UserTypeGroup.objects.filter(user_type=role, group=group.id).exists()
                    if exist:
                        return exist
        return exist

    def has_permission(self, perm):
        if isinstance(perm, list):
            return self.groups.filter(name__in=perm).exists() or (Group.objects.filter(name__in=perm).exists()
                                                       and self.has_super_perms(perm))

        return self.groups.filter(name=perm).exists() or (Group.objects.filter(name=perm).exists()
                                                              and self.has_super_perms( perm))

    def get_role_model(self, role):
        model = None
        if role == UserType.ADMIN.value:
            model = self.admin_user

        if role == UserType.STORE.value:
            model = self.store_user

        if role == UserType.SPONSOR.value:
            model = self.sponsor_user

        if role == UserType.CUSTOMER.value:
            model = self.customer

        if role == UserType.DELIVERY.value:
            model = self.delivery_boy

        if role == UserType.DEVELOPER.value:
            model = self.developer

        return model

    def get_store(self):
        store_user = self.get_role_model(UserType.STORE.value)
        if store_user:
            return store_user.store
        return None


class Admin(SoftDeleteHistoryModel, ExportModel):
    user = models.OneToOneField(
        User,
        related_name='admin_user',
        on_delete=models.CASCADE
    )
    is_super = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    auth_type = models.CharField(max_length=16, choices=[(type.name, type.value) for type in AuthType],
                              default=AuthType.TWO_FACTOR_NEW.value)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status],
                              default=Status.PENDING.value)


class UserRole(BaseModel):

    user = models.ForeignKey(
        User,
        related_name='roles',
        on_delete=models.CASCADE
    )
    user_type = models.CharField(max_length=10, choices=[(type.name, type.value) for type in UserType])

    class Meta:
        unique_together = (("user", "user_type"),)


register(User)


class Otp(BaseModel):
    user = models.ForeignKey(
        User,
        related_name='otps',
        on_delete=models.CASCADE
    )
    otp = models.IntegerField()
    session_id = models.CharField(max_length=128, null=True, blank=True)
    session_message = models.TextField(null=True, blank=True)
    expire = models.DateTimeField()





