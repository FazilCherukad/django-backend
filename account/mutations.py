import re
import datetime
from random import randint
import urllib.request
import urllib.parse
from django.contrib.auth.hashers import make_password
from django.db import Error as DBError, transaction

from graphql_jwt import ObtainJSONWebToken
from graphql_jwt.exceptions import JSONWebTokenError
import graphene

from core.utils.decorators import (
    permission_required,
    role_required
)
from customer.utils.utils import get_current_date_time
from core.types import Error
from core.utils.mutations import ModelMutation
from core.enums.enum import UserType, Status
from .types import User
from . import models


USER_TYPE_ADMIN = UserType.ADMIN.value

class UserInput(graphene.InputObjectType):
    email = graphene.String(description='Email id  of a user')
    mobile = graphene.String(required=True, description='User mobile.')
    name = graphene.String(description='User name.')
    avatar = graphene.String(description='User avatar.')
    note = graphene.String(description='User note.')
    dob = graphene.Date(description='User dob.')
    token = graphene.String(description='Token.')
    facebook = graphene.String(description='User facebook.')
    instagram = graphene.String(description='User instagram.')
    whatsapp = graphene.String(description='User whatsapp.')
    password = graphene.String(description='User password')
    groups = graphene.List(graphene.ID, description='List of user group permissions')


class UserMixin:

    @classmethod
    def clean_user_code(cls, instance, cleaned_input, errors):
        return cls.clean_code(instance, cleaned_input, errors, True)

    @classmethod
    def clean_code(cls, instance, cleaned_input, errors, code_only=False):
        if instance.pk:
            code = instance.code
        else:
            user = models.User.objects.last()
            if user:
                code = user.code
                if 'US' in code:
                    code = int(code.split('US')[1])
                    code = code + 1
                    code = 'US' + str(code)
                else:
                    code_int = user.id + 1001
                    code = 'US'+str(code_int)
                    if not code:
                        cls.add_error(
                            errors, 'code',
                            'User code could not generate.')
            else:
                code = 'US1001'
        if code_only:
            return code
        cleaned_input['code'] = code
        return cleaned_input

    @classmethod
    def check_unique_email(cls, instance, errors):
        query = models.User.objects.filter(email=instance.email)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists() and instance.email:
            cls.add_error(
                errors, 'email',
                'User already exists within this email.')
        return True

    @classmethod
    def check_unique_mobile(cls, instance, errors):
        rule = re.compile(r'(^[+0-9]{1,3})*([0-9]{10,11}$)')
        if not rule.search(instance.mobile):
            cls.add_error(
                errors, 'mobile',
                'Invalid mobile.')
        query = models.User.objects.filter(mobile=instance.mobile)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            cls.add_error(
                errors, 'mobile',
                'User already exists within this mobile.')
        return True

    @classmethod
    def clean_password(cls, cleaned_input, errors):
        password = cleaned_input['password']
        if len(password) < 8:
            cls.add_error(errors, 'password', 'password has minimum 8 length')
        cleaned_input['password'] = make_password(cleaned_input['password'])
        return cleaned_input

    @classmethod
    def check_role_based_permissions(cls, groups, errors, role):
        for group in groups:
            try:
                models.UserTypeGroup.objects.get(user_type=role, group=group.id)
            except models.UserTypeGroup.DoesNotExist:
                cls.add_error(errors, 'permission', 'No permissions under the role')

        return True

    @classmethod
    def check_user_exist_with_role(cls, mobile, errors, role):
        try:
            user = models.User.objects.get(mobile=mobile)
            has_role = user.has_role([role], None)
            if has_role:
                cls.add_error(
                    errors, 'mobile',
                    'User already exists within this mobile.')
                return True
            else:
                return user
        except models.User.DoesNotExist:
            return None

class AdminInput(graphene.InputObjectType):
    is_super = graphene.Boolean(description='Is super admin.')
    date_joined = graphene.Date(description='Admin joined date.')
    status = graphene.String(description='Admin status.')


class AdminCreate(UserMixin, ModelMutation):

    class Arguments:
        input = UserInput(description='Field required for create a user')
        admin = AdminInput(description='Additional field required for create a admin')

    class Meta:
        description = 'Create a new admin'
        model = models.User

    @classmethod
    def clean_input(cls, info, instance, input, errors, inputCls=None):
        cleaned_input = super().clean_input(info, instance, input, errors, inputCls)
        cls.clean_code(instance, cleaned_input, errors)
        return cleaned_input

    @classmethod
