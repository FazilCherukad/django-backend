import graphene

from core.types.sort_input import SortInputObjectType

class TemplateSortField(graphene.Enum):
    NAME = "name"
    DATE = "updated"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            TemplateSortField.NAME.name: "name",
            TemplateSortField.DATE.name: "update date"
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class TemplateSortInput(SortInputObjectType):
    class Meta:
        sort_enum = TemplateSortField
        type_name = "product templates"

class MasterSortField(graphene.Enum):
    NAME = "product_template__name"
    DATE = "updated"

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            MasterSortField.NAME.name: "name",
            MasterSortField.DATE.name: "update date"
        }
        if self.name in descriptions:
            return f"Sort products by {descriptions[self.name]}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class MasterSortInput(SortInputObjectType):
    class Meta:
        sort_enum = MasterSortField
        type_name = "product templates"