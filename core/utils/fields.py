from functools import partial
import graphene
from django.db.models.query import QuerySet
from graphene.relay import PageInfo
from graphene_django.fields import DjangoConnectionField
from graphql_relay.connection.arrayconnection import connection_from_list_slice
from promise import Promise



def patch_pagination_args(field: DjangoConnectionField):
    """Add descriptions to pagination arguments in a connection field.
    By default Graphene's connection fields comes without description for pagination
    arguments. This functions patches those fields to add the descriptions.
    """
    field.args["first"].description = "Return the first n elements from the list."
    field.args["last"].description = "Return the last n elements from the list."
    field.args[
        "before"
    ].description = (
        "Return the elements in the list that come before the specified cursor."
    )
    field.args[
        "after"
    ].description = (
        "Return the elements in the list that come after the specified cursor."
    )
    field.args["offset"].description = "Return the first n elements from the list."
    field.args["limit"].description = "Return the last n elements from the list."


class BaseConnectionField(graphene.ConnectionField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, offset=graphene.Int(), limit=graphene.Int(), **kwargs)
        patch_pagination_args(self)

class BaseDjangoConnectionField(DjangoConnectionField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, offset=graphene.Int(), limit=graphene.Int(), **kwargs)
        patch_pagination_args(self)

class PrefetchingConnectionField(BaseDjangoConnectionField):
    @classmethod
    def connection_resolver(
        cls,
        resolver,
        connection,
        default_manager,
        queryset_resolver,
        max_limit,
        enforce_first_or_last,
        root,
        info,
        **args,
    ):

        # Disable `enforce_first_or_last` if not querying for `edges`.
        values = [
            field.name.value for field in info.field_asts[0].selection_set.selections
        ]
        if "edges" not in values:
            enforce_first_or_last = False

        return super().connection_resolver(
            resolver,
            connection,
            default_manager,
            queryset_resolver,
            max_limit,
            enforce_first_or_last,
            root,
            info,
            **args,
        )

    @classmethod
    def resolve_connection(cls, connection, args, iterable):

        offset = args.get("offset")
        limit = args.get("limit")
        item_length = args.get("item_length")
        filter = args.get("filter") or None
        have_length = False

        if item_length :
            have_length = True

        if have_length:
            _len = item_length
        elif isinstance(iterable, QuerySet):
            _len = iterable.count()
        else:
            _len = len(iterable)

        if offset is not None and limit and iterable and isinstance(iterable, QuerySet) and have_length is False:
            iterable = iterable[offset:limit + offset]

        connection = connection_from_list_slice(
            iterable,
            args,
            slice_start=0,
            list_length=_len,
            list_slice_length=_len,
            connection_type=connection,
            edge_type=connection.Edge,
            pageinfo_type=PageInfo,
        )
        connection.iterable = iterable
        connection.length = 50
        return connection


class FilterInputConnectionField(BaseDjangoConnectionField):
    def __init__(self, *args, **kwargs):
        self.filter_field_name = kwargs.pop("filter_field_name", "filter")
        self.filter_input = kwargs.get(self.filter_field_name)
        self.filterset_class = None
        if self.filter_input:
            self.filterset_class = self.filter_input.filterset_class
        super().__init__(*args, **kwargs)

    @classmethod
    def resolve_connection(cls, connection, args, iterable):

        offset = args.get("offset")
        limit = args.get("limit")
        item_length = args.get("item_length")
        filter = args.get("filter") or None
        have_length = False

        if item_length:
            have_length = True

        if have_length:
            _len = item_length
        elif isinstance(iterable, QuerySet):
            _len = iterable.count()
        else:
            _len = len(iterable)

        if offset is not None and limit and iterable and isinstance(iterable, QuerySet) and have_length is False:
            iterable = iterable[offset:limit+offset]

        connection = connection_from_list_slice(
            iterable,
            args,
            slice_start=0,
            list_length=_len,
            list_slice_length=_len,
            connection_type=connection,
            edge_type=connection.Edge,
            pageinfo_type=PageInfo,
        )
        connection.iterable = iterable
        connection.length = _len
        return connection


    @classmethod
    def connection_resolver(
        cls,
        resolver,
        connection,
        default_manager,
        queryset_resolver,
        max_limit,
        enforce_first_or_last,
        filterset_class,
        filters_name,
        root,
        info,
        **args,
    ):

        # Disable `enforce_first_or_last` if not querying for `edges`.
        values = [
            field.name.value for field in info.field_asts[0].selection_set.selections
        ]
        if "edges" not in values:
            enforce_first_or_last = False

        first = args.get("first")
        last = args.get("last")

        if enforce_first_or_last:
            assert first or last, (
                "You must provide a `first` or `last` value to properly "
                "paginate the `{}` connection."
            ).format(info.field_name)

        if max_limit:
            if first:
                assert first <= max_limit, (
                    "Requesting {} records on the `{}` connection exceeds the "
                    "`first` limit of {} records."
                ).format(first, info.field_name, max_limit)
                args["first"] = min(first, max_limit)

            if last:
                assert last <= max_limit, (
                    "Requesting {} records on the `{}` connection exceeds the "
                    "`last` limit of {} records."
                ).format(last, info.field_name, max_limit)
                args["last"] = min(last, max_limit)

        response = resolver(root, info, **args)

        if type(response) == tuple:
            iterable = response[0]
            args['item_length'] = response[1]
        else:
            iterable = response
            args['item_length'] = None

        if iterable is None:
            iterable = default_manager
        # thus the iterable gets refiltered by resolve_queryset
        # but iterable might be promise
        iterable = queryset_resolver(connection, iterable, info, args)

        on_resolve = partial(cls.resolve_connection, connection, args)

        filter_input = args.get(filters_name)

        if filter_input and filterset_class and args['item_length'] is None:
            iterable = filterset_class(
                data=dict(filter_input), queryset=iterable, request=info.context
            ).qs

        if Promise.is_thenable(iterable):
            return Promise.resolve(iterable).then(on_resolve)
        return on_resolve(iterable)

    def get_resolver(self, parent_resolver):
        return partial(
            super().get_resolver(parent_resolver),
            self.filterset_class,
            self.filter_field_name,
        )