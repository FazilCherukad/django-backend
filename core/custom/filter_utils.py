from core.utils.utils import get_nodes

from products import types as product_types
from store_products import types as store_product_types
from search.backend.search import (
    search_categories,
    search_brands,
    search_departments
)

def template_filter_search(qs, _, value):
    """Search a product template"""
    # if value:
    #     products = seach_templates(value)
    #     qs &= products.distinct()
    return qs

def master_filter_search(qs, _, value):
    """Search a product master"""
    # if value:
    #     products = search_masters(value)
    #     qs &= products.distinct()
    return qs

def category_filter_search(qs, _, value):
    """Search a category"""
    if value:
        categories = search_categories(value)
        if isinstance(categories, tuple):
            categories = categories[0]
        qs &= categories.distinct()
    return qs

def brand_filter_search(qs, _, value):
    """Search a brand"""
    if value:
        brands = search_brands(value)
        if isinstance(brands, tuple):
            brands = brands[0]
        qs &= brands.distinct()
    return qs

def departments_filter_search(qs, _, value):
    """Search a department"""
    if value:
        departments = search_departments(value)
        if isinstance(departments, tuple):
            departments = departments[0]
        qs &= departments.distinct()
    return qs


def template_filter_by_categories(qs, _ , value):
    """Filter product template by list of categories"""
    ids = get_category_ids(value)
    qs = qs.filter(categories__category__id__in=ids)
    return qs

def template_filter_by_brands(qs, _, value):
    """Filter product template by list of brands"""
    ids = get_brand_ids(value)
    qs = qs.filter(brands__brand__id__in=ids)
    return qs

def template_filter_by_departments(qs, _, value):
    """Filter product template by list of departments"""
    ids = get_department_ids(value)
    qs = qs.filter(categories__category__department__id__in=ids)
    return qs

def master_filter_by_categories(qs, _, value):
    """Filter product master by list of categories"""
    ids = get_category_ids(value)
    qs = qs.filter(product_template__categories__category__id__in=ids)
    return qs

def master_filter_by_brands(qs, _, value):
    """Filter product master by list of brands"""
    ids = get_brand_ids(value)
    qs = qs.filter(product_template__brands__brand__id__in=ids)
    return qs

def master_filter_by_departments(qs, value):
    """Filter product master by list of departments"""
    ids = get_department_ids(value)
    qs = qs.filter(product_template__departments__department__id__in=ids)
    return qs


def get_category_ids(value):
    """Convert list of category global id's to pk's
        Also returns all the child category id's
    """
    if not value:
        return []
    categories = get_nodes(value, product_types.Category)
    categories = [
        category.get_descendants(include_self=True) for category in categories
    ]
    ids = [category.id for tree in categories for category in tree]
    return ids

def get_department_ids(value):
    """Convert list of departments global id's to pk's """
    if not value:
        return []
    departments = get_nodes(value, product_types.Department)
    ids = [
        department.id for department in departments
    ]
    return ids

def get_brand_ids(value):
    """Convert list of brand global id's to pk's """
    if not value:
        return []
    brands = get_nodes(value, product_types.Brand)
    ids = [
        brand.id for brand in brands
    ]
    return ids


def get_store_product_ids(value):
    """Convert list of store products global id's to pk's """
    if not value:
        return []
    store_products = get_nodes(value, store_product_types.StoreProduct)
    ids = [
        store_product.id for store_product in store_products
    ]
    return ids


