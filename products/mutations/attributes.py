import re
from django.core.exceptions import ValidationError
from django.db import Error as DBError, transaction
from django.template.defaultfilters import slugify
import graphene

from core.utils.decorators import permission_required, role_required
from core.utils.mutations import ModelMutation, ModelDeleteMutation
from refs.types import AttributeType
from refs.types import Icon
from core.enums.enum import UserType
from .. import models
from ..types import Attribute, AttributeGroup


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Attribute value name")
    value = graphene.String(description="Attribute value")
    sort_order = graphene.Int(description="Sort order for attribute values")

class AttributeCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Attribute name")
    icon = graphene.ID(description='Icon ID')
    qty_attribute = graphene.Boolean(description="Is it a variant of quantity")
    values = graphene.List(
        AttributeValueCreateInput, description="Attribute values")

class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="Attribute name")
    qty_attribute = graphene.Boolean(description="Is it a variant of quantity")
    remove_values = graphene.List(
        graphene.ID, name='removeValues',
        description='IDs of values to be removed from this attribute.')
    add_values = graphene.List(
        AttributeValueCreateInput, name='addValues',
        description='New values to be created for this attribute.')

class AttributeGroupItemCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Attribute group item name")
    icon = graphene.ID(description="Item icon ID")

class AttributeGroupCreateInput(graphene.InputObjectType):
    name = graphene.String(
        required=True, description="Attribute group name")
    items = graphene.List(
        AttributeGroupItemCreateInput, description="Attribute group items")

class AttributeGroupUpdateInput(graphene.InputObjectType):
    name = graphene.String(description="Attribute group name")
    remove_items = graphene.List(
        graphene.ID, name='removeItems',
        description='IDs of items to be removed from this attribute group.')
    add_items = graphene.List(
        AttributeGroupItemCreateInput, name='addItems',
        description='New items to be created for this attribute group.')

class AttributeGroupMixin:

    @classmethod
    def check_unique_items(cls, info, values_input, attribute_group, errors):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute_group.items.values_list('slug', flat=True)
        for value_data in values_input:
            slug = slugify(value_data['name'])
            if slug in existing_values:
                msg = (
                        'Item %s already exists within this attribute group.' %
                        value_data['name'])
                cls.add_error(errors, cls.ATTRIBUTE_VALUES_FIELD, msg)

        new_slugs = [
            slugify(value_data['name']) for value_data in values_input]
        if len(set(new_slugs)) != len(new_slugs):
            cls.add_error(
                errors, cls.ATTRIBUTE_VALUES_FIELD,
                'Provided items are not unique.')

        # Also check value RegX with function value is correct format like color #123456

    @classmethod
    def clean_values(cls, info, cleaned_input, attribute_group, errors):
        """Clean group attribute values.
        Transforms AttributeGroupValueCreateInput into AttributeGroupValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input[cls.ATTRIBUTE_VALUES_FIELD]

        for value_data in values_input:
            value_data['slug'] = slugify(value_data['name'])

            attribute_group_item = models.AttributeGroupItem(
                **value_data, attribute_group=attribute_group)

            try:
                attribute_group_item.full_clean()
            except ValidationError as validation_errors:

                for field in validation_errors.message_dict:
                    if field == 'attribute_group':
                        continue
                    for message in validation_errors.message_dict[field]:
                        cls.add_error(
                            errors, cls.ATTRIBUTE_VALUES_FIELD, message)
        cls.check_unique_items(info, values_input, attribute_group, errors)
        return errors

    @classmethod
    def clean_group_attribute(
            cls, info, instance, cleaned_input, errors):
        if 'name' in cleaned_input:
            slug = slugify(cleaned_input['name'])
        elif instance.pk:
            slug = instance.slug
        else:
            cls.add_error(errors, 'name', 'This field cannot be blank.')
            return cleaned_input
        cleaned_input['slug'] = slug

        if cleaned_input.get('icon'):
            icon = cls.get_node_or_error(
                info, cleaned_input.get('icon'), errors, 'id', Icon)
            if not icon:
                cls.add_error(
                    errors, 'icon',
                    'Icon not found.')

        query = models.AttributeGroup.objects.filter(slug=slug)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            cls.add_error(
                errors, 'name',
                'Attribute group already exists.')
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, attribute_group, cleaned_data):
        super()._save_m2m(info, attribute_group, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            attribute_group.items.create(**value)

class AttributeMixin:

    @classmethod
    def check_expression(cls, attribute_type, value):
        if attribute_type.regx:
            return re.match(attribute_type.regx, value)
        else:
            return True

    @classmethod
    def check_unique_values(cls, info, values_input, attribute, attribute_type, errors):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute.values.values_list('slug', flat=True)
        for value_data in values_input:
            slug = slugify(value_data['name'])
            value = value_data['value']
            if slug in existing_values:
                msg = (
                    'Value %s already exists within this attribute.' %
                    value_data['name'])
                cls.add_error(errors, cls.ATTRIBUTE_VALUES_FIELD, msg)
            if not cls.check_expression(attribute_type, value):
                msg = (
                        'Value %s is not a valid format.' %
                        value_data['value'])
                cls.add_error(errors, cls.ATTRIBUTE_VALUES_FIELD, msg)


        new_slugs = [
            slugify(value_data['name']) for value_data in values_input]
        if len(set(new_slugs)) != len(new_slugs):
            cls.add_error(
                errors, cls.ATTRIBUTE_VALUES_FIELD,
                'Provided values are not unique.')

    @classmethod
    def clean_values(cls, info, cleaned_input, attribute, attribute_type, errors):
        """Clean attribute values.
        Transforms AttributeValueCreateInput into AttributeValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input[cls.ATTRIBUTE_VALUES_FIELD]

        for value_data in values_input:
            value_data['slug'] = slugify(value_data['name'])
            attribute_value = models.AttributeValue(
                **value_data, attribute=attribute)
            try:
                attribute_value.full_clean()
            except ValidationError as validation_errors:
                for field in validation_errors.message_dict:
                    if field == 'attribute':
                        continue
                    for message in validation_errors.message_dict[field]:
                        cls.add_error(
                            errors, cls.ATTRIBUTE_VALUES_FIELD, message)
        cls.check_unique_values(info, values_input, attribute, attribute_type, errors)
        return errors

    @classmethod
    def clean_attribute(
            cls, info, instance, cleaned_input, attribute_type, errors):

        if 'name' in cleaned_input:
            slug = slugify(cleaned_input['name'])
        elif instance.pk:
            slug = instance.slug
        else:
            cls.add_error(errors, 'name', 'This field cannot be blank.')
            return cleaned_input
        cleaned_input['slug'] = slug

        if cleaned_input.get('icon'):
            icon = cls.get_node_or_error(
                info, cleaned_input.get('icon'), errors, 'id', Icon)
            if not icon:
                cls.add_error(
                    errors, 'icon',
                    'Icon not found.')


        if attribute_type:
            cleaned_input['attribute_type'] = attribute_type

        query = models.Attribute.objects.filter(slug=slug)
        query = query.exclude(pk=getattr(instance, 'pk', None))
        if query.exists():
            cls.add_error(
                errors, 'name',
                'Attribute already exists with this name.')
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, attribute, cleaned_data):
        super()._save_m2m(info, attribute, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            attribute.values.create(**value)

class AttributeCreate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = 'values'

    attribute = graphene.Field(Attribute, description='A created Attribute.')
    attribute_type = graphene.Field(AttributeType, description='A created Attribute type.')

    class Arguments:
        attribute_type = graphene.ID(
            required=True,
            description='ID of the AttributeType to create an attribute for.')

        input = AttributeCreateInput(
            required=True,
            description='Fields required to create an attribute.')

    class Meta:
        description = 'Creates an attribute.'
        model = models.Attribute

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, attribute_type, input):
        errors = []
        attribute_type = cls.get_node_or_error(
            info, attribute_type, errors, 'id', AttributeType)

        if not attribute_type:
            cls.add_error(errors, 'attribute_type', 'Attribute type not found')
            return AttributeCreate(errors=errors)

        instance = models.Attribute()
        cleaned_input = cls.clean_input(info, instance, input,  errors)
        cls.clean_attribute(info,
            instance, cleaned_input,attribute_type, errors)
        cls.clean_values(info, cleaned_input, instance, attribute_type, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)

        if errors:
            return AttributeCreate( errors=errors)
        try:
            with transaction.atomic():
                instance.save()
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return AttributeCreate( errors=errors)

        return AttributeCreate( attribute=instance, attribute_type=attribute_type, errors=errors)

class AttributeUpdate(AttributeMixin, ModelMutation):

    ATTRIBUTE_VALUES_FIELD = 'add_values'
    attribute_type = graphene.Field(AttributeType, description='A created Attribute type.')

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to update.')
        input = AttributeUpdateInput(
            required=True,
            description='Fields required to update an attribute.')

    class Meta:
        description = 'Updates attribute.'
        model = models.Attribute

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance, errors):
        """Check if AttributeValues to be removed are assigned to given
        Attribute.
        """
        remove_values = cleaned_input.get('remove_values', [])
        for value in remove_values:
            if value.attribute != instance:
                msg = 'Value %s does not belong to this attribute.' % value
                cls.add_error(errors, 'remove_values', msg)
        return remove_values

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get('remove_values', []):
            attribute_value.delete()

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, id, input):
        errors = []
        instance = cls.get_node_or_error(info, id, errors, 'id', Attribute)

        cleaned_input = cls.clean_input(info, instance, input, errors)
        attribute_type = instance.attribute_type
        cls.clean_attribute(info, instance, cleaned_input, attribute_type, errors)
        cls.clean_values(info, cleaned_input, instance, attribute_type, errors)
        cls.clean_remove_values(cleaned_input, instance, errors)

        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return AttributeUpdate( errors=errors)
        try:
            with transaction.atomic():
                instance.save()
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return AttributeUpdate(errors=errors)

        return AttributeUpdate(attribute=instance, errors=errors)

class AttributeDelete(ModelDeleteMutation):

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to delete.')

    class Meta:
        description = 'Delete attribute.'
        model = models.Attribute

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        super().mutate(root, info, **data)

class AttributeGroupCreate(AttributeGroupMixin, ModelMutation):

    ATTRIBUTE_VALUES_FIELD = 'items'
    attributeGroup = graphene.Field(AttributeGroup, description='A created Attribute group.')

    class Arguments:
        input = AttributeGroupCreateInput(
            required=True,
            description='Fields required to create an attribute group.')

    class Meta:
        description = 'Creates an attribute group.'
        model = models.AttributeGroup

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, input):
        errors = []
        instance = models.AttributeGroup()
        cleaned_input = cls.clean_input(info, instance, input, errors)
        cls.clean_group_attribute(info,
            instance, cleaned_input, errors)
        cls.clean_values(info, cleaned_input, instance, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return AttributeGroupCreate(errors=errors)

        try:
            with transaction.atomic():
                instance.save()
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return AttributeGroupCreate(errors=errors)

        return AttributeGroupCreate( attributeGroup=instance, errors=errors)

class AttributeGroupUpdate(AttributeGroupMixin, ModelMutation):

    ATTRIBUTE_VALUES_FIELD = 'add_items'

    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute group to update.')
        input = AttributeGroupUpdateInput(
            required=True,
            description='Fields required to update an attribute group.')

    class Meta:
        description = 'Updates attribute group.'
        model = models.AttributeGroup

    @classmethod
    def clean_remove_items(cls, cleaned_input, instance, errors):
        """Check if AttributeGroupItems to be removed are assigned to given
        AttributeGroup.
        """
        remove_items = cleaned_input.get('remove_items', [])
        for value in remove_items:
            if value.attribute_group != instance:
                msg = 'Value %s does not belong to this attribute group.' % value
                cls.add_error(errors, 'remove_items', msg)
        return remove_items

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_item in cleaned_data.get('remove_items', []):
            attribute_item.delete()

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, id, input):
        errors = []
        instance = cls.get_node_or_error(info, id, errors, 'id', AttributeGroup)

        cleaned_input = cls.clean_input(info, instance, input, errors)
        cls.clean_group_attribute(info,
            instance, cleaned_input, errors)
        cls.clean_values(info, cleaned_input, instance, errors)
        cls.clean_remove_items(cleaned_input, instance, errors)

        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return AttributeGroupUpdate(errors=errors)

        try:
            with transaction.atomic():
                instance.save()
                cls._save_m2m(info, instance, cleaned_input)
        except DBError as e:
            cls.add_error(errors, 'db', str(e))
            return AttributeGroupCreate(errors=errors)

        return AttributeGroupUpdate(attributeGroup=instance, errors=errors)

class AttributeGroupDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute group to delete.')

    class Meta:
        description = 'Delete attribute group.'
        model = models.AttributeGroup

    @classmethod
    @permission_required('products')
    @role_required([UserType.ADMIN.value])
    def mutate(cls, root, info, **data):
        super().mutate(root, info, **data)