from django.template.defaultfilters import slugify
from django.db import Error as DBError, transaction
import graphene

from core.utils.decorators import permission_required, role_required
from core.utils.mutations import ModelMutation, ModelStatusChangeMutation
from core.types import Upload
from core.utils.utils import validate_image_file, clean_seo_fields
from search.schema import SeoInput
from uom.types import UOM
from core.enums.grapheneEnum import ProductPackingType
from refs.types import Country
from refs import models as refsModel
from core.enums.enum import UserType, Status
from ..utils.thumbnails import (
    create_product_template_default_thumbnails,
    create_product_template_addon_thumbnails,
    create_product_template_thumbnails,
    create_product_master_default_thumbnails,
    create_product_master_thumbnails
)
from ..types import (
    ProductTemplate,
    Brand,
    Category,
    ProductTemplateAttributeGroupValue,
    Attribute,
    AttributeValue,
    ProductMaster,
    AttributeGroupItem,
    ProductTemplateDescription,
    ProductTemplateNutrition,
    ProductTemplateIngredient,
    ProductTemplateHowToUse,
    ProductTemplateCautionMessage,
    ProductTemplateCertification,
    ProductTemplateAttribute,
    ProductTemplateAttributeGroup,
    ProductTemplatePolicy,
    ProductTemplateInclude,
    ProductTemplateRelatedProduct,
    ProductTemplateMedia,
    ProductMasterMedia
)
from .. import models

class CheckBarcodeExist(ModelMutation):

    exist = graphene.Boolean(description='Is barcode is existing')

    class Arguments:
        barcode = graphene.String(description="Barcode to check exist")

    class Meta:
        description = 'Check barcode exist'
        model = models.ProductMaster

    @classmethod
    def mutate(cls, root, info, barcode):
        try:
            instance = models.ProductMaster.objects.get(barcode=barcode)
            return CheckBarcodeExist(productMaster=instance, exist=True)
        except models.ProductMaster.DoesNotExist:
            return CheckBarcodeExist(productMaster=None, exist=False)


class ProductBrandRelationInput(graphene.InputObjectType):
    brand = graphene.ID(description='Product template brand ids.')

class ProductCategoryRelationInput(graphene.InputObjectType):
    category = graphene.ID(description='Product template brand ids.')


class ProductTemplateMediaInput(graphene.InputObjectType):
    id = graphene.ID(description='ID of the template image')
    media = Upload(required=True, description='Image.')

class ProductMasterAttributeValueInput(graphene.InputObjectType):
    product_master = graphene.ID(description='Product master ID')
    attribute = graphene.ID(description='Attribute ID')
    product_template_attribute = graphene.ID(description='Product template attribute assigned ID')
    attribute_value = graphene.ID(description='Attribute value corresponding to ID')


class ProductMasterMediaInput(graphene.InputObjectType):
    id = graphene.ID(description='ID of the template image')
    media = Upload(required=True, description='Image.')
    sort_order = graphene.Int(description="Sort order for attribute values")


class ProductInput(graphene.InputObjectType):
    country = graphene.ID(description='IDs of country group')

class ProductMasterPackItemInput(graphene.InputObjectType):
    item = graphene.ID(description='Product master ID')
    qty = graphene.Float(description="Product quantity in pack")
    value_type = graphene.String(description="Product value type")

class ProductMasterInput(graphene.InputObjectType):
    id = graphene.ID(description='Product master ID')
    product_master = graphene.ID(description='Product master ID to update')
    product_template = graphene.ID(description='Product template ID')
    name = graphene.String(description='Product master name')
    sub_name = graphene.String(description='Product master name')
    barcode = graphene.String(description='Product master barcode')
    model = graphene.String(description='Product master model number')
    description = graphene.String(description='Product master description')
    url = graphene.String(description='Product master url')
    weight = graphene.Float(description='Product master weight')
    weight_unit = graphene.ID(description='Product master weight unit')
    parent = graphene.ID(description='Product master parent ID')
    icon = Upload(description='Icon image file.')
    large_icon = Upload(description='Large icon image file.')
    default_image = Upload(description='Default image file.')
    image_alt_text = graphene.String(description='Image alt text .')
    seo = SeoInput(description='Search engine optimization fields.')
    packing_type = graphene.String(description='Product master product packing type eg: Single,Combo')
    status = graphene.String(description='Category active.')
    attributes = graphene.List(ProductMasterAttributeValueInput, description='Product master attribute value list')
    products = graphene.List(ProductInput, description='List of initial available countries')
    images = graphene.List(ProductMasterMediaInput, description='List of product template images')
    remove_images = graphene.List(graphene.ID, description='List of image IDs to delete')
    pack_items = graphene.List(ProductMasterPackItemInput, description="List Of product pack items")


class ProductMasterMixin:

    @classmethod
    def clean_master_code(cls, instance, cleaned_input, errors, index=None):
        product_master = models.ProductMaster.all_objects.last()
        if instance.pk:
            code = instance.code
        else:
            if product_master:
                code = product_master.code
                if 'M' in code:
                    code = int(code.split('M')[1])
                    if index:
                        code = code + index
                    else:
                        code = code + 1
                    code = 'M' + str(code)
                else:
                    cls.add_error(
                        errors, 'code',
                        'Product master code could not generate.')
            else:
                code = 'M100000001'
        cleaned_input['code'] = code
        return cleaned_input

    @classmethod
    def clean_pack_item(cls, info, cleaned_input, errors, index=None):
        pack_items = cleaned_input.get('pack_items') or []
        for item in pack_items:
            item['item'] = cls.get_node_or_error(info, item['item'], errors, 'id', ProductMaster)
        return cleaned_input

    @classmethod
    def clean_seo_fields(cls, instance, cleaned_input, errors):
        template = cleaned_input.get('product_template')
        template_seo_title = ''
        template_seo_keywords = []
        template_seo_description = ''
        if template:
            template_seo_title = template.seo_title
            template_seo_keywords = template.seo_keywords
            template_seo_description = template.seo_description

        seo_keywords = cleaned_input.get('seo_keywords') or []
        seo_title = cleaned_input.get('seo_title')
        seo_description = cleaned_input.get('seo_description')

        if instance.pk:
            existing_keywords = instance.seo_keywords
            for seo_keyword in seo_keywords:
                if seo_keyword not in existing_keywords:
                    existing_keywords.append(seo_keyword)
            cleaned_input['seo_keywords'] = existing_keywords
        else:
            for template_seo_keyword in template_seo_keywords:
                if template_seo_keyword not in seo_keywords:
                    seo_keywords.append(template_seo_keyword)
            cleaned_input['seo_keywords'] = seo_keywords
            if seo_title is None:
                cleaned_input['seo_title'] = template_seo_title
            if seo_description is None:
                cleaned_input['seo_description'] = template_seo_description
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def clean_master_images(cls, info, cleaned_input, errors):
        newImages = []
        images = cleaned_input.get('images') or []
        for image in images:
            media = {}
            value = info.context.FILES.get(image['media'])
            media['media'] = value
            validate_image_file(cls, value, 'media', errors)
            if image.get('id'):
                image = cls.get_node_or_error(info, image.get('id'), errors, field='id', only_type=ProductMasterMedia)
                media['image'] = image
            newImages.append(media)
        cleaned_input['images'] = newImages
        return cleaned_input


    @classmethod
    def check_all_attributes_filled(cls, product_master, cleaned_input,errors):
        """Checking all the attributes assigned for template is provided for master"""
        product_template = cleaned_input.get('product_template')
        template_attributes = product_template.attributes.values_list('id', flat=True)
        master_attributes = cleaned_input.get('attributes') or []
        existing_attributes = product_master.attributes.values_list('product_template_attribute', flat=True) or []

        for template_attribute in template_attributes:
            found = False
            if template_attribute in existing_attributes:
                continue;
            for master_attribute in master_attributes:
                if template_attribute == master_attribute.get('product_template_attribute').id:
                    found =True
                    break
            if found: continue
            cls.add_error(errors, 'attributes', 'Provide all the attributes defined for template')
            break

    @classmethod
    def clean_attributes(cls, info, cleaned_input, product_master, errors):
        """Clean attribute with checking template assigned attribute
        Check attribute already assigned to a master product
        check attribute and its values are proper fields"""

        if not 'attributes' in cleaned_input:
            return cleaned_input
        attributes = cleaned_input['attributes']
        newAttributes = []
        existing_values = product_master.attributes.values_list('product_template_attribute', flat=True)
        for attribute_data in attributes:
            product_template_attribute = attribute_data['product_template_attribute']
            attribute = attribute_data['attribute']
            attribute_value = attribute_data['attribute_value']

            product_template_attribute_obj = cls.get_node_or_error(
                info, product_template_attribute, errors, 'id', ProductTemplateAttribute)
            if not product_template_attribute_obj or product_template_attribute_obj.id in existing_values:
                # msg = (
                #         'Attribute %s already exists within this product master.' %
                #         attribute_data['product_template_attribute'])
                # cls.add_error(errors, 'attributes', msg)
                continue
            attribute_data['product_template_attribute'] = product_template_attribute_obj

            new_attribute = cls.get_node_or_error(
                info, attribute, errors, 'id', Attribute)
            attribute = product_template_attribute_obj.attribute
            if not new_attribute or not attribute or new_attribute != attribute:
                msg = (
                    'Attribute not found.')
                cls.add_error(errors, 'attribute', msg)
                continue
            attribute_data['attribute'] = attribute

            existing_attribute_values = attribute.values.values_list('id', flat=True)
            attribute_value_obj = cls.get_node_or_error(
                info, attribute_value, errors, 'id', AttributeValue)
            if not attribute_value_obj or not attribute_value_obj.id in existing_attribute_values :
                msg = (
                    'Attribute value not found.')
                cls.add_error(errors, 'attribute', msg)
                continue
            attribute_data['attribute_value'] = attribute_value_obj
            attribute_data.pop('attribute', None)
            newAttributes.append(attribute_data)

        cleaned_input['attributes'] = newAttributes
        return cleaned_input


    @classmethod
    def clean_product(cls, info, cleaned_input, instance, errors):
        products = []
        if 'products' in cleaned_input:
            for product in cleaned_input['products']:
                country = cls.get_node_or_error(
                    info, product['country'], errors, 'id', Country)
                if country:
                    if instance.pk:
                        query = models.Product.objects.filter(country=country.id,
                                                              product_master=instance.id)
                        if not query.exists():
                            product['country'] = country
                            products.append(product)
                    else:
                        product['country'] = country
                        products.append(product)

                else:
                    cls.add_error(
                        errors, 'country',
                        'Country  not found.')

        else:
            countries = []
            products = []
            for country in countries:
                product = {}
                if instance.pk:
                    query = models.Product.objects.filter(country=country.id,
                                                          product_master=instance.id)
                    if not query.exists():
                        product['country'] = country
                        products.append(product)
                else:
                    product['country'] = country
                    products.append(product)

        cleaned_input['products'] = products
        return cleaned_input

    @classmethod
    def clean_master_input(cls, info, instance, input, errors, index=None):
        cleaned_input = super().clean_input(info, instance, input, errors, ProductMasterInput)
        cls.clean_master_code(instance, cleaned_input, errors, index)

        if 'name' in cleaned_input and cleaned_input['name'] != '':
            slug = slugify(cleaned_input['name'])

        else:
            slug = cleaned_input.get('code')
            # cls.add_error(errors, 'name', 'This field cannot be blank.')
            # return cleaned_input

        if instance.pk:
            slug = instance.slug
        cleaned_input['slug'] = slug

        query = models.ProductMaster.objects.filter(slug=slug)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            cls.add_error(
                errors, 'name',
                'Product master already exists with this name.')


        if 'barcode' in cleaned_input and cleaned_input['barcode'] != '':
            barcode = (cleaned_input['barcode'])
        elif instance.pk:
            barcode = instance.barcode
        else:
            barcode = cleaned_input['code']
        cleaned_input['barcode'] = barcode

        new_query = models.ProductMaster.objects.filter(barcode=barcode)
        new_query = new_query.exclude(pk=getattr(instance, 'pk', None))
        if new_query.exists():
            cls.add_error(
                errors, 'name',
                'Product master already exists with this barcode.')


        cls.clean_seo_fields(instance, cleaned_input, errors)
        cls.clean_pack_item(info, cleaned_input, errors)
        return cleaned_input

class ProductTemplateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Product template name")
    model = graphene.String(description='Product template model.')
    description = graphene.String(description='Product template description.')
    url = graphene.String(description='Product template url.')
    icon = Upload(description='Icon image file.')
    large_icon = Upload(description='Large icon image file.')
    default_image = Upload(description='Default image file.')
    image_alt_text = graphene.String(description='Image alt text .')
    seo = SeoInput(description='Search engine optimization fields.')
    unit_id = graphene.ID(description='Product template unit id.')
    selling_unit = graphene.ID(description='Product template selling unit id.')
    status = graphene.String(description='Product template active.')
    product_type = graphene.ID(description='Product template type like Food')
    product_sub_type = graphene.ID(description='Product template sub type like Veg Food')
    categories = graphene.List(ProductCategoryRelationInput, description='Product template categories.')
    brands = graphene.List(ProductBrandRelationInput, description='Product template brands.')
    images = graphene.List(ProductTemplateMediaInput, description='List of product template images')
    masters = graphene.List(ProductMasterInput, description='Master Field required to create single variant template')
    remove_images = graphene.List(graphene.ID, description='List of image IDs to delete')

class ProductTemplateMixin:

    @classmethod
    def clean_code(cls, instance, cleaned_input, errors):
        if instance.pk:
            code = instance.code
        else:
            product_template = models.ProductTemplate.all_objects.last()
            if product_template:
                code = product_template.code
                if 'T' in code:
                    code = int(code.split('T')[1])
                    code = code + 1
                    code = 'T' + str(code)
                else:
                    cls.add_error(
                        errors, 'code',
                        'Product template code could not generate.')
            else:
                code = 'T100000001'
        cleaned_input['code'] = code
        return cleaned_input

    @classmethod
    def clean_template_input(cls, info, instance, input, errors, brands):
        cleaned_input = super().clean_input(info, instance, input, errors)

        if 'name' in cleaned_input:
            slug = slugify(cleaned_input['name'])
            if brands and len(brands)>0 and cleaned_input['name']:
                brand = brands[0]
                brand_name = brand.slug
                slug = brand_name+slug
        else:
            cls.add_error(errors, 'name', 'This field cannot be blank.')
            return cleaned_input

        if instance.pk:
            slug = instance.slug

        cleaned_input['slug'] = slug

        query = models.ProductTemplate.all_objects.filter(slug=slug)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            cls.add_error(
                errors, 'name',
                'Product template already exists with this name.')

        unit_id = input.get('unit_id')
        if unit_id:
            unit = cls.get_node_or_error(
                info, unit_id, errors, field='id', only_type=UOM)
            if unit:
                cleaned_input['uom'] = unit

        clean_seo_fields(cleaned_input)
        cls.clean_code(instance, cleaned_input, errors)
        if cleaned_input.get('masters'):
            masters = cleaned_input.get('masters') or []
            masterArray = []
            for master_input in masters:
                master = models.ProductMaster()
                master_cleaned_input = cls.clean_master_input(info, master, master_input, errors)
                cls.clean_product(info, master_cleaned_input, master, errors)
                master = cls.construct_instance(master, master_cleaned_input)
                cls.clean_instance(master, errors)
                masterArray.append(master_cleaned_input)
            cleaned_input['masters'] = masterArray
        return cleaned_input

    @classmethod
    def clean_brand_relations(cls, info, instance, input, errors):
        brandArray = []
        brands = input.get('brands') or []
        for item in brands:
            id = item.brand
            brand = cls.get_node_or_error(info, id, errors, 'id', Brand)
            query = models.ProductBrandRelation.objects.filter(brand=brand.id, product_template=instance.id)
            if query.exists():
                pass
            else:
                brandArray.append(brand)
        return brandArray

    @classmethod
    def clean_category_relations(cls, info, instance, input, errors):
        categoryArray = []
        categories = input.get('categories') or []
        for item in categories:
            id = item.category
            category = cls.get_node_or_error(info, id, errors, field='id', only_type=Category)
            if instance.pk:
                query = models.ProductCategoryRelation.objects.filter(category=category.id,
                                                                      product_template=instance.pk)
                if query.exists():
                    pass
                else:
                    categoryArray.append(category)
            else:
                categoryArray.append(category)
        return categoryArray

    @classmethod
    def clean_images(cls, info, cleaned_input, errors):
        newImages = []
        images = cleaned_input.get('images') or []
        for image in images:
            media = {}
            value = info.context.FILES.get(image['media'])
            media['media'] = value
            validate_image_file(cls, value, 'media', errors)
            if image.get('id'):
                image = cls.get_node_or_error(info, image.get('id'), errors, field='id', only_type=ProductTemplateMedia)
                media['image'] = image
            newImages.append(media)
        cleaned_input['images'] = newImages
        return cleaned_input


    @classmethod
    def save(cls, info, instance, cleaned_input, categories, brands):
        instance.save()
        if cleaned_input.get('icon'):
            create_product_template_default_thumbnails.delay(instance.pk, 'icon')

        if cleaned_input.get('large_icon'):
            create_product_template_default_thumbnails.delay(instance.pk, 'large_icon')

        if cleaned_input.get('default_image'):
            create_product_template_default_thumbnails.delay(instance.pk, 'default_image')

        for category in categories:
            instance.categories.create(category=category)

        for brand in brands:
            instance.brands.create(brand=brand)

        if cleaned_input.get('masters'):
            masters = cleaned_input.get('masters') or []
            for master_input in masters:
                packing_type = ProductPackingType.SINGLE.value
                if master_input.get('packing_type'):
                    packing_type = master_input.get('packing_type')
                master = instance.masters.create(
                    name=master_input.get('name'),
                    sub_name=master_input.get('sub_name'),
                    slug=master_input.get('slug'),
                    model=master_input.get('model'),
                    barcode=master_input.get('barcode'),
                    weight=master_input.get('weight'),
                    description=master_input.get('description'),
                    weight_unit=master_input.get('weight_unit'),
                    code=master_input.get('code'),
                    seo_title=master_input.get('seo_title'),
                    seo_description=master_input.get('seo_description'),
                    seo_keywords=master_input.get('seo_keywords'),
                    packing_type=packing_type
                )
                products = master_input.get('products') or []
                pack_items = master_input.get('pack_items') or []
                for pack_item in pack_items:
                    master.product_master_pack_items.create(**pack_item)
                for product in products:
                    master.products.create(**product)


    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        images = cleaned_data.get('images') or []
        remove_images = cleaned_data.get('remove_images') or []
        for image in images:
            if image.get('image'):
                oldImage = image.get('image')
                oldImage.media = image.get('media')
                oldImage.save()
                create_product_template_thumbnails.delay(oldImage.pk)
            else:
                image = instance.images.create(**image)
                create_product_template_thumbnails.delay(image.pk)

        for image in remove_images:
            image.delete()


