import django_filters
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from core.types.file_input import FilterInputObjectType
from core.custom.filter_utils import (
    template_filter_search,
    master_filter_search,
    category_filter_search,
    brand_filter_search,
    departments_filter_search,
    template_filter_by_categories,
    template_filter_by_brands,
    template_filter_by_departments,
    master_filter_by_categories,
    master_filter_by_brands,
    master_filter_by_departments,
    get_department_ids,
    get_category_ids
)
from .models import (
    ProductTemplate,
    ProductCategoryRelation,
    ProductBrandRelation,
    Category,
    ProductMaster,
    Brand
)

def category_filter_by_departments(qs, _, value):
    if value:
        ids = get_department_ids(value)
        qs = qs.filter(department__in=ids)
    return qs

def brand_filter_by_categories(qs, _, value):
    if value:
        ids = get_category_ids(value)
        product_ids = ProductCategoryRelation.object.filter(category__in=ids)\
            .values_list('product_template', flat=True) or []
        brand_ids = ProductBrandRelation.objects.filter(product_template__in=product_ids)
        qs = qs.filter(id__in=brand_ids)
    return qs


class TemplateFilter(django_filters.FilterSet):
    categories = GlobalIDMultipleChoiceFilter()
    brands = GlobalIDMultipleChoiceFilter()
    departments = GlobalIDMultipleChoiceFilter()
    search = django_filters.CharFilter()

    class Meta:
        model = ProductTemplate
        fields = [
            "categories",
            "brands",
            "departments"
        ]

class MasterFilter(django_filters.FilterSet):
    categories = GlobalIDMultipleChoiceFilter()
    brands = GlobalIDMultipleChoiceFilter()
    departments = GlobalIDMultipleChoiceFilter()
    search = django_filters.CharFilter()

    class Meta:
        model = ProductMaster
        fields = [
            "categories",
            "brands",
            "departments"
        ]

class CategoryFilter(django_filters.FilterSet):
    departments = GlobalIDMultipleChoiceFilter(method=category_filter_by_departments)
    search = django_filters.CharFilter(method=category_filter_search)

    class Meta:
        model = Category
        fields = [
            "departments",
            "search"
        ]

class BrandFilter(django_filters.FilterSet):
    categories = GlobalIDMultipleChoiceFilter(method=brand_filter_by_categories)
    search = django_filters.CharFilter(method=brand_filter_search)

    class Meta:
        model = Brand
        fields = [
            "categories",
            "search"
        ]

class DepartmentFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=departments_filter_search)

    class Meta:
        model = Brand
        fields = [
            "search"
        ]

class TemplateFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = TemplateFilter

class MasterFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = MasterFilter

class CategoryFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CategoryFilter

class BrandFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = BrandFilter

class DepartmentFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = DepartmentFilter