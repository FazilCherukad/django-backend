import graphene

from core.utils.fields import PrefetchingConnectionField, FilterInputConnectionField
from core.utils.decorators import (
    permission_required,
    role_required
)
from core.enums.enum import UserType
from .mutations import (
    AdminCreate,
    CreateAdminToken,
    AdminVerify,
    SendOtp,
    VerifyOtp,
    ChangeName,
    ChangeEmail,
    ChangePassword
)
from .types import (
    UserTypeGroup,
    Admin
)
from .resolvers import (
    resolve_user_type_groups,
    resolve_users
)

class UserAccountQuery(graphene.ObjectType):
    user_type_group = graphene.Field(
        UserTypeGroup, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a user type group by ID.')
    user_type_groups = FilterInputConnectionField(
        UserTypeGroup, query=graphene.String(
            description='List of user type groups query'),
        role=graphene.Argument(graphene.String),
        description='List of user type groups.')

    users = FilterInputConnectionField(Admin,
        query=graphene.String(description='List of brands query'),
        description='List of user type groups.')

    @role_required([UserType.ADMIN.value, UserType.STORE.value, UserType.DEVELOPER.value])
    def resolve_user_type_group(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, UserTypeGroup)

    @role_required([UserType.ADMIN.value, UserType.STORE.value, UserType.DEVELOPER.value])
    def resolve_user_type_groups(self, info, role, query=None, **kwargs):
        return resolve_user_type_groups(info, role=role, query=query)

    @permission_required('account')
    @role_required([UserType.ADMIN.value])
    def resolve_users(self, info, query=None, **kwargs):
        return resolve_users(info, query=query)


class UserAccountMutations(graphene.ObjectType):
    create_admin = AdminCreate.Field()
    create_admin_token = CreateAdminToken.Field()
    verify_admin = AdminVerify.Field()

    change_name = ChangeName.Field()
    change_email = ChangeEmail.Field()
    change_password = ChangePassword.Field()

    send_otp = SendOtp.Field()
    verify_otp = VerifyOtp.Field()