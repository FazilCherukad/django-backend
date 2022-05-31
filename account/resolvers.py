import graphene_django_optimizer as gql_optimizer

from core.utils.utils import (
    filter_by_query_param
)
from . import models

USER_TYPE_GROUP_SEARCH_FIELDS = ('user_type')
USER_SEARCH_FIELDS = ('id')


def resolve_user_type_groups(info, query, role):
    qs = models.UserTypeGroup.objects.all()
    qs = qs.filter(user_type=role)
    qs = filter_by_query_param(qs, query, USER_TYPE_GROUP_SEARCH_FIELDS)
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)

def resolve_users(info, query):
    qs = models.Admin.objects.all().exclude(user=info.context.user.id)
    qs = filter_by_query_param(qs, query, USER_SEARCH_FIELDS)
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)