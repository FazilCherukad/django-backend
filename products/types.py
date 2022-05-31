from django.db.models import Q
import graphene
import graphene_django_optimizer as gql_optimizer
from graphene import relay
from graphene_federation import key

from core.utils.connection import CountableDjangoObjectType
from core.custom.get_thumbnails import get_thumbnail
from core.types.meta import MetadataObjectType
from refs.types import AttributeType
from uom.types import UOM
from store_products.types import StoreProduct
from core.enums.enum import Status, ProductPackingType
from store_products import models as store_product_model
from . import models

class ProductTemplateMedia(CountableDjangoObjectType):
    media = graphene.String(
        required=True,
        description='The URL of the image.')

    class Meta:
        description = 'Represents a image of product template.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateMedia

    def resolve_media(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.media, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

class AttributeValue(CountableDjangoObjectType):
    name = graphene.String(description="Attribute value name")
    value = graphene.String(description="Attribute value")

    class Meta:
        description = 'Represents a value of an attribute value.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.AttributeValue

class Attribute(CountableDjangoObjectType):
    name = graphene.String(description="Attribute name")
    attribute_type = AttributeType()
    values = gql_optimizer.field(
        graphene.List(
            AttributeValue, description="Attribute values"),
        model_field='values')

    class Meta:
        description = 'Represents a value of an attribute.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Attribute

    def resolve_values(self, info):
        return self.values.all()


class AttributeGroupItem(CountableDjangoObjectType):
    name = graphene.String(description="Attribute group item name")

    class Meta:
        description = 'Represents a value of an group attribute items.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.AttributeGroupItem

class AttributeGroup(CountableDjangoObjectType):
    name = graphene.String(description="Attribute group name")
    items = gql_optimizer.field(
        graphene.List(
            AttributeGroupItem, description="Attribute group item"),
        model_field='items')

    class Meta:
        description = 'Represents a value of an attribute group.'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.AttributeGroup

    def resolve_items(self, info):
        return self.items.all()



class Department(CountableDjangoObjectType):
    name = graphene.String(description="Department name")
    code = graphene.String(description="Department code")
    note = graphene.String(description="Department note")
    url = graphene.String(description="Department url")
    icon = graphene.String(description="Department icon")
    large_icon = graphene.String(description="Department large icon")
    default_image = graphene.String(description="Department default image")
    view_type = graphene.ID(description='Department view type.')
    status = graphene.String(description="Department set active/disabled/delete")

    class Meta:
        description = 'Represent a Department'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Department

    def resolve_default_image(self, info, *, size=None):
        return info.context.build_absolute_uri(self.default_image.url)


class Brand(CountableDjangoObjectType):
    name = graphene.String(description="Brand name")
    code = graphene.String(description="Brand code")
    note = graphene.String(description="Brand note")
    url = graphene.String(description="Brand url")
    icon = graphene.String(description="Brand icon")
    large_icon = graphene.String(description="Brand large icon")
    default_image = graphene.String(description="Brand default image")
    status = graphene.String(description="Brand set active/disabled/delete")

    class Meta:
        description = 'Represent a Brand'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Brand

    @gql_optimizer.resolver_hints(prefetch_related='images')
    def resolve_default_image(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.default_image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

class Category(CountableDjangoObjectType):
    name = graphene.String(description="Category name")
    code = graphene.String(description="Category code")
    note = graphene.String(description="Category note")
    url = graphene.String(description="Category url")
    icon = graphene.String(description="Category icon")
    large_icon = graphene.String(description="Category large icon")
    default_image = graphene.String(description="Category default image")
    status = graphene.String(description="Category set active/disabled/delete")

    class Meta:
        description = 'Represent a Category'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Category

    @gql_optimizer.resolver_hints(prefetch_related='images')
    def resolve_default_image(self, info, *, size=None):
        return info.context.build_absolute_uri(self.default_image.url)

class ProductTemplateAttributeGroup(CountableDjangoObjectType):
    attribute_group = graphene.Field(AttributeGroup, description='Attribute group')
    product_template = graphene.ID(description='Product template ID')

    class Meta:
        description = 'Represent a Product Template attribute group'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateAttributeGroup

class ProductTemplateAttributeGroupValue(CountableDjangoObjectType):
    attribute_group_item = graphene.Field(AttributeGroupItem, description='Attribute group item')
    value = graphene.String(description='Attribute group item value')

    class Meta:
        description = 'Represent a Product Template attribute group value'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateAttributeGroupValue

class ProductCategoryRelation(CountableDjangoObjectType):
    class Meta:
        description = 'Represent a Product Template categories'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductCategoryRelation

class ProductBrandRelation(CountableDjangoObjectType):
    class Meta:
        description = 'Represent a Product Template brands'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductBrandRelation

class ProductTemplateAttribute(CountableDjangoObjectType):

    class Meta:
        description = 'Represent a Product Template attribute'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateAttribute

class ProductTemplateDescription(CountableDjangoObjectType):
    title = graphene.String(description='Description title')
    description = graphene.String(description='Description content')

    class Meta:
        description = 'Represent a Product Template description'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateDescription

    @gql_optimizer.resolver_hints()
    def resolve_image(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

@key(fields="id")
class ProductTemplate(CountableDjangoObjectType, MetadataObjectType):
    name = graphene.String(description="Product Template name")
    code = graphene.String(description="Product Template code")
    model = graphene.String(description="Product Template model")
    url = graphene.String(description="Product Template url")
    icon = graphene.String(description="Product Template icon")
    large_icon = graphene.String(description="Product Template large icon")
    default_image = graphene.String(description="Product Template default image")
    description = graphene.String(description="Product Template description")
    status = graphene.String(description="Product template set active/disabled/delete")
    departments = gql_optimizer.field(
        graphene.List(
            Department, description="Product template assigned departments"))
    store_products = gql_optimizer.field(
        graphene.List(
            StoreProduct, description="Product template assigned attributes"))


    class Meta:
        description = 'Represent a Product Template'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplate

    @gql_optimizer.resolver_hints(prefetch_related='images')
    def resolve_default_image(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.default_image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

    # def resolve_attributes(self, info):
    #     return self.attributes.all()

    def resolve_attribute_groups(self, info):
        return self.attribute_groups.all()

    def resolve_departments(self, info):
        categories = self.categories.values_list('category')
        return models.Department.objects.filter(categories__pk__in=categories).distinct()

    def resolve_related(self, info):
        return models.ProductTemplateRelatedProduct.objects.filter(Q(product_template=self.id)|Q(related=self.id))

    def resolve_store_products(self, info):
        user = info.context.user
        store = user.get_store()
        masters = self.masters.filter(status=Status.ACTIVE.value,
                                      stores__store=store.id,
                                      stores__status=Status.ACTIVE.value
                                      ).values_list('id', flat=True)
        return store_product_model.StoreProduct.objects.filter(product_master__in=masters, store=store.id)



class ProductTemplateNutrition(CountableDjangoObjectType):
    nutrition = graphene.String(description='Product template nutrition description')
    value = graphene.String(description='Product template nutrition description have any value')

    class Meta:
        description = 'Represent a Product Template Nutrition'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateNutrition

class ProductTemplateIngredient(CountableDjangoObjectType):
    ingredient = graphene.String(description='Product template ingredient')
    value = graphene.String(description='Product template ingredient have any value')

    class Meta:
        description = 'Represent a Product Template Ingredient'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateIngredient

class ProductTemplateHowToUse(CountableDjangoObjectType):
    level = graphene.Int(description='How to use step number')
    title = graphene.String(description='Title for how to use')
    description = graphene.String(description='A detailed note for how to use')

    class Meta:
        description = 'Represent a Product Template How to use'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateHowToUse

    @gql_optimizer.resolver_hints()
    def resolve_image(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)


class ProductTemplateCautionMessage(CountableDjangoObjectType):
    message = graphene.String(description='Product template caution message')

    class Meta:
        description = 'Represent a Product Template Caution message'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateCautionMessage

    @gql_optimizer.resolver_hints()
    def resolve_image(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

class ProductTemplateCertification(CountableDjangoObjectType):

    class Meta:
        description = 'Represent a Product Template Certification'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateCertification

class ProductTemplateManufacture(CountableDjangoObjectType):
    product_template = graphene.ID(description='Product template ID')

    class Meta:
        description = 'Represent a Product Template Manufacture'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateManufacture


class ProductTemplateWarranty(CountableDjangoObjectType):

    class Meta:
        description = 'Represent a Product Template Warranty'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateWarranty

class ProductTemplatePolicy(CountableDjangoObjectType):

    class Meta:
        description = 'Represent a Product Template Policy'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplatePolicy

class ProductTemplateInclude(CountableDjangoObjectType):
    name = graphene.String(description='Pack include name')
    description = graphene.String(description='Pack include description')
    image = graphene.String(description='Pack include image')
    qty = graphene.Float(description='Pack include qty')

    class Meta:
        description = 'Represent a Product Template Include'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateInclude

    @gql_optimizer.resolver_hints()
    def resolve_image(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

class ProductMasterAttributeValue(CountableDjangoObjectType):

    class Meta:
        description = 'Represent a Product Template Attribute value'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductMasterAttributeValue

class ProductMasterMedia(CountableDjangoObjectType):

    class Meta:
        description = 'Represent a Product Master image'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductMasterMedia

    def resolve_media(self, info, *, size=None):
        if not size:
            size = 255
        url = get_thumbnail(
            self.media, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

class ProductPackItem(CountableDjangoObjectType):
    class Meta:
        description = 'Represent a Product Master Pack Item'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductPackItem

class ProductMaster(CountableDjangoObjectType):

    name = graphene.String(description='Product master name')
    model = graphene.String(description='Product master model number')
    barcode = graphene.String(description='Product master barcode')
    description = graphene.String(description='Product master description')
    url = graphene.String(description='Product master url')
    weight = graphene.String(description='Product master weight')
    status = graphene.String(description="Product master set active/disabled/delete")
    departments = gql_optimizer.field(
        graphene.List(
            Department, description="Product master department"))
    categories = gql_optimizer.field(
        graphene.List(
            Category, description="Product master category"))
    brands = gql_optimizer.field(
        graphene.List(
            Brand, description="Product master brands"))
    pack_items = gql_optimizer.field(
        graphene.List(
            ProductPackItem, description="Product master brands"))
    unit = gql_optimizer.field(
        graphene.Field(
            UOM, description="Product master unit"))
    store_product = gql_optimizer.field(
        graphene.Field(
            StoreProduct, description="Product product"))
    self_name = graphene.String(description='Product master self name')
    self_description = graphene.String(description='Product master self description')
    sub_name = graphene.String(description="Product Pack Items Details")

    class Meta:
        description = 'Represent a Product Master'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductMaster

    @gql_optimizer.resolver_hints(prefetch_related='images')
    def resolve_default_image(self, info, *, size=None):
        if not size:
            size = 255

        if self.default_image:
            default_image = self.default_image
        else:
            default_image = self.product_template.default_image
        url = get_thumbnail(
            default_image, size, method='thumbnail')
        return info.context.build_absolute_uri(url)

    def resolve_description(self, info):
        if self.description == '' or not self.description:
            return self.product_template.description
        return self.description

    def resolve_name(self, info):
        if self.name == '' or not self.name:
            return self.product_template.name
        return self.name

    def resolve_sub_name(self, info):
        return self.get_sub_name()

    def resolve_self_description(self, info):
        return self.description

    def resolve_self_name(self, info):
        return self.name

    def resolve_departments(self, info):
        categories = self.product_template.categories.values_list('category', flat=True)
        return models.Department.objects.filter(categories__pk__in=categories).distinct()

    def resolve_categories(self, info):
        categories = self.product_template.categories.values_list('category', flat=True)
        return models.Category.objects.filter(pk__in=categories).distinct()

    def resolve_pack_items(self, info):
        return self.product_master_pack_items.all()

    def resolve_brands(self, info):
        brands = self.product_template.brands.values_list('brand', flat=True)
        return models.Brand.objects.filter(pk__in=brands).distinct()

    def resolve_unit(self, info):
        return self.product_template.uom

    def resolve_store_product(self, info):
        try:
            user = info.context.user
            store = user.get_store()
            master = store_product_model.StoreProduct.all_objects.get(store=store.id, product_master=self.id)
        except store_product_model.StoreProduct.DoesNotExist:
            return None
        return master


class ProductTemplateRelatedProduct(CountableDjangoObjectType):

    direction = graphene.String(description='Product template relation direction')

    class Meta:
        description = 'Represent a Product Template related product'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.ProductTemplateRelatedProduct

class Product(CountableDjangoObjectType):
    code = graphene.String(description='Product name')
    barcode = graphene.String(description='Product barcode')
    country_group = graphene.List(graphene.ID, description='IDs of country group')
    status = graphene.String(description='Product status')

    class Meta:
        description = 'Represent a Product'
        interfaces = [relay.Node]
        exclude_fields = []
        model = models.Product