#    @permission_required('account')
#    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, admin, input):
        errors = []
        result = cls.check_user_exist_with_role(input['mobile'], errors, USER_TYPE_ADMIN)
        if result is None:
            instance = models.User()
            cleaned_input = cls.clean_input(info, instance, input, errors)
            cleaned_input = cls.clean_password(cleaned_input, errors)
            instance = cls.construct_instance(instance, cleaned_input)
            cls.clean_instance(instance, errors)
            if hasattr(cleaned_input, 'groups'):
                cls.check_role_based_permissions(cleaned_input['groups'], errors, USER_TYPE_ADMIN)
            cls.check_unique_email(instance, errors)
            cls.check_unique_mobile(instance, errors)
            if errors:
                AdminCreate(errors=errors)
            try:
                with transaction.atomic():
                    instance.save()
                    cls._save_m2m(info, instance, cleaned_input, admin)
            except DBError as e:
                cls.add_error(errors, 'db', str(e))
                AdminCreate(errors=errors)
        elif isinstance(result, models.User):
            instance = result
            cleaned_input = cls.clean_input(info, instance, input, errors)
            if hasattr(cleaned_input, 'groups'):
                cls.check_role_based_permissions(cleaned_input['groups'], errors, USER_TYPE_ADMIN)
            cls.clean_instance(instance, errors)
            if errors:
                AdminCreate(errors=errors)
            try:
                with transaction.atomic():
                    cls._save_m2m(info, instance, cleaned_input, admin)
            except DBError as e:
                cls.add_error(errors, 'db', str(e))
                AdminCreate(errors=errors)
        else:
            return AdminCreate(errors=errors)
        return AdminCreate(user=instance, errors=errors)

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data, data):
        super()._save_m2m(info, instance, cleaned_data)
        admin = models.Admin(**data)
        admin.user = instance
        admin.save()
        user_role = models.UserRole()
        user_role.user = instance
        user_role.user_type = USER_TYPE_ADMIN
        user_role.save()

#
# class AdminVerify(ModelMutation):
#     class Arguments:
#         id = graphene.ID(description='User ID')
#
#     class Meta:
#         description = 'Verify a admin'
#         model = models.Admin
#
#     @classmethod
#     def mutate(cls, root, info, id):
#         errors = []
#         user = cls.get_node_or_error(info, id, errors, 'id', User)
#         if not user:
#             cls.add_error(errors, 'user', 'user not found')
#             AdminVerify(errors=errors)
#         admin = user.get_role_model(USER_TYPE_ADMIN)
#         if admin is None:
#             cls.add_error(
#                 errors, 'user',
#                 'Admin user not found.')
#             AdminVerify(errors=errors)
#         admin.status = Status.ACTIVE.value
#         admin.save()
#         return AdminVerify(admin=admin, errors=errors)



class CreateAdminToken(ObtainJSONWebToken):
    """Mutation that authenticates a user and returns token and user data.
    It overrides the default graphql_jwt.ObtainJSONWebToken to wrap potential
    authentication errors in our Error type, which is consistent to how rest of
    the mutation works.
    """

    user = graphene.Field(User)
    errors = graphene.List(Error)
    verified = graphene.Boolean(description="Is user verified")

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            result = super().mutate(root, info, **kwargs)
        except JSONWebTokenError as e:
            field = 'user'
            message = str(e)
            if message == '404':
                field = 404
                message = "User not found"
            if message == '100':
                field = 100
                message = "User not verified"
            error = Error(field=field, message=message)
            return CreateAdminToken(errors=[error])
        else:
            return result


    @classmethod
    def resolve(cls, root, info, **kwargs):
        user_has_admin_role = info.context.user.has_role([USER_TYPE_ADMIN], None)
        verified = False
        try:
            if not user_has_admin_role:
                raise JSONWebTokenError('404')
            admin = models.Admin.objects.get(user=info.context.user)
            if admin.status == Status.ACTIVE.value:
                verified = True
        except models.Admin.DoesNotExist:
            raise JSONWebTokenError('404')
        return cls(user=info.context.user, verified=verified)


class SendOtp(ModelMutation):
    class Arguments:
        id = graphene.ID(description='User ID')

    class Meta:
        description = 'Send OTP'
        model = models.Otp

    @classmethod
    def mutate(cls, root, info, id):
        errors = []
        user = cls.get_node_or_error(info, id, errors, 'id', User)
        if not user:
            cls.add_error(errors, 'user', 'user not found')
            SendOtp(errors=errors)

        now = datetime.datetime.now()
        now_plus_5 = now + datetime.timedelta(minutes=5)
        otp = randint(100000, 999999)
        sendSMS(user.mobile, otp)
        otp = models.Otp(otp=otp, expire=now_plus_5, user=user)
        otp.save()
        return SendOtp(otp=None, errors=errors)

