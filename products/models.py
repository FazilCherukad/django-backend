from django.db import models
from versatileimagefield.fields import PPOIField, VersatileImageField
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from simple_history import register

from uom.models import UOM
from core.models import (
    BaseModel,
    SoftDeleteHistoryModel,
    SoftDeleteManager,
    SoftDeleteModel,
    SortableModel,
    ExportModel
)
from search.models import SeoModel
from refs.models import (
    MediaType,
    AttributeType,
    ViewType,
    ProductType,
    ProductSubType,
    CountryGroup,
    Country,
    Icon
)
from core.enums.enum import (
    ProductPackingType,
    TimeType,
    PolicyType,
    WarrantyType,
    ValueType,
    Maturity,
    Priority,
    Direction,
    UserType,
    Status
)
from manufacture.models import (
    ManufactureBranch,
    Manufacture,
    Certification
)

PERMISSIONS_FOR = [UserType.ADMIN.value]

class AttributeGroup(BaseModel):
    """Attribute group, example Display, Memory"""
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    icon = models.ForeignKey(
        Icon,
        related_name='attribute_groups',
        on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class AttributeGroupItem(BaseModel):
    """Attribute group items, example Size, Resolution under group Display"""
    attribute_group = models.ForeignKey(
        AttributeGroup,
        related_name='items',
        on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    icon = models.ForeignKey(
        Icon,
        related_name='attribute_group_items',
        on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Attribute(BaseModel):
    """Attribute is help to define variants of a product template
    For example Color of a product (iPhone6 have multiple colors)
    All the attributes are categorised into attribute group General"""
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)
    qty_attribute = models.BooleanField(default=False)
    attribute_type = models.ForeignKey(
        AttributeType,
        related_name='attributes',
        on_delete=models.CASCADE)
    icon = models.ForeignKey(
        Icon,
        related_name='attributes',
        on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class AttributeValue(BaseModel, SortableModel):
    """Predefined values of a attribute
    example red, green are the values of the attribute color"""
    attribute = models.ForeignKey(
        Attribute,
        related_name='values',
        on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    value = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128)

    def __str__(self):
        return self.name

class Department(SeoModel, SoftDeleteHistoryModel, ExportModel):
    """Department is the top level of the product tree
    Example grocery, home appliances, electronics"""

    name = models.CharField(max_length=128, )
    slug = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=12, unique=True)
    note = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    icon = VersatileImageField(
        upload_to='category-group-icons', blank=True, null=True)
    large_icon = VersatileImageField(
        upload_to='category-group-large-icons', blank=True, null=True)
    default_image = VersatileImageField(
        upload_to='category-group-images')
    image_alt_text = models.CharField(max_length=32, default="Department")
    background_color = models.CharField(max_length=32, blank=True, null=True)
    view_type = models.ForeignKey(
        ViewType,
        related_name='departments',
        on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status])

    def __str__(self):
        return self.name

class DepartmentTranslation(BaseModel):
    """A translated object of Department"""
    department = models.ForeignKey(
        Department,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=128, unique=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("language_code", "department"),)


class Category(MPTTModel, SoftDeleteModel, SeoModel, ExportModel):
    """Category is second level in product tree
    example fruits, vegetables"""
    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=12, unique=True)
    note = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    icon = VersatileImageField(
        upload_to='category-icons', blank=True, null=True)
    large_icon = VersatileImageField(
        upload_to='category-large-icons', blank=True, null=True)
    default_image = VersatileImageField(
        upload_to='category-images')
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)
    image_alt_text = models.CharField(max_length=32, default="Category")
    department = models.ForeignKey(
        Department,
        related_name='categories',
        on_delete=models.CASCADE, blank=True, null=True)
    priority = models.CharField(max_length=10, choices=[(priority.name, priority.value) for priority in Priority],
                                default=Priority.MEDIUM.value)
    maturity = models.CharField(max_length=10, choices=[(maturity.name, maturity.value) for maturity in Maturity],
                                default=Maturity.MATURED.value)
    view_type = models.ForeignKey(
        ViewType,
        related_name='categories',
        on_delete=models.SET_NULL, blank=True, null=True)
    background_color = models.CharField(max_length=32, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status])

    objects = SoftDeleteManager()
    tree = TreeManager()

    def __str__(self):
        return self.name

    def get_image_url(self, info):
        return info.context.build_absolute_uri(self.default_image.url)

register(Category)


class CategoryTranslation(BaseModel):
    """A translated object for category"""
    category = models.ForeignKey(
        Category,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=128,unique=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("language_code", "category"),)



class CategoryMedia(BaseModel, SortableModel):
    """Multiple images of a category, optional"""
    category = models.ForeignKey(
        Category,
        related_name='images',
        on_delete=models.CASCADE)
    media_type = models.ForeignKey(
        MediaType,
        related_name='category_medias',
        on_delete=models.CASCADE, blank=True, null=True)
    media = VersatileImageField(
        upload_to='category-images')


class Brand(SoftDeleteHistoryModel, SeoModel, ExportModel):
    """Brand of a product like nike, adidas"""
    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=12, unique=True)
    note = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    icon = VersatileImageField(
        upload_to='brand-icons', blank=True, null=True)
    large_icon = VersatileImageField(
        upload_to='brand-large-icons', blank=True, null=True)
    default_image = VersatileImageField(
        upload_to='brand-images')
    image_alt_text = models.CharField(max_length=32, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status])

    def __str__(self):
        return self.name


class BrandTranslation(BaseModel):
    """A translated object for brand"""
    brand = models.ForeignKey(
        Brand,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=128, unique=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("language_code", "brand"),)

class BrandMedia(BaseModel, SortableModel):
    """Multiple image option for brand"""
    brand = models.ForeignKey(
        Brand,
        related_name='images',
        on_delete=models.CASCADE)
    media_type = models.ForeignKey(
        MediaType,
        related_name='brand_medias',
        on_delete=models.CASCADE, blank=True, null=True)
    media = VersatileImageField(
        upload_to='brand-images')


class ProductTemplate(SoftDeleteHistoryModel, SeoModel, ExportModel):
    """Product template is third level of product tree
    But in other way it is the first level of the product tree
    Every product start define from here
    Example iPhone 6 is a product template
    Product type means Food/Beverages and sub type means Veg/Non-Veg/Hot/Cool"""
    name = models.CharField(max_length=128)
    slug = models.CharField(max_length=128, unique=True)
    code = models.CharField(max_length=15, unique=True)
    model = models.CharField(max_length=64, blank=True, null=True)
    uom = models.ForeignKey(
        UOM,
        related_name='templates',
        on_delete=models.SET_NULL, blank=True, null=True)
    selling_unit = models.ForeignKey(
        UOM,
        related_name='selling_templates',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    description = models.TextField(blank=True, null=True)
    cared_handle = models.BooleanField(default=False)
    url = models.URLField(blank=True, null=True)
    icon = VersatileImageField(
        upload_to='product-template-icons', blank=True, null=True)
    large_icon = VersatileImageField(
        upload_to='product-template-icons', blank=True, null=True)
    default_image =VersatileImageField(
        upload_to='product-template-images')
    product_type = models.ForeignKey(
        ProductType,
        related_name='templates',
        on_delete=models.SET_NULL, blank=True, null=True)
    product_sub_type = models.ForeignKey(
        ProductSubType,
        related_name='templates',
        on_delete=models.SET_NULL, blank=True, null=True)
    tax = models.FloatField(default=0)
    background = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status])

    def __str__(self):
        return self.name

class ProductTemplateCountry(SoftDeleteHistoryModel):
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='countries',
        on_delete=models.CASCADE
    )
    country = models.ForeignKey(
        Country,
        related_name='products',
        on_delete=models.DO_NOTHING
    )

class ProductTemplateTranslation(BaseModel, SeoModel):
    """A translated object for product template"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=128, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("language_code", "product_template"),)

class ProductCategoryRelation(SoftDeleteHistoryModel):
    """A product template can have optional categories or multiple categories"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='categories',
        on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        related_name='templates',
        on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status],
                              default=Status.ACTIVE.value)

    class Meta:
        unique_together = (("category", "product_template"),)

    def change_status(self, status, **kwargs):
        super().change_status(status, **kwargs)
        self.product_template.change_status(status, **kwargs)


class ProductBrandRelation(SoftDeleteHistoryModel):
    """A product template can have optional brand or multiple brand (in case of mixed pack)"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='brands',
        on_delete=models.CASCADE)
    brand = models.ForeignKey(
        Brand,
        related_name='templates',
        on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status],
                              default=Status.ACTIVE.value)

    class Meta:
        unique_together = (("brand", "product_template"),)


class ProductTemplateAttributeGroup(BaseModel, SortableModel):
    """Product template assigned attribute group with item and its value
    example attribute group display contains an item resolution and value 1024x1024"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='attribute_groups',
        on_delete=models.CASCADE)
    attribute_group = models.ForeignKey(
        AttributeGroup,
        related_name='templates',
        on_delete=models.CASCADE)


    class Meta:
        unique_together = (("product_template", "attribute_group"),)


class ProductTemplateAttributeGroupValue(BaseModel):
    template_attribute_group = models.ForeignKey(
        ProductTemplateAttributeGroup,
        related_name='items',
        on_delete=models.CASCADE
    )
    attribute_group_item = models.ForeignKey(
        AttributeGroupItem,
        related_name='templates',
        on_delete=models.CASCADE)
    value = models.CharField(max_length=128)

    class Meta:
        unique_together = (("template_attribute_group", "attribute_group_item"),)


class ProductTemplateAttribute(BaseModel, SortableModel):
    """Product template assigned attributes"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='attributes',
        on_delete=models.CASCADE)
    attribute = models.ForeignKey(
        Attribute,
        related_name='templates',
        on_delete=models.CASCADE)

    class Meta:
        unique_together = (("product_template", "attribute"),)

class ProductTemplateMedia(BaseModel, SortableModel):
    """Multiple media files for a product template"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='images',
        on_delete=models.CASCADE)
    media_type = models.ForeignKey(
        MediaType,
        related_name='templates',
        on_delete=models.CASCADE, blank=True, null=True)
    media = VersatileImageField(
        upload_to='product-template-images')

class ProductTemplateDescription(BaseModel, SortableModel):
    """Product template description with title, description and image"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='descriptions',
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=128)
    description = models.TextField()
    image = VersatileImageField(
        upload_to='product-template-description-images', blank=True, null=True)

    def __str__(self):
        return self.title


class ProductTemplateDescriptionTranslation(BaseModel):
    """A translated object for product template description"""
    product_template_description = models.ForeignKey(
        ProductTemplateDescription,
        related_name='translations',
        on_delete=models.CASCADE
    )
    language_code = models.CharField(max_length=10)
    title = models.CharField(max_length=128)
    description = models.TextField()

    class Meta:
        unique_together = (("language_code", "product_template_description"),)


class ProductTemplateNutrition(BaseModel, SortableModel):
    """List of nutrition's of a product"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='nutritions',
        on_delete=models.CASCADE)
    nutrition = models.TextField()
    value = models.CharField(max_length=128, blank=True, null=True)

class ProductTemplateNutritionTranslation(BaseModel):
    """A translated object for product nutrition"""
    product_template_nutrition = models.ForeignKey(
        ProductTemplateNutrition,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    nutrition = models.TextField()

    class Meta:
        unique_together = (("language_code", "product_template_nutrition"),)

class ProductTemplateIngredient(BaseModel, SortableModel):
    """Product template ingredients"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='ingredients',
        on_delete=models.CASCADE)
    ingredient = models.TextField()
    value = models.CharField(max_length=128, blank=True, null=True)

class ProductTemplateHowToUse(BaseModel, SortableModel):
    """Product template hoe to use instructions"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='how_to_use',
        on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    image = VersatileImageField(
        upload_to='product-template-how_to_use',null=True, blank=True)


class ProductTemplateCautionMessage(BaseModel, SortableModel):
    """Product template caution message"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='cautions',
        on_delete=models.CASCADE)
    message = models.TextField()
    image = VersatileImageField(
        upload_to='product-template-caution',null=True, blank=True)

class ProductTemplateCertification(BaseModel, SortableModel):
    """Product template can have multiple certificates like fsaai"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='certifications',
        on_delete=models.CASCADE)
    certification = models.ForeignKey(
        Certification,
        related_name='certificate',
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("product_template", "certification"),)

class ProductTemplateWarranty(BaseModel):
    """Warranty available for a product template, and which type of warranty"""
    product_template = models.OneToOneField(
        ProductTemplate,
        related_name='warranty',
        on_delete=models.CASCADE)
    warranty_available = models.BooleanField(default=False)
    warranty_period = models.CharField(max_length=10, blank=True, null=True)
    time_type = models.CharField(
            max_length=8,
            choices=[(time_type.name, time_type.value) for time_type in TimeType]
            , blank=True, null=True)
    warranty_type = models.CharField(max_length=15,choices=[(type.name, type.value) for type in WarrantyType])
    warranty_terms = models.TextField(blank=True, null=True)


class ProductTemplateWarrantyTranslation(BaseModel):
    """A translated object for warranty"""
    product_template_warranty = models.OneToOneField(
        ProductTemplateWarranty,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    warranty_terms = models.TextField()


class ProductTemplatePolicy(BaseModel, SortableModel):
    """Other policies of product template"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='policies',
        on_delete=models.CASCADE)
    content = models.TextField()
    policy_type = models.CharField(
            max_length=8,
            choices=[(policy_type.name, policy_type.value) for policy_type in PolicyType]
            , blank=True, null=True)


class ProductTemplatePolicyTranslation(BaseModel):
    """A translated object for policy"""
    product_template_policy = models.ForeignKey(
        ProductTemplatePolicy,
        related_name='translations',
        on_delete=models.CASCADE)
    content = models.TextField()

class ProductTemplateManufacture(BaseModel):
    """Manufacture and origin details of a template product"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='manufactures',
        on_delete=models.CASCADE)
    manufacture = models.ForeignKey(
        Manufacture,
        related_name='templates',
        on_delete=models.CASCADE
    )
    manufacture_branch = models.ForeignKey(
        ManufactureBranch,
        related_name='templates',
        on_delete = models.CASCADE,
        blank=True, null=True
    )

class ProductMaster(MPTTModel, SoftDeleteModel, SeoModel, ExportModel):
    """Product master is all the variants and packs of the product master
    Inheriting description privacy, warranty etc. Option to overwrite"""

    name = models.CharField(max_length=128, null=True, blank=True)
    sub_name = models.CharField(max_length=128, null=True, blank=True)
    slug = models.CharField(max_length=128, unique=True, null=True, blank=True)
    code = models.CharField(max_length=15, unique=True)
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='masters',
        on_delete=models.CASCADE, blank=True, null=True)
    model = models.CharField(max_length=32, blank=True, null=True,)
    barcode = models.CharField(max_length=32, blank=True, null=True,)
    description = models.TextField( blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    weight = models.FloatField(max_length=128, blank=True, null=True)
    weight_unit = models.ForeignKey(
        UOM,
        related_name='masters',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        on_delete=models.CASCADE)
    icon = VersatileImageField(
        upload_to='product-master-icons', blank=True, null=True)
    large_icon = VersatileImageField(
        upload_to='product-master-icons', blank=True, null=True)
    default_image = VersatileImageField(
        upload_to='product-master-images', null=True, blank=True)
    image_alt_text = models.CharField(max_length=32, default="Product")
    packing_type = models.CharField(
            max_length=8,
            choices=[(packing_type.name, packing_type.value) for packing_type in ProductPackingType]
            , blank=True, null=True, default=ProductPackingType.SINGLE.value)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status],
                              default=Status.ACTIVE.value)

    objects = SoftDeleteManager()
    tree = TreeManager()

    def __str__(self):
        if self.name == '' or not self.name:
            return self.product_template.name
        return self.name

    def get_image(self):
        if self.default_image:
            return self.default_image
        return self.product_template.default_image

    def get_sub_name(self):
        value = ''
        if self.sub_name:
            return self.sub_name
        if self.packing_type != ProductPackingType.SINGLE.value:
            items = self.product_master_pack_items.all()
            i = 0
            for item in items:
                product_master = item.item
                if product_master.name == '' or not product_master.name:
                    name = product_master.product_template.name
                else:
                    name = product_master.name
                value += str(int(item.qty)) + ' ' + name
                if i != len(items)-1:
                    value += ', '
                i += 1
        return value

register(ProductMaster)

class ProductMasterTranslation(BaseModel):
    """A translated object for product master"""
    product_master = models.ForeignKey(
        ProductMaster,
        related_name='translations',
        on_delete=models.CASCADE)
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=128)
    note = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (("product_master", "language_code"),)

class ProductMasterAttributeValue(BaseModel):
    """Product master values of attribute assigned for product template"""
    product_master = models.ForeignKey(
        ProductMaster,
        related_name='attributes',
        on_delete=models.CASCADE)
    product_template_attribute = models.ForeignKey(
        ProductTemplateAttribute,
        related_name='masters',
        on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(
        AttributeValue,
        related_name='masters',
        on_delete=models.CASCADE)

class ProductTemplateInclude(BaseModel, SortableModel):
    """Product template box includes.
    Example iPhone 6 box contain charger, headphone etc.
    Its may be a string or existing product from our system"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='included',
        on_delete=models.CASCADE
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=128, null=True, blank=True)
    image = VersatileImageField(
        upload_to='product-master-included', blank=True, null=True)
    value_type = models.CharField(max_length=10, choices=[(type.name, type.value) for type in ValueType],
                                  default=ValueType.FREE.value)
    qty = models.FloatField(default=1)
    warranty_available = models.BooleanField(default=False)
    ref_id = models.ForeignKey(
        ProductMaster,
        related_name='master_product',
        on_delete=models.SET_NULL, null=True, blank=True)

class ProductPackItem(BaseModel):
    """Product master mixed combination contains list of items"""
    product_master = models.ForeignKey(
        ProductMaster,
        related_name='product_master_pack_items',
        on_delete=models.CASCADE)
    item = models.ForeignKey(
        ProductMaster,
        related_name='product_master_pack_item',
        on_delete=models.CASCADE)
    qty = models.FloatField()
    value_type = models.CharField(max_length=10, choices=[(type.name, type.value) for type in ValueType],
                                  default=ValueType.PAID.value)

class ProductMasterMedia(BaseModel, SortableModel):
    """Multiple media option to product master/ overwrite product template based on overwrite_media field in product
    master"""
    product_master = models.ForeignKey(
        ProductMaster,
        related_name='images',
        on_delete=models.CASCADE)
    media_type = models.ForeignKey(
        MediaType,
        related_name='m_image_type',
        on_delete=models.CASCADE, blank=True, null=True)
    media = VersatileImageField(
        upload_to='product-master-images')


# class ProductMasterDescription(BaseModel):
#     """Overwrite/append variant description"""
#     product_master = models.ForeignKey(
#         ProductMaster,
#         related_name='descriptions',
#         on_delete=models.CASCADE
#     )
#     title = models.CharField(max_length=128)
#     description = models.TextField()
#     image = models.FileField(
#         upload_to='product-master-description-image', blank=True, null=True)
#
#
# class ProductMasterDescriptionTranslation(BaseModel):
#     """A translated object for product master description"""
#     product_master_description = models.ForeignKey(
#         ProductMasterDescription,
#         related_name='descriptions_tr',
#         on_delete=models.CASCADE
#     )
#     language_code = models.CharField(max_length=10)
#     title = models.CharField(max_length=128)
#     description = models.TextField()


class ProductMasterPacking(BaseModel):
    """Packing details of product master"""
    product_master = models.ForeignKey(
        ProductMaster,
        related_name='product_master_ver',
        on_delete=models.CASCADE)
    available_onwards = models.DateField(blank=True, null=True)
    expire_period_from_packing = models.IntegerField(blank=True, null=True)
    time_type = models.CharField(
        max_length=8,
        choices=[(time_type.name, time_type.value) for time_type in TimeType]
        , blank=True, null=True)

class ProductTemplateRelatedProduct(BaseModel, SortableModel):
    """Related products"""
    product_template = models.ForeignKey(
        ProductTemplate,
        related_name='related',
        on_delete=models.CASCADE
    )
    related = models.ForeignKey(
        ProductTemplate,
        related_name='related_reverse',
        on_delete=models.CASCADE
    )
    direction = models.CharField(max_length=10, choices=[(direction.name, direction.value) for direction in Direction],
                                 default=Direction.BOTH.value)


class Product(BaseModel, SeoModel):
    """Overwrite a master product for a country/group of countries"""
    product_master = models.ForeignKey(
        ProductMaster,
        related_name='products',
        on_delete=models.CASCADE)
    country = models.ForeignKey(
        Country,
        related_name='country_overwrite_products',
        on_delete=models.DO_NOTHING
    )
    code = models.CharField(max_length=15, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=32, blank=True, null=True)
    name = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    default_image = VersatileImageField(
        upload_to='product-images', null=True, blank=True)
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status],
                              default=Status.ACTIVE.value)



# class ProductMasterPrice(BaseModel):
#     """Product master default price in country group"""
#     product_master = models.OneToOneField(
#         ProductMaster,
#         related_name='price',
#         on_delete=models.CASCADE)
#     price = models.FloatField()
#     discount = models.FloatField(default=0)
#     final_price = models.FloatField()
#
# class ProductMasterPriceHistory(BaseModel):
#     """Product price history"""
#     product_master = models.ForeignKey(
#         ProductMaster,
#         related_name='price_histories',
#         on_delete=models.CASCADE)
#     price = models.FloatField()
#     discount = models.FloatField(default=0)
#     final_price = models.FloatField()
#     date = models.DateTimeField()
#
# class ProductMasterPaymentOption(BaseModel):
#     product_master = models.ForeignKey(
#         ProductMaster,
#         related_name='payment_options',
#         on_delete=models.CASCADE)
#     payment_option = models.ForeignKey(
#         PaymentOption,
#         related_name='masters',
#         on_delete=models.CASCADE)
#
#
# class ProductMasterReview(BaseModel):
#     product_master = models.ForeignKey(
#         ProductMaster,
#         related_name='reviews',
#         on_delete=models.CASCADE)
#     rating = models.FloatField(blank=True, null=True)
#     message = models.TextField(blank=True, null=True)
#     rated_by = models.IntegerField(blank=True, null=True)
#     order_id = models.CharField(max_length=255, blank=True, null=True)
#
# class ProductRegistry(BaseModel):
#     date_time = models.DateTimeField()
#     level = models.CharField(max_length=10, choices=[(level.value, level.name) for level in ProductLevel])
#     ref_id = models.IntegerField()