class ProductTemplateCreate(ProductMasterMixin, ProductTemplateMixin, ModelMutation):

    class Arguments:
        input = ProductTemplateInput(
            required=True, description='Fields required to create a product template.')

    class Meta:
        description = 'Creates a new product template.'
        model = models.ProductTemplate

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input):
        errors = []
        instance = models.ProductTemplate()

        brands = cls.clean_brand_relations(info, instance, input, errors)
        categories = cls.clean_category_relations(info, instance, input, errors)

        cleaned_input = cls.clean_template_input(info, instance, input, errors, brands)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        cls.clean_images(info, cleaned_input, errors)


        if errors:
            return ProductTemplateCreate(errors=errors)
        try:
            with transaction.atomic():
                cls.save(info, instance, cleaned_input, categories, brands)
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateCreate(errors=errors)

        return ProductTemplateCreate(productTemplate=instance, errors=errors)




class ProductTemplateUpdate(ProductTemplateMixin, ModelMutation):

    class Arguments:
        input = ProductTemplateInput(
            required=True, description='Fields required to update a product template.')
        id = graphene.ID(description='ID of product template')

    class Meta:
        description = 'update a  product template.'
        model = models.ProductTemplate

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, id):
        errors = []
        instance = cls.get_node_or_error(info, id, errors, 'id', ProductTemplate)
        brands = cls.clean_brand_relations(info, instance, input, errors)
        categories = cls.clean_category_relations(info, instance, input, errors)
        cleaned_input = cls.clean_template_input(info, instance, input, errors, brands)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        cls.clean_images(info, cleaned_input, errors)

        if errors:
            return ProductTemplateUpdate(errors=errors)

        try:
            with transaction.atomic():
                cls.save(info, instance, cleaned_input, categories, brands)
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateCreate(errors=errors)
        return ProductTemplateUpdate(productTemplate=instance, errors=errors)



class ProductTemplateChangeStatus(ModelStatusChangeMutation):

    class Arguments:
        status = graphene.String(description='New status of product template')
        id = graphene.ID(description='ID of the product template')
        cascade = graphene.Boolean(description='Option to delete via non-cascade')

    class Meta:
        description = 'Update a product template status.'
        model = models.ProductTemplate

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)

class ProductTemplateAttributeGroupValueInput(graphene.InputObjectType):
    id = graphene.String(description='Attribute group item value id')
    attribute_group_item = graphene.ID(description='Attribute group item ID')
    value = graphene.String(description='Attribute group item value')

class ProductTemplateAttributeGroupInput(graphene.InputObjectType):
    id = graphene.ID(description='ID of the product template group attribute')
    attribute_group = graphene.ID(description='Attribute group ID')
    items = graphene.List(ProductTemplateAttributeGroupValueInput, description='Group attribute items with value')
    product_template = graphene.ID(description='Product template ID')
    sort_order = graphene.Int(description="Sort order for attribute values")



class ProductTemplateAttributeGroupCreate(ModelMutation):

    productTemplateAttributeGroups = graphene.List(ProductTemplateAttributeGroup)

    class Arguments:

        input = graphene.List(ProductTemplateAttributeGroupInput,
                              description='Required fields for product template attribute group')
        removeItems = graphene.List(graphene.ID,
                                    description='IDs to delete')

    class Meta:
        description = 'Create a new product template attribute group'
        model = models.ProductTemplateAttributeGroup

    @classmethod
    def clean_items(cls, info, cleaned_input, instance, errors):

        values_input = cleaned_input['items']
        items = []

        existing_values = instance.items.values_list('attribute_group_item', flat=True)
        for value_data in values_input:
            item = cls.get_node_or_error(info, value_data['attribute_group_item'], errors, 'id',
                                                         AttributeGroupItem)

            if item.id in existing_values:
                old = cls.get_node_or_error(info, value_data['id'], errors, 'id',
                                            ProductTemplateAttributeGroupValue)
                if old:
                    value_data['id'] = old.id
            value = value_data['value']
            if not value or len(value) < 1:
                cls.add_error(errors, 'value', 'attribute group item value not found')
            value_data['attribute_group_item'] = item
            items.append(value_data)

        cleaned_input['items'] = items
        return cleaned_input


    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        data = []
        removeInstances=[]

        for cleaned_input in input:
            if cleaned_input.get('id'):
                instance = cls.get_node_or_error(info, cleaned_input.get('id'), errors, 'id',
                                                 ProductTemplateAttributeGroup)
            else:
                instance = models.ProductTemplateAttributeGroup()

            cleaned_input = cls.clean_input(info, instance, cleaned_input, errors,
                                            ProductTemplateAttributeGroupInput)
            cleaned_input = cls.clean_items(info, cleaned_input, instance, errors)
            instance = cls.construct_instance(instance, cleaned_input)
            cls.clean_instance(instance, errors)
            data.append((instance, cleaned_input))
            instances.append(instance)

        for remove_data in removeItems:
            instance = cls.get_node_or_error(info, remove_data, errors, 'id',
                                             ProductTemplateAttributeGroup)
            if instance:
                removeInstances.append(instance)
        if errors:
            return ProductTemplateAttributeGroupCreate(errors=errors)
        cls.save(info, data, removeInstances)
        return ProductTemplateAttributeGroupCreate(productTemplateAttributeGroups=instances, errors=errors)

    @classmethod
    def save(cls, info, instances, remove_items):
        for instance, cleaned_input in instances:
            instance.save()
            items = cleaned_input.get('items') or []
            for item in items:
                if item.get('id'):
                    old = instance.items.get(pk=item.get('id'))
                    old.attribute_group_item = item.get('attribute_group_item')
                    old.value = item.get('value')
                    old.save()
                else:
                    instance.items.create(**item)
        for remove_item in remove_items:
            remove_item.delete()

class ProductTemplateAttributeInput(graphene.InputObjectType):
    new_items = graphene.List(graphene.ID, description="Fields required for assign new attribute for product template")
    remove_items = graphene.List(graphene.ID, description="Fields required delete a assigned attribute")


class ProductTemplateAttributeCreate(ModelMutation):

    productTemplateAttributes = graphene.List(ProductTemplateAttribute)

    class Arguments:
        product_template = graphene.ID(description='Product template ID')
        input = ProductTemplateAttributeInput(description='Field required to update product template attribute')

    class Meta:
        description = 'Create a new relation between product template and attribute'
        model = models.ProductTemplateAttribute

    @classmethod
    def clean_attribute(cls, info, input, product_template, errors):
        values = []
        new_items = input.get('new_items') or []
        qty_attribute_count = 0
        count = product_template.attributes.filter(attribute__qty_attribute=True).count()
        qty_attribute_count = qty_attribute_count + count
        for item in new_items:
            value = {}
            attr = cls.get_node_or_error(
                info, item, errors, 'id', Attribute)

            if not attr:
                cls.add_error(errors, 'attribute', 'attribute not found')
            else:
                if attr.qty_attribute:
                    qty_attribute_count = qty_attribute_count + 1
            value['attribute'] = attr
            value['product_template'] = product_template
            query = models.ProductTemplateAttribute.objects.\
                filter(attribute=attr.id, product_template=product_template.id)
            if not query.exists():
                values.append(value)
        if qty_attribute_count > 1:
            cls.add_error(errors, 'attribute qty', 'product only accept single quantity attribute')
        return values

    @classmethod
    def clean_remove_attributes(cls, info, input, errors):
        items = []
        remove_items = input.get('remove_items') or []
        for item in remove_items:
            product_template_attribute = cls.get_node_or_error(
                info, item, errors, 'id', ProductTemplateAttribute)
            if product_template_attribute:
                items.append(product_template_attribute)
            else:
                cls.add_error(errors, 'product_template_attribute', 'product template attribute not existing')

        return items

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, product_template):
        errors = []
        instances = []
        product_template = cls.get_node_or_error(
            info, product_template, errors, 'id', ProductTemplate)
        if not product_template:
            cls.add_error(errors, 'product_template', 'product template not existing')
        remove_items = cls.clean_remove_attributes(info, input, errors)
        input = cls.clean_attribute(info, input, product_template, errors)

        for cleaned_input in input:
            try:
                instance = models.ProductTemplateAttribute.objects.get\
                    (attribute=cleaned_input.get('attribute').id,
                    product_template=cleaned_input.get('product_template').id)
            except models.ProductTemplateAttribute.DoesNotExist:
                instance = models.ProductTemplateAttribute()
            instance = cls.construct_instance(instance, cleaned_input)
            cls.clean_instance(instance, errors)
            instances.append(instance)
        if errors:
            return ProductTemplateAttributeCreate(errors=errors)
        cls.save(info, instances, remove_items)
        return ProductTemplateAttributeCreate(productTemplateAttributes=instances, errors=errors)

    @classmethod
    def save(cls, info, instances, remove_items):
        for instance in instances:
            instance.save()

        for remove_item in remove_items:
            remove_item.delete()


class ProductTemplateDescriptionInput(graphene.InputObjectType):
    id = graphene.ID(description='ID of the description to update')
    title = graphene.String(description='Description title')
    description = graphene.String(description='Description content')
    sort_order = graphene.Int(description="Sort order for attribute values")
    image = Upload(description='If any image for description')
    product_template = graphene.ID(description='Product template ID')

class ProductTemplateDescriptionCreate(ModelMutation):

    productTemplateDescriptions = graphene.List(ProductTemplateDescription)

    class Arguments:
        input = graphene.List(ProductTemplateDescriptionInput,
                              description='Fields required to create product template description')
        removeItems = graphene.List(graphene.ID,
                                    description='IDs to delete')

    class Meta:
        description = 'Create a list of new product template description'
        model = models.ProductTemplateDescription

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        data = []
        instances = []
        removeInstances = []
        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateDescription)
                    else:
                        instance = models.ProductTemplateDescription()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateDescriptionInput)
                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    data.append((instance, cleaned_input))
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id',
                                                     ProductTemplateDescription)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateDescriptionCreate(errors=errors)

                cls.save(info, data, removeInstances)
                return ProductTemplateDescriptionCreate(errors=errors, productTemplateDescriptions=instances)

        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateDescriptionCreate(errors=errors)


    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance, cleaned_input in instances:
            instance.save()
            if cleaned_input.get('image'):
                create_product_template_addon_thumbnails.delay(instance.pk, models.ProductTemplateDescription)
        for removeInstance in removeInstances:
            removeInstance.delete()


class ProductTemplateNutritionInput(graphene.InputObjectType):
    nutrition = graphene.String(description='Product template nutrition description')
    value = graphene.String(description='Product template nutrition description have any value')
    sort_order = graphene.Int(description="Sort order for attribute values")
    product_template = graphene.ID(description='Product template ID')
    id = graphene.ID(description='Product template nutrition id')

class ProductTemplateNutritionCreate(ModelMutation):

    productTemplateNutritions = graphene.List(ProductTemplateNutrition)

    class Arguments:
        input = graphene.List(ProductTemplateNutritionInput,
                              description='Fields required for create to list of nutrition')
        removeItems = graphene.List(graphene.ID, description='List of items to delete')

    class Meta:
        description = 'Create a list of nutrition for product template'
        model = models.ProductTemplateNutrition

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        removeInstances = []
        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateNutrition)
                    else:
                        instance = models.ProductTemplateNutrition()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateNutritionInput)
                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id',
                                                     ProductTemplateNutrition)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateNutritionCreate(errors=errors)

                cls.save(info, instances, removeInstances)
                return ProductTemplateNutritionCreate(productTemplateNutritions=instances, errors=errors)

        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateNutritionCreate(errors=errors)

    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance in instances:
            instance.save()
        for removeInstance in removeInstances:
            removeInstance.delete()

class ProductTemplateIngredientInput(graphene.InputObjectType):
    ingredient = graphene.String(description='Product template ingredient')
    value = graphene.String(description='Product template ingredient have any value')
    sort_order = graphene.Int(description="Sort order for attribute values")
    product_template = graphene.ID(description='Product template ID')
    id = graphene.ID(description='Product template ingrediant id')