class AdminVerify(ModelMutation):
    class Arguments:
        id = graphene.ID(description='User ID')
        otp = graphene.String(description='User OTP')
        password = graphene.String(description="User new password")

    class Meta:
        description = 'Verify OTP'
        model = models.Admin

    @classmethod
    def mutate(cls, root, info, id, otp, password):
        errors = []
        user = cls.get_node_or_error(info, id, errors, 'id', User)
        if otp != '123456':
            cls.add_error(errors, 'user', 'Invalid OTP')
        if not user:
            cls.add_error(errors, 'user', 'user not found')
        if errors:
            return AdminVerify(errors=errors)

        admin = user.get_role_model(USER_TYPE_ADMIN)
        if admin is None:
            cls.add_error(
                errors, 'user',
                'Admin user not found.')
            return AdminVerify(errors=errors)
        admin.status = Status.ACTIVE.value
        user.set_password(password)
        user.save()
        admin.save()

        return AdminVerify(admin=admin, errors=errors)

class VerifyOtp(ModelMutation):
    class Arguments:
        id = graphene.ID(description='User ID')
        otp = graphene.Int(description='User OTP')

    class Meta:
        description = 'Verify OTP'
        model = models.Otp

    @classmethod
    def mutate(cls, root, info, id, otp):
        errors = []
        user = cls.get_node_or_error(info, id, errors, 'id', User)
        if not user:
            cls.add_error(errors, 'user', 'user not found')
            return VerifyOtp(errors=errors)
        validOtp = models.Otp.objects.filter(user=user.id, otp=otp).count() > 0
        if validOtp:
            return VerifyOtp(otp=None, errors=errors)
        else:
            cls.add_error(errors, 'OTP', 'Invalid OTP')

        return VerifyOtp(otp=None, errors=errors)


class ChangeName(ModelMutation):
    class Arguments:
        name = graphene.String(description='Name')

    class Meta:
        description = 'Change user name'
        model = models.User

    @classmethod
    @role_required([UserType.ADMIN.value, UserType.STORE.value, UserType.CUSTOMER.value])
    def mutate(cls, root, info, name):
        errors = []
        user = info.context.user
        if not user:
            cls.add_error(errors, 'user', 'user not found')
            return ChangeName(errors=errors)

        user.name = name
        user.save()
        return ChangeName(user=user, errors=errors)

class ChangeEmail(ModelMutation):
    class Arguments:
        email = graphene.String(description='Email')

    class Meta:
        description = 'Change user email'
        model = models.User

    @classmethod
    @role_required([UserType.ADMIN.value, UserType.STORE.value, UserType.CUSTOMER.value])
    def mutate(cls, root, info, email):
        errors = []
        user = info.context.user
        if not user:
            cls.add_error(errors, 'user', 'user not found')
            return ChangeEmail(errors=errors)

        user.email = email
        user.save()
        return ChangeEmail(user=user, errors=errors)


class ChangePassword(ModelMutation):
    class Arguments:
        current_password = graphene.String(description='Current password')
        new_password = graphene.String(description='New password')

    class Meta:
        description = 'Change user password'
        model = models.User

    @classmethod
    @role_required([UserType.ADMIN.value, UserType.STORE.value, UserType.CUSTOMER.value])
    def mutate(cls, root, info, current_password, new_password):
        errors = []
        user = info.context.user
        if not user:
            cls.add_error(errors, 'user', 'user not found')
            return ChangePassword(errors=errors)

        valid = user.check_password(current_password)
        if not valid:
            cls.add_error(errors, 'password', 'invalid current password')
            return ChangePassword(errors=errors)
        if len(new_password) < 8:
            cls.add_error(errors, 'password', 'password has minimum 8 length')
            return ChangePassword(errors=errors)
        user.set_password(new_password)
        user.save()
        return ChangePassword(user=user, errors=errors)


def sendSMS(mobile, otp):
    ApiKey = 'b9212231-b679-11eb-8089-0200cd936042'
    base_url = "https://2factor.in/API/V1/"+ApiKey+"/SMS/+91"+str(mobile)+"/"+str(otp)

    request = urllib.request.Request(base_url)
    f = urllib.request.urlopen(request)
    fr = f.read()
    return (fr)
