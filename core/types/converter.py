from django.contrib.gis.db.models.fields import PointField, PolygonField
from graphene_django.converter import convert_django_field
from graphene import List, String
from graphene_django.forms.converter import convert_form_field

from core.utils.filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter


@convert_form_field.register(ObjectTypeFilter)
@convert_form_field.register(EnumFilter)
def convert_convert_enum(field):
    return field.input_class()

@convert_form_field.register(ListObjectTypeFilter)
def convert_list_object_type(field):
    return List(field.input_class)

@convert_django_field.register(PointField)
def convert_point_field_to_string(field, registry=None, input_flag=None, nested_fields=False):
    return String(description=field.help_text or field.verbose_name,
                  required=not field.null and input_flag == 'create')

@convert_django_field.register(PolygonField)
def convert_polygon_field_to_string(field, registry=None, input_flag=None, nested_fields=False):
    return String(description=field.help_text or field.verbose_name,
                  required=not field.null and input_flag == 'create')
