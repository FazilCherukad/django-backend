from celery import task

from core.custom.utils import create_thumbnails
from ..models import (
    Category,
    CategoryMedia,
    Brand,
    BrandMedia,
    Department,
    ProductTemplate,
    ProductTemplateMedia,
    ProductMasterMedia,
    ProductMaster
)


@task
def create_department_default_thumbnails(department_id, type):
    """Takes a category model,
    and creates the background image thumbnails for it."""
    create_thumbnails(
        pk=department_id, model=Department,
        size_set=type, image_attr=type)



@task
def create_category_default_thumbnails(category_id, type):
    """Takes a category model,
    and creates the background image thumbnails for it."""
    create_thumbnails(
        pk=category_id, model=Category,
        size_set=type, image_attr=type)

@task
def create_category_thumbnails(image_id):
    create_thumbnails(pk=image_id, model=CategoryMedia, size_set='image', image_attr='image')



@task
def create_brand_default_thumbnails(brand_id, type):
    """Takes a brand model,
    and creates the background image thumbnails for it."""
    create_thumbnails(
        pk=brand_id, model=Brand,
        size_set=type, image_attr=type)

@task
def create_brand_thumbnails(image_id):
    create_thumbnails(pk=image_id, model=BrandMedia, size_set='image', image_attr='image')


@task
def create_product_template_default_thumbnails(product_template_id, type):
    """Takes a brand model,
    and creates the background image thumbnails for it."""
    create_thumbnails(
        pk=product_template_id, model=ProductTemplate,
        size_set=type, image_attr=type)

@task
def create_product_template_thumbnails(image_id):
    create_thumbnails(pk=image_id, model=ProductTemplateMedia, size_set='image', image_attr='media')
    # items = ProductTemplateMedia.objects.filter(product_template=template_id)
    # for item in items:

@task
def create_product_master_default_thumbnails(product_master_id, type):
    """Takes a brand model,
    and creates the background image thumbnails for it."""
    create_thumbnails(
        pk=product_master_id, model=ProductMaster,
        size_set=type, image_attr=type)

@task
def create_product_master_thumbnails(image_id):
    create_thumbnails(pk=image_id, model=ProductMasterMedia, size_set='image', image_attr='media')


@task
def create_product_template_addon_thumbnails(id, type):
    create_thumbnails(pk=id, model=type, size_set='image', image_attr='image')

