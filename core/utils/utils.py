from django.http.response import HttpResponseBadRequest
from datetime import datetime
import json
import re
import six
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import BytesIO
from django.db.models import Q, QuerySet
import graphene
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_relay import from_global_id
from graphene_django.views import HttpError
from graphene_sentry.views import SentryGraphQLView
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from core.enums.grapheneEnum import ReportingPeriod
from core.types.sort_input import SortInputObjectType
from refs.models import Country

registry = get_global_registry()

class CustomGraphQlView(SentryGraphQLView):

    @staticmethod
    def get_graphql_params(request, data):
        operations = request.GET.get("operations") or data.get("operations")
        if operations:
            if isinstance(operations, six.text_type):
                try:
                    operations = json.loads(operations)
                except Exception:
                    raise HttpError(HttpResponseBadRequest("Operations are invalid JSON."))

            if isinstance(operations, list):
                pass
            else:
                query = operations.get("query")
                variables = operations.get("variables")
                id = operations.get("id")
                map = data.get('map')
                operation_name = operations.get("operationName")

                if variables and isinstance(variables, six.text_type):
                    try:
                        variables = json.loads(variables)
                    except Exception:
                        raise HttpError(HttpResponseBadRequest("Variables are invalid JSON."))

                if map:
                    if isinstance(map, six.text_type):
                        try:
                            map = json.loads(map)
                        except Exception:
                            raise HttpError(HttpResponseBadRequest("Map are invalid JSON."))

                    variables = parse(variables, map, 'variables')

            if operation_name == "null":
                operation_name = None

            return query, variables, operation_name, id
        else:
            query = request.GET.get("query") or data.get("query")
            variables = request.GET.get("variables") or data.get("variables")
            id = request.GET.get("id") or data.get("id")

            if variables and isinstance(variables, six.text_type):
                try:
                    variables = json.loads(variables)
                except Exception:
                    raise HttpError(HttpResponseBadRequest("Variables are invalid JSON."))

            operation_name = request.GET.get("operationName") or data.get("operationName")
            if operation_name == "null":
                operation_name = None

            return query, variables, operation_name, id


def parse(object, map, keyword):
    if isinstance(object, list):
        for index, obj in enumerate(object):
            newkeyword = generateKeyword(keyword, str(index))
            parse(obj, map, newkeyword)
    elif isinstance(object, dict):
        for key, value in object.items():
            if value is None:
                newkeyword = generateKeyword(keyword, str(key))
                keyValue = get_key(map, newkeyword)
                if key:
                    object[key] = keyValue
            elif isinstance(value, dict) or isinstance(value, list):
                newkeyword = generateKeyword(keyword, str(key))
                parse(value, map, newkeyword)
    return object

def generateKeyword(keyword, child):
    if keyword != '':
        keyword = keyword + '.' +child
        return keyword
    return child


def get_key(map, keyword):
    for key, value in map.items():
        if isinstance(value, list):
            for child in value:
                if child == keyword:
                    return key
        if keyword == value:
            return key
    return None

def get_country_group(country_code):
    country = Country.objects.get(code=country_code)
    if country:
        return country.country_group.id
    return None

def formatNumber( num):
    if num % 1 == 0:
        return int(num)
    else:
        return num

def clean_seo_fields(data):
    """Extract and assign seo fields to given dictionary."""
    seo_fields = data.pop('seo', None)
    seo_keywords = []
    if seo_fields:
        data['seo_title'] = seo_fields.get('seo_title')
        data['seo_description'] = seo_fields.get('seo_description')
        keywords = seo_fields.get('seo_keywords') or []
        for keyword in keywords:
            if not keyword in seo_keywords:
                seo_keywords.append(keyword)
        data['seo_keywords'] = seo_keywords


def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    hlen = len(hex)
    return tuple(int(hex[i:i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))

def create_pil_image(image, fields):
    img = Image.open(image)
    draw = ImageDraw.Draw(img)
    import os.path
    SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

    for field in fields:
        x = field.get('x') or 0
        y = field.get('y') or 0
        max_length = field.get('max_length') or 10
        font = field.get('font') or None
        font_size = field.get('font_size') or 16
        font_weight = field.get('font_weight') or 400
        font_color = field.get('font_color') or "#000000"
        italic = field.get('italic') or False
        bold = field.get('bold') or False
        spacing = field.get('spacing') or 5
        lines = field.get('lines') or 1
        value = field.get('value') or 'Blank'
        multiline_spacing = field.get('multiline_spacing') or 0

        font = ImageFont.truetype(font.font, size=font_size)
        draw.text((x, y), value, fill=hex_to_rgb(font_color), font=font, spacing=spacing)

    buffer = BytesIO()
    img.save(fp=buffer, format='JPEG')
    image_file = InMemoryUploadedFile(buffer, None, image.name, 'image/jpeg', img.size, None)

    return image_file

def snake_to_camel_case(name):
    """Convert snake_case variable name to camelCase."""
    if isinstance(name, str):
        split_name = name.split('_')
        return split_name[0] + "".join(map(str.capitalize, split_name[1:]))
    return name

def to_camel_case(name):
    """Convert snake_case variable name to camelCase."""
    if isinstance(name, str):
        name = name.strip()
        split_name = name.split(' ')
        return " ".join(map(str.capitalize, split_name))
    return name


def str_to_enum(name):
    """Create an enum value from a string."""
    return name.replace(' ', '_').replace('-', '_').upper()


def validate_image_file(mutation_cls, file, field_name, errors):
    """Validate if the file is an image."""
    if not file.content_type.startswith('image/'):
        mutation_cls.add_error(errors, field_name, 'Invalid file type')

def validate_font(mutation_cls, file, field_name, errors):
    if not file.content_type.startswith('application/octet-stream'):
        mutation_cls.add_error(errors, field_name, 'Invalid file type')


def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return re.match(regex, url) is not None




def get_database_id(info, node_id, only_type):
    """Get a database ID from a node ID of given type."""
    _type, _id = graphene.relay.Node.from_global_id(node_id)
    graphene_type = info.schema.get_type(_type).graphene_type
    if graphene_type != only_type:
        raise AssertionError('Must receive a %s id.' % only_type._meta.name)
    return _id


def get_nodes(ids, graphene_type=None):
    """Return a list of nodes.
    If the `graphene_type` argument is provided, the IDs will be validated
    against this type. If the type was not provided, it will be looked up in
    the Graphene's registry. Raises an error if not all IDs are of the same
    type.
    """
    pks = []
    types = []
    invalid_ids = []
    error_msg = "Could not resolve to a nodes with the global id list of '%s'."
    for graphql_id in ids:
        if graphql_id:
            try:
                _type, _id = from_global_id(graphql_id)
            except Exception:
                invalid_ids.append(graphql_id)
            else:
                if graphene_type:
                    assert str(graphene_type) == _type, (
                        'Must receive an {} id.').format(
                            graphene_type._meta.name)
                pks.append(_id)
                types.append(_type)
    if invalid_ids:
        raise GraphQLError(
            error_msg % invalid_ids)

    # If `graphene_type` was not provided, check if all resolved types are
    # the same. This prevents from accidentally mismatching IDs of different
    # types.
    if types and not graphene_type:
        assert len(set(types)) == 1, 'Received IDs of more than one type.'
        # get type by name
        type_name = types[0]
        for model, _type in registry._registry.items():
            if _type._meta.name == type_name:
                graphene_type = _type
                break

    nodes = list(graphene_type._meta.model.objects.filter(pk__in=pks))
    nodes.sort(key=lambda e: pks.index(str(e.pk)))  # preserve order in pks
    if not nodes:
        raise GraphQLError(
            error_msg % ids)
    nodes_pk_list = [str(node.pk) for node in nodes]
    for pk in pks:
        assert pk in nodes_pk_list, (
            'There is no node of type {} with pk {}'.format(_type, pk))
    return nodes


def filter_by_query_param(queryset, query, search_fields):
    """Filter queryset according to given parameters.
    Keyword arguments:
    queryset - queryset to be filtered
    query - search string
    search_fields - fields considered in filtering
    """
    if query:
        query_by = {
            '{0}__{1}'.format(
                field, 'icontains'): query for field in search_fields}
        query_objects = Q()
        for q in query_by:
            query_objects |= Q(**{q: query_by[q]})
        return queryset.filter(query_objects).distinct()
    return queryset

def sort_queryset(
    queryset: QuerySet, sort_by: SortInputObjectType, sort_enum: graphene.Enum
) -> QuerySet:
    """Sort queryset according to given parameters.

    Keyword Arguments:
        queryset - queryset to be filtered
        sort_by - dictionary with sorting field and direction

    """

    if sort_by is None:
        return queryset

    if isinstance(sort_by, dict):
        direction = sort_by['direction']
        sorting_field = sort_by['field']
    else:
        direction = sort_by.direction
        sorting_field = sort_by.field

    if not sorting_field:
        return queryset

    custom_sort_by = getattr(sort_enum, f"sort_by_{sorting_field}", None)
    if custom_sort_by:
        return custom_sort_by(queryset, sort_by)
    return queryset.order_by(f"{direction}{sorting_field}")


def reporting_period_to_date(period):
    now = datetime.now()
    if period == ReportingPeriod.TODAY:
        start_date = now.replace(
            hour=0, minute=0, second=0, microsecond=0)
    elif period == ReportingPeriod.THIS_MONTH:
        start_date = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError('Unknown period: %s' % period)
    return start_date


def filter_by_period(queryset, period, field_name):
    start_date = reporting_period_to_date(period)
    return queryset.filter(**{'%s__gte' % field_name: start_date})


def generate_query_argument_description(search_fields):
    header = 'Supported filter parameters:\n'
    supported_list = ''
    for field in search_fields:
        supported_list += '* {0}\n'.format(field)
    return header + supported_list


# def format_permissions_for_display(permissions):
#     """Transform permissions queryset into PermissionDisplay list.
#     Keyword arguments:
#     permissions - queryset with permissions
#     """
#     formatted_permissions = []
#     for permission in permissions:
#         codename = '.'.join(
#             [permission.content_type.app_label, permission.codename])
#         formatted_permissions.append(
#             PermissionDisplay(
#                 code=PermissionEnum.get(codename),
#                 name=permission.name))
#     return formatted_permissions