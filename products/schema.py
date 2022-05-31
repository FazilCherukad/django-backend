import graphene

from core.utils.decorators import (
    permission_required,
    role_required
)
from core.enums.enum import UserType
from core.utils.fields import (
    PrefetchingConnectionField,
    FilterInputConnectionField
)
from .mutations.attributes import (
    AttributeCreate,
    AttributeGroupCreate,
    AttributeUpdate,
    AttributeGroupUpdate,
    AttributeDelete,
    AttributeGroupDelete
)
from .mutations.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentChangeStatus
)
from .mutations.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryChangeStatus
)
from .mutations.brand import (
    BrandCreate,
    BrandUpdate,
    BrandChangeStatus
)
from .mutations.products import (
    ProductTemplateCreate,
    ProductTemplateUpdate,
    ProductTemplateChangeStatus,
    ProductTemplateAttributeGroupCreate,
    ProductTemplateWarrantyCreate,
    ProductTemplatePolicyCreate,
    ProductMasterCreate,
    ProductTemplateDescriptionCreate,
    ProductTemplateNutritionCreate,
    ProductTemplateIngredientCreate,
    ProductTemplateHowToUseCreate,
    ProductTemplateCautionMessageCreate,
    ProductTemplateCertificationCreate,
    ProductTemplateAttributeCreate,
    ProductMasterListUpdate,
    ProductTemplateManufactureCreate,
    ProductTemplateIncludeCreate,
    ProductTemplateRelatedProductCreate,
    ProductMasterChangeStatus,
    CheckBarcodeExist
)
from .types import (
    Department,
    ProductTemplate,
    Category,
    Attribute,
    AttributeGroup,
    Brand,
    ProductMaster,
    ProductTemplateAttribute
)
from .resolvers import (
    resolve_categories,
    resolve_attributes,
    resolve_group_attributes,
    resolve_departments,
    resolve_brands,
    resolve_templates,
    resolve_product_masters,
    resolve_product_template_attributes
)
from .filters import (
    TemplateFilterInput,
    MasterFilterInput,
    CategoryFilterInput,
    BrandFilterInput
)
from .sorters import (
    TemplateSortInput,
    MasterSortInput
)

class ProductQuery(graphene.ObjectType):

    search_products = FilterInputConnectionField(
        ProductTemplate, query=graphene.String(
            description='List of attributes query'),
        description='List of attributes.')

    attribute = graphene.Field(
        Attribute, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a attribute by ID.')
    attributes = FilterInputConnectionField(
        Attribute, query=graphene.String(
            description='List of attributes query'),
        description='List of attributes.')

    group_attribute = graphene.Field(
        AttributeGroup, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a group attribute by ID.')
    group_attributes = FilterInputConnectionField(
        AttributeGroup, query=graphene.String(
            description='List of group attributes query'),
        description='List of group attributes.')

    department = graphene.Field(
        Department, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a department by ID.')
    departments = FilterInputConnectionField(
        Department, query=graphene.String(
            description='List of departments query'),
        description='List of departments.')

    category = graphene.Field(
        Category, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a category by ID.')
    categories = FilterInputConnectionField(
        Category,
        filter=CategoryFilterInput(description="Filter option for category"),
        level=graphene.Argument(graphene.Int),
        description='List of categories.')

    brand = graphene.Field(
        Brand, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a brand by ID.')
    brands = FilterInputConnectionField(
        Brand,
        filter=BrandFilterInput(description="Filter options for brands"),
        description='List of brands.')

    template = graphene.Field(
        ProductTemplate,
        id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a a product template by ID.')
    templates = FilterInputConnectionField(
        ProductTemplate,
        sort_by=TemplateSortInput(description="Sort products."),
        filter=TemplateFilterInput(description="Filtering options for products."),
        description='List of product templates.')

    template_attributes = FilterInputConnectionField(
        ProductTemplateAttribute, id=graphene.ID(
            description='List of product template attributes by ID'),
        description='List of product template attributes.')

    product_master = graphene.Field(
        ProductMaster, id=graphene.Argument(graphene.ID, required=True),
        description='Lookup a a product master by ID.')
    product_masters = FilterInputConnectionField(
        ProductMaster,
        sort_by=MasterSortInput(description="Sort products."),
        filter=MasterFilterInput(description="Filter options for product masters"),
        description='List of product masters.')


    def resolve_search_products(self, info,  query=None, **kwargs):
        kwargs['filter']['search'] = query
        return resolve_templates(info, kwargs)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_category(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Category)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_categories(self, info, level=None, **kwargs):
        return resolve_categories(info, level=level, **kwargs)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_brand(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Brand)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_brands(self, info, **kwargs):
        return resolve_brands(info, **kwargs)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_attribute(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Attribute)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_attributes(self, info, query=None, **kwargs):
        return resolve_attributes(info, query=query)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_group_attribute(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, AttributeGroup)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_group_attributes(self, info, query=None, **kwargs):
        return resolve_group_attributes(info, query=query)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_department(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, Department)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_departments(self, info, query=None, **kwargs):
        return resolve_departments(info, query=query)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_templates(self, info, **kwargs):
        return resolve_templates(info,  **kwargs)

    @permission_required(['products', 'store_products'])
    @role_required([UserType.ADMIN.value, UserType.STORE.value])
    def resolve_template(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductTemplate)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_template_attributes(self, info, id, **kwargs):
        template = graphene.Node.get_node_from_global_id(info, id, ProductTemplate)
        return resolve_product_template_attributes(info, id=template.id)

    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def resolve_product_masters(self, info, **kwargs):
        return resolve_product_masters(info, **kwargs)

    @permission_required(['products', 'store_products'])
    @role_required([UserType.ADMIN.value, UserType.STORE.value])
    def resolve_product_master(self, info, id):
        return graphene.Node.get_node_from_global_id(info, id, ProductMaster)


class ProductMutations(graphene.ObjectType):
    create_attribute = AttributeCreate.Field()
    update_attribute = AttributeUpdate.Field()
    delete_attribute = AttributeDelete.Field()

    create_attribute_group = AttributeGroupCreate.Field()
    update_attribute_group = AttributeGroupUpdate.Field()
    delete_attribute_group = AttributeGroupDelete.Field()

    create_department = DepartmentCreate.Field()
    update_department = DepartmentUpdate.Field()
    change_department_status = DepartmentChangeStatus.Field()

    create_category = CategoryCreate.Field()
    update_category = CategoryUpdate.Field()
    change_category_status = CategoryChangeStatus.Field()

    create_brand = BrandCreate.Field()
    update_brand = BrandUpdate.Field()
    change_brand_status = BrandChangeStatus.Field()

    create_product_template = ProductTemplateCreate.Field()
    update_product_template = ProductTemplateUpdate.Field()
    change_product_template_status = ProductTemplateChangeStatus.Field()

    create_product_template_attribute = ProductTemplateAttributeCreate.Field()
    create_product_template_manufacture = ProductTemplateManufactureCreate.Field()
    create_product_template_description = ProductTemplateDescriptionCreate.Field()
    create_product_template_ingredient = ProductTemplateIngredientCreate.Field()
    create_product_template_nutrition = ProductTemplateNutritionCreate.Field()
    create_product_template_how_to_use = ProductTemplateHowToUseCreate.Field()
    create_product_template_caution_message = ProductTemplateCautionMessageCreate.Field()
    create_product_template_certification = ProductTemplateCertificationCreate.Field()
    create_template_attribute_group = ProductTemplateAttributeGroupCreate.Field()
    create_product_template_warranty = ProductTemplateWarrantyCreate.Field()
    create_product_template_include = ProductTemplateIncludeCreate.Field()
    create_product_template_policy = ProductTemplatePolicyCreate.Field()

    create_product_master = ProductMasterCreate.Field()
    update_product_master = ProductMasterListUpdate.Field()
    change_product_master_status = ProductMasterChangeStatus.Field()

    create_related_products = ProductTemplateRelatedProductCreate.Field()

    check_barcode_exist = CheckBarcodeExist.Field()
