from django.template.defaultfilters import slugify
import graphene

from core.utils.decorators import permission_required, role_required
from core.utils.mutations import ModelMutation, ModelStatusChangeMutation
from core.types import Upload
from core.utils.utils import clean_seo_fields
from search.schema import SeoInput
from core.enums.enum import UserType
from core.enums.grapheneEnum import Maturity, Priority
from ..utils.thumbnails import create_category_default_thumbnails
from .. import models

class CategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True, description="Category name")
    note = graphene.String(description='Category note.')
    url = graphene.String(description='Category url.')
    icon = Upload(description='Icon image file.')
    large_icon = Upload(description='Large icon image file.')
    background_color = graphene.String(description='Background Color.')
    default_image = Upload(description='Default image file.')
    image_alt_text = graphene.String(description='Image alt text .')
    seo = SeoInput(description='Search engine optimization fields.')
    parent = graphene.ID(description='Category parent id.')
    department = graphene.ID(description='Category department id.')
    maturity = Maturity(description='Show a category by maturity')
    priority = Priority(description='A category priority')
    status = graphene.String(description="Category set active/disabled/delete")

class CategoryMixin:

    @classmethod
    def clean_code(cls, instance, cleaned_input, errors):
        if instance.pk:
            code = instance.code
        else:
            category = models.Category.all_objects.last()
            if category:
                code = category.code
                if 'C' in code:
                    code = int(code.split('C')[1])
                    code = code + 1
                    code = 'C' + str(code)
                else:
                    cls.add_error(
                        errors, 'code',
                        'Category code could not generate.')
            else:
                code = 'C100000001'
        cleaned_input['code'] = code
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get('icon'):
            create_category_default_thumbnails.delay(instance.pk, 'icon')

        if cleaned_input.get('large_icon'):
            create_category_default_thumbnails.delay(instance.pk, 'large_icon')

        if cleaned_input.get('default_image'):
            create_category_default_thumbnails.delay(instance.pk, 'default_image')

    @classmethod
    def clean_input(cls, info, instance, input, errors):
        cleaned_input = super().clean_input(info, instance, input, errors)

        if 'name' in cleaned_input:
            slug = slugify(cleaned_input['name'])
        elif instance.pk:
            slug = instance.slug
        else:
            cls.add_error(errors, 'name', 'This field cannot be blank.')
            return cleaned_input
        cleaned_input['slug'] = slug

        query = models.Category.all_objects.filter(slug=slug)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            pass
            # cls.add_error(
            #     errors, 'name',
            #     'Category already exists with this name.')

        if not input.get('maturity'):
            input['maturity'] = Maturity.MATURED.value
        if not input.get('priority'):
            input['priority'] = Priority.MEDIUM.value

        clean_seo_fields(cleaned_input)
        cls.clean_code(instance, cleaned_input, errors)
        return cleaned_input


class CategoryCreate(CategoryMixin,ModelMutation):
    class Arguments:
        input = CategoryInput(
            required=True, description='Fields required to create a category.')

    class Meta:
        description = 'Creates a new category.'
        model = models.Category

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)

class CategoryUpdate(CategoryMixin, ModelMutation):

    class Arguments:
        input = CategoryInput(
            required=True, description='Fields required to update a category.')
        id = graphene.ID(description='Category ID to be update')

    class Meta:
        description = 'Creates a new category.'
        model = models.Category

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)

class CategoryChangeStatus(ModelStatusChangeMutation):

    class Arguments:
        status = graphene.String(description='New status of category')
        id = graphene.ID(description='ID of the category')
        cascade = graphene.Boolean(description='Option to delete via non-cascade')

    class Meta:
        description = 'Update a category status.'
        model = models.Category

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)


