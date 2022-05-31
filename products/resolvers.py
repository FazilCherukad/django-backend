import graphene_django_optimizer as gql_optimizer

from core.utils.utils import (
    filter_by_query_param,
    sort_queryset
)
from search.backend.search import  get_product_templates, get_product_masters
from store_products.filters import prepare_product_pojo_filter
from . import models
from .sorters import (
    TemplateSortField,
    MasterSortField
)

CATEGORY_SEARCH_FIELDS = ('name', 'slug', 'description', 'parent__name', 'code')
ATTRIBUTES_SEARCH_FIELDS = ('name', 'slug')
GROUP_ATTRIBUTES_SEARCH_FIELDS = ('name', 'slug')
DEPARTMENTS_SEARCH_FIELDS = ('name', 'slug', 'code')
BRANDS_SEARCH_FIELDS = ('name', 'slug', 'code')

def resolve_categories(info, level=None, **kwargs):
    qs = models.Category.objects.prefetch_related('children')
    if level is not None:
        qs = qs.filter(level=level)
    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)

def resolve_attributes(info, query=None):
    qs = models.Attribute.objects.all()
    qs = filter_by_query_param(qs, query, ATTRIBUTES_SEARCH_FIELDS)
    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)

def resolve_group_attributes(info, query=None):
    qs = models.AttributeGroup.objects.all()
    qs = filter_by_query_param(qs, query, GROUP_ATTRIBUTES_SEARCH_FIELDS)
    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)

def resolve_departments(info, query=None):
    qs = models.Department.objects.all()
    qs = filter_by_query_param(qs, query, DEPARTMENTS_SEARCH_FIELDS)
    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)

def resolve_brands(info, **kwargs):
    qs = models.Brand.objects.all()
    qs = qs.order_by('name')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)

def resolve_templates(info, **kwargs):
    pojo = prepare_product_pojo_filter(**kwargs)
    (qs, count) = get_product_templates(pojo)
    return (gql_optimizer.query(qs, info), count)

def resolve_product_masters(info, **kwargs):
    pojo = prepare_product_pojo_filter(**kwargs)
    (qs, count) = get_product_masters(pojo)
    return (gql_optimizer.query(qs, info), count)

def resolve_product_template_attributes(info, id):
    qs = models.ProductTemplateAttribute.objects.filter(product_template=id)
    qs = qs.order_by('id')
    qs = qs.distinct()
    return gql_optimizer.query(qs, info)
