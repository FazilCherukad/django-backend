from django.template.defaultfilters import slugify
import graphene

from core.utils.decorators import permission_required, role_required
from core.utils.mutations import ModelMutation, ModelStatusChangeMutation
from core.types import Upload
from core.utils.utils import clean_seo_fields
from search.schema import SeoInput
from core.enums.enum import UserType
from ..utils.thumbnails import create_brand_default_thumbnails
from .. import models

class BrandMediaInput(graphene.InputObjectType):
    media = Upload(decription='Brand media file')
    media_type = graphene.ID(description='Brand media file type')
    sort_order = graphene.Int(description="Sort order for attribute values")


class BrandInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Brand name")
    note = graphene.String(description='Brand note.')
    url = graphene.String(description='Brand url.')
    icon = Upload(description='Icon image file.')
    large_icon = Upload(description='Large icon image file.')
    default_image = Upload(description='Default image file.')
    image_alt_text = graphene.String(description='Image alt text .')
    seo = SeoInput(description='Search engine optimization fields.')
    status = graphene.String(description="Brand set active/disabled/delete")
    # images = graphene.List(BrandMediaInput, description='List of brand media')

class BrandMixin:
    @classmethod
    def clean_code(cls, instance, cleaned_input, errors):
        if instance.pk:
            code = instance.code
        else:
            brand = models.Brand.all_objects.last()
            if brand:
                code = brand.code
                if 'B' in code:
                    code = int(code.split('B')[1])
                    code = code + 1
                    code = 'B' + str(code)
                else:
                    cls.add_error(
                        errors, 'code',
                        'Brand code could not generate.')
            else:
                code = 'B100000001'
        cleaned_input['code'] = code
        return cleaned_input

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

        query = models.Brand.all_objects.filter(slug=slug)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            cls.add_error(
                errors, 'name',
                'Brand already exists with this name.')

        clean_seo_fields(cleaned_input)
        cls.clean_code(instance, cleaned_input, errors)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get('icon'):
            create_brand_default_thumbnails.delay(instance.pk, 'icon')

        if cleaned_input.get('large_icon'):
            create_brand_default_thumbnails.delay(instance.pk, 'large_icon')

        if cleaned_input.get('default_image'):
            create_brand_default_thumbnails.delay(instance.pk, 'default_image')


class BrandCreate(BrandMixin, ModelMutation):
    class Arguments:
        input = BrandInput(
            required=True, description='Fields required to create a brand.')

    class Meta:
        description = 'Creates a new brand.'
        model = models.Brand

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)


class BrandUpdate(BrandMixin, ModelMutation):
    class Arguments:
        input = BrandInput(
            required=True, description='Fields required to update a brand.')
        id = graphene.ID(description='ID of the brand')

    class Meta:
        description = 'Update a new brand.'
        model = models.Brand

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)

class BrandChangeStatus(ModelStatusChangeMutation):

    class Arguments:
        status = graphene.String(description='New status of brand')
        id = graphene.ID(description='ID of the brand')
        cascade = graphene.Boolean(description='Option to delete via non-cascade')

    class Meta:
        description = 'Update a brand status.'
        model = models.Brand

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)