class ProductTemplateIngredientCreate(ModelMutation):

    productTemplateIngredients = graphene.List(ProductTemplateIngredient)

    class Arguments:

        input = graphene.List(ProductTemplateIngredientInput, description='Fields required to create list ingredients')
        removeItems = graphene.List(graphene.ID, description='List of ids to delete')

    class Meta:
        description = 'Create a list of ingredient of a product template'
        model = models.ProductTemplateIngredient

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        removeInstances = []

        try:
            with transaction.atomic():

                for cleaned_data in input:

                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateIngredient)
                    else:
                        instance = models.ProductTemplateIngredient()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateIngredientInput)

                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id',
                                                     ProductTemplateIngredient)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateIngredientCreate(errors=errors)
                cls.save(info, instances, removeInstances)
                return ProductTemplateIngredientCreate(productTemplateIngredients=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateIngredientCreate(errors=errors)


    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance in instances:
            instance.save()
        for removeInstance in removeInstances:
            removeInstance.delete()

class ProductTemplateHowToUseInput(graphene.InputObjectType):
    sort_order = graphene.Int(description="Sort order for attribute values")
    title = graphene.String(description='Title for how to use')
    description = graphene.String(description='A detailed note for how to use')
    image = Upload(description='How to use step by step image')
    product_template = graphene.ID(description='Product template ID')
    id = graphene.ID(description='Product template how to use id')

class ProductTemplateHowToUseCreate(ModelMutation):

    productTemplateHowToUses = graphene.List(ProductTemplateHowToUse)

    class Arguments:
        input = graphene.List(ProductTemplateHowToUseInput,
                              description='Fields required to create list of how to use step')
        removeItems = graphene.List(graphene.ID, description='List of ids to delete')

    class Meta:
        description = 'Create a list of how to use of a product template'
        model = models.ProductTemplateHowToUse

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        data = []
        removeInstances = []

        try:
            with transaction.atomic():

                for cleaned_data in input:

                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateHowToUse)
                    else:
                        instance = models.ProductTemplateHowToUse()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateHowToUseInput)

                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    data.append((instance, cleaned_input))
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id', ProductTemplateHowToUse)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateHowToUseCreate(errors=errors)

                cls.save(info, data, removeInstances)
                return ProductTemplateHowToUseCreate(productTemplateHowToUses=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateHowToUseCreate(errors=errors)

    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance, cleaned_input in instances:
            instance.save()
            if cleaned_input.get('image'):
                create_product_template_addon_thumbnails.delay(instance.pk, models.ProductTemplateHowToUse)
        for removeInstance in removeInstances:
            removeInstance.delete()


class ProductTemplateCautionMessageInput(graphene.InputObjectType):
    message = graphene.String(description='Product template caution message')
    sort_order = graphene.Int(description="Sort order for attribute values")
    image = Upload(description='Caution message image')
    product_template = graphene.ID(description='Product template ID')
    id = graphene.ID(description='Product template caution message ID')

class ProductTemplateCautionMessageCreate(ModelMutation):

    productTemplateCautionMessages = graphene.List(ProductTemplateCautionMessage)

    class Arguments:

        input = graphene.List(ProductTemplateCautionMessageInput,
                              description='Fields required to create list of caution message')
        removeItems = graphene.List(graphene.ID, description='List of ids to delete')

    class Meta:
        description = 'Create list of caution message for product template'
        model = models.ProductTemplateCautionMessage

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        data = []
        removeInstances = []
        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateCautionMessage)
                    else:
                        instance = models.ProductTemplateCautionMessage()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateCautionMessageInput)
                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    data.append((instance, cleaned_input))
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id', ProductTemplateCautionMessage)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateCautionMessageCreate(errors=errors)

                cls.save(info, data, removeInstances)
                return ProductTemplateCautionMessageCreate(productTemplateCautionMessages=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateCautionMessageCreate(errors=errors)



    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance, cleaned_input in instances:
            instance.save()
            if cleaned_input.get('image'):
                create_product_template_addon_thumbnails.delay(instance.pk, models.ProductTemplateCautionMessage)
        for removeInstance in removeInstances:
            removeInstance.delete()

class ProductTemplateCertificationInput(graphene.InputObjectType):
    certification = graphene.ID(description='Certification ID')
    sort_order = graphene.Int(description="Sort order for attribute values")
    product_template = graphene.ID(description='Product template ID')
    id = graphene.ID(description='Product template certificate ID')

class ProductTemplateCertificationCreate(ModelMutation):

    productTemplateCertifications = graphene.List(ProductTemplateCertification)

    class Arguments:

        input = graphene.List(ProductTemplateCertificationInput,
                              description='Fields required to create list of cerificates')
        removeItems = graphene.List(graphene.ID, description='IDs of product template to delete')

    class Meta:
        description = 'Create a list of certificate'
        model = models.ProductTemplateCertification

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        removeInstances = []

        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateCertification)
                    else:
                        instance = models.ProductTemplateCertification()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateCertificationInput)

                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id', ProductTemplateCertification)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateCertificationCreate(errors=errors)
                cls.save(info, instances, removeInstances)
                return ProductTemplateCertificationCreate(productTemplateCertifications=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateCertificationCreate(errors=errors)

    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance in instances:
            instance.save()
        for removeInstance in removeInstances:
            removeInstance.delete()


class ProductTemplateWarrantyInput(graphene.InputObjectType):
    product_template = graphene.ID(description='Product template ID')
    warranty_available = graphene.Boolean(description='Product template warranty available')
    warranty_period = graphene.Int(description='Warranty period')
    time_type = graphene.String(description='Period time minute/hr/day/week/month/year')
    warranty_terms = graphene.String(description='Warranty terms')
    warranty_type = graphene.String(description='Warranty type')

class ProductTemplateWarrantyCreate(ModelMutation):

    class Arguments:
        input = ProductTemplateWarrantyInput(description='Field required for create product template warranty')

    class Meta:
        description = 'Create a new product template warranty'
        model = models.ProductTemplateWarranty

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input):
        errors = []
        product_template = cls.get_node_or_error(info, input.get('product_template'), errors, 'id', ProductTemplate)
        warranty = models.ProductTemplateWarranty.objects.filter(product_template=product_template.id).last()
        if warranty:
            instance = warranty
        else:
            instance = models.ProductTemplateWarranty()
        cleaned_input = cls.clean_input(info, instance, input, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)

        if errors:
            return ProductTemplateWarrantyCreate(errors=errors)

        instance.save()
        return ProductTemplateWarrantyCreate(productTemplateWarranty=instance, errors=errors)


class ProductTemplatePolicyInput(graphene.InputObjectType):
    product_template = graphene.ID(description='Product template ID')
    sort_order = graphene.Int(description="Sort order")
    content = graphene.String(description='Product template policy content')
    policy_type = graphene.String(description='Product template policy type')
    id = graphene.ID(description='Product template policy ID')


class ProductTemplatePolicyCreate(ModelMutation):

    productTemplatePolicies = graphene.List(ProductTemplatePolicy)

    class Arguments:
        input = graphene.List(ProductTemplatePolicyInput, description='Fields required for create product policy')
        removeItems = graphene.List(graphene.ID, description='IDs of product template policy to delete')

    class Meta:
        description = 'Create/Update a product template policy'
        model = models.ProductTemplatePolicy

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        removeInstances = []

        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplatePolicy)
                    else:
                        instance = models.ProductTemplatePolicy()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplatePolicyInput)

                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    instances.append(instance)

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id', ProductTemplatePolicy)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplatePolicyCreate(errors=errors)
                cls.save(info, instances, removeInstances)
                return ProductTemplatePolicyCreate(productTemplatePolicies=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplatePolicyCreate(errors=errors)

    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance in instances:
            instance.save()
        for removeInstance in removeInstances:
            removeInstance.delete()

class ProductTemplateIncludeInput(graphene.InputObjectType):
    product_template = graphene.ID(description='Product template ID')
    name = graphene.String(description='Pack include name')
    description = graphene.String(description='Pack include description')
    image = Upload(description='Pack include image')
    qty = graphene.Float(description='Pack include qty')
    id = graphene.ID(description='Product template include ID')

class ProductTemplateIncludeCreate(ModelMutation):

    productTemplateIncludes = graphene.List(ProductTemplateInclude)

    class Arguments:
        input = graphene.List(ProductTemplateIncludeInput, description='Fields required for create product include')
        removeItems = graphene.List(graphene.ID, description='IDs of product template include to delete')

    class Meta:
        description = 'Create/Update a product template include'
        model = models.ProductTemplateInclude

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        data = []
        removeInstances = []

        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateInclude)
                    else:
                        instance = models.ProductTemplateInclude()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateIncludeInput)

                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    instances.append(instance)
                    data.append((instance, cleaned_input))

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id', ProductTemplateInclude)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateIncludeCreate(errors=errors)
                cls.save(info, data, removeInstances)
                return ProductTemplateIncludeCreate(productTemplateIncludes=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateIncludeCreate(errors=errors)

    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance, cleaned_input in instances:
            instance.save()
            if cleaned_input.get('image'):
                create_product_template_addon_thumbnails.delay(instance.pk, models.ProductTemplateInclude)
        for removeInstance in removeInstances:
            removeInstance.delete()

class ProductTemplateManufactureInput(graphene.InputObjectType):
    product_template = graphene.ID(description='Product template ID')
    manufacture = graphene.ID(description='Product template manufacture')
    manufacture_branch = graphene.ID(description='Product template manufacture branch')

class ProductTemplateManufactureCreate(ModelMutation):

    class Arguments:
        input = ProductTemplateManufactureInput(description='Fields required to add a manufacture for product')
    class Meta:
        description = 'Create a relation between manufacture and product'
        model = models.ProductTemplateManufacture

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input):
        errors = []

        product_template = cls.get_node_or_error(info, input.get('product_template'), errors, 'id', ProductTemplate)
        manufacture = models.ProductTemplateManufacture.objects.filter(product_template=product_template.id).last()
        if manufacture:
            instance = manufacture
        else:
            instance = models.ProductTemplateManufacture()
        cleaned_input = cls.clean_input(info, instance, input, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)

        if errors:
            return ProductTemplateManufactureCreate(errors=errors)

        instance.save()
        return ProductTemplateManufactureCreate(productTemplateManufacture=instance, errors=errors)


class ProductMasterCreate(ProductMasterMixin, ModelMutation):

    class Arguments:
        input = ProductMasterInput(description='Fields required for create new master product')

    class Meta:
        description = 'Create a new master product'
        model = models.ProductMaster

    @classmethod
    def _save_m2m(cls, info, product_master, cleaned_data):
        super()._save_m2m(info, product_master, cleaned_data)
        attributes = cleaned_data.get('attributes') or []
        products = cleaned_data.get('products') or []
        for attribute in attributes:
            product_master.attributes.create(**attribute)

        for product in products:
            product_master.products.create(**product)

        images = cleaned_data.get('images') or []
        for image in images:
            image = product_master.images.create(**image)
            create_product_master_thumbnails.delay(image.pk)

        remove_images = cleaned_data.get('remove_images') or []
        for image in remove_images:
            image.delete()

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get('icon'):
            create_product_master_default_thumbnails.delay(instance.pk, 'icon')

        if cleaned_input.get('large_icon'):
            create_product_master_default_thumbnails.delay(instance.pk, 'large_icon')

        if cleaned_input.get('default_image'):
            create_product_master_default_thumbnails.delay(instance.pk, 'default_image')

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input):
        errors = []
        product_template = cls.get_node_or_error(
            info, input['product_template'], errors, 'id', ProductTemplate)

        if not product_template:
            cls.add_error(errors, 'product_template', "Product template not found")
            return ProductMasterCreate(errors=errors)
        if input.get('parent'):
            product_master = cls.get_node_or_error(
                info, input['parent'], errors, 'id', ProductMaster)
            if not product_master:
                cls.add_error(errors, 'product_master', "Parent product master not found")
        instance = models.ProductMaster()
        cleaned_input = cls.clean_master_input(info, instance, input, errors)
        cls.clean_attributes(info, cleaned_input, instance, errors)
        cls.check_all_attributes_filled(instance,cleaned_input, errors)
        cls.clean_product(info,cleaned_input, instance, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        cls.clean_master_images(info, cleaned_input, errors)
        if errors:
            return ProductMasterCreate(errors=errors)
        try:
            with transaction.atomic():
                cls.save(info, instance, cleaned_input)
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductMasterCreate(errors=errors)

        return ProductMasterCreate(productMaster=instance, errors=errors)


class ProductMasterListInput(graphene.InputObjectType):
    items = graphene.List(ProductMasterInput , description='Fields required for create/update master product')
    remove_items = graphene.List(graphene.ID, description='List of product master IDs to delete')

class ProductMasterListUpdate(ProductMasterMixin, ModelMutation):
    productMasters = graphene.List(ProductMaster)
    class Arguments:
        input = ProductMasterListInput(description='Fields required for create/update master product')

    class Meta:
        description = 'Create or update master product'
        model = models.ProductMaster

    @classmethod
    def clean_remove_items(cls, info, remove_items, errors):
        newRemoveItems = []
        for remove_item in remove_items:
            product_master = cls.get_node_or_error(
                info, remove_item, errors, 'id', ProductMaster)
            if product_master:
                master = models.ProductMaster.objects.get(pk=product_master.id)
                newRemoveItems.append(master)
        return newRemoveItems

    @classmethod
    def clean_item(cls, info, instance, input, errors, index=None):

        product_template = cls.get_node_or_error(
            info, input['product_template'], errors, 'id', ProductTemplate)
        if not product_template:
            cls.add_error(errors, 'product_template', "Product template not found")
        if input.get('parent'):
            product_master = cls.get_node_or_error(
                info, input['parent'], errors, 'id', ProductMaster)
            if not product_master:
                cls.add_error(errors, 'product_master', "Parent product master not found")

        cleaned_input = cls.clean_master_input(info, instance, input, errors, index)
        cls.clean_attributes(info, cleaned_input, instance, errors)
        cls.check_all_attributes_filled(instance, cleaned_input, errors)
        cls.clean_product(info, cleaned_input, instance, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        cls.clean_master_images(info, cleaned_input, errors)
        return (instance, cleaned_input)

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input):
        errors = []
        instances = []
        instancesArray = []
        items = input.get('items') or []
        removeItems = input.get('remove_items') or []
        for i,newItem in enumerate(items):
            if newItem.get('id'):
                instance = cls.get_node_or_error(
                    info, newItem.get('id'), errors, 'id', ProductMaster)
            else:
                instance = models.ProductMaster()
            instancesArray.append(instance)
            data = cls.clean_item(info, instance, newItem, errors, i+1)
            instances.append(data)

        removeItems = cls.clean_remove_items(info, removeItems, errors)

        if errors:
            return ProductMasterListUpdate(errors=errors)

        try:
            with transaction.atomic():
                cls.save(info, instances, removeItems)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductMasterListUpdate(errors=errors)

        return ProductMasterListUpdate(productMasters=instancesArray, errors=errors)

    @classmethod
    def save(cls, info, instances, removeItems):
        for instance, cleaned_input in instances:
            instance.save()
            attributes = cleaned_input.get('attributes') or []
            products = cleaned_input.get('products') or []
            pack_items = cleaned_input.get('pack_items') or []

            for attribute in attributes:
                instance.attributes.create(**attribute)

            for pack_item in pack_items:
                instance.product_master_pack_items.create(**pack_item)

            for product in products:
                instance.products.create(**product)

            if cleaned_input.get('icon'):
                create_product_master_default_thumbnails.delay(instance.pk, 'icon')

            if cleaned_input.get('large_icon'):
                create_product_master_default_thumbnails.delay(instance.pk, 'large_icon')

            if cleaned_input.get('default_image'):
                create_product_master_default_thumbnails.delay(instance.pk, 'default_image')

            images = cleaned_input.get('images') or []
            for image in images:
                if image.get('image'):
                    oldImage = image.get('image')
                    oldImage.media = image.get('media')
                    oldImage.save()
                    create_product_master_thumbnails.delay(oldImage.pk)
                else:
                    image = instance.images.create(**image)
                    create_product_master_thumbnails.delay(image.pk)

            remove_images = cleaned_input.get('remove_images') or []
            for image in remove_images:
                image.delete()

        for removeItem in removeItems:
            removeItem.change_status(Status.DELETED.value)


class ProductTemplateRelatedProductInput(graphene.InputObjectType):
    id = graphene.ID(description='ID of the template relation')
    sort_order = graphene.Int(description="Sort order")
    product_template = graphene.ID(description='ID of the template')
    related = graphene.ID(description='ID of the related template')
    direction = graphene.String(description='Relation type BOTH/SINGLE direction')


class ProductTemplateRelatedProductCreate(ModelMutation):

    relatedProducts = graphene.List(ProductTemplateRelatedProduct)

    class Arguments:
        input = graphene.List(ProductTemplateRelatedProductInput,
                              description='Fields required for template product relations')
        removeItems = graphene.List(graphene.ID, description='IDs of product template relation to delete')

    class Meta:
        description = 'Create a template product relation'
        model = models.ProductTemplateRelatedProduct

    @classmethod
    def clean_input(cls, info, instance, input, errors, inputCls=None):
        cleaned_input = super().clean_input(info, instance, input, errors, inputCls)

        related = cleaned_input.get('related').id
        product_template = cleaned_input.get('product_template').id

        query = models.ProductTemplateRelatedProduct.objects.filter(product_template=product_template, related=related)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            return None
        else:
            query = models.ProductTemplateRelatedProduct.objects.filter(product_template=related, related=product_template)
            query = query.exclude(pk=getattr(instance, 'pk', None))
            if query.exists():
                return None

        return cleaned_input

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input, removeItems):
        errors = []
        instances = []
        data = []
        removeInstances = []

        try:
            with transaction.atomic():
                for cleaned_data in input:
                    if cleaned_data.get('id'):
                        instance = cls.get_node_or_error(info, cleaned_data.get('id'), errors, 'id',
                                                         ProductTemplateRelatedProduct)
                    else:
                        instance = models.ProductTemplateRelatedProduct()

                    cleaned_input = cls.clean_input(info, instance, cleaned_data, errors,
                                                    ProductTemplateRelatedProductInput)

                    if cleaned_input is None:
                        continue

                    instance = cls.construct_instance(instance, cleaned_input)
                    cls.clean_instance(instance, errors)
                    instances.append(instance)
                    data.append((instance, cleaned_input))

                for remove_data in removeItems:
                    instance = cls.get_node_or_error(info, remove_data, errors, 'id', ProductTemplateRelatedProduct)
                    if instance:
                        removeInstances.append(instance)

                if errors:
                    return ProductTemplateRelatedProductCreate(errors=errors)
                cls.save(info, data, removeInstances)
                return ProductTemplateRelatedProductCreate(relatedProducts=instances, errors=errors)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return ProductTemplateRelatedProductCreate(errors=errors)


    @classmethod
    def save(cls, info, instances, removeInstances):
        for instance, cleaned_input in instances:
            instance.save()

        for removeInstance in removeInstances:
            removeInstance.delete()

class ProductMasterChangeStatus(ModelStatusChangeMutation):

    class Arguments:
        status = graphene.String(description='New status of product master')
        id = graphene.ID(description='ID of the product master')
        cascade = graphene.Boolean(description='Option to delete via non-cascade')

    class Meta:
        description = 'Update a product master status.'
        model = models.ProductMaster

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        return super().mutate(root, info, **data)

