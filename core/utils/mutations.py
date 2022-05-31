from itertools import chain
from textwrap import dedent

import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models.fields.files import FileField
from graphene.types.mutation import MutationOptions
from graphene_django.registry import get_global_registry
from graphql.error import GraphQLError
from graphql_jwt import ObtainJSONWebToken, Verify
from graphql_jwt.exceptions import JSONWebTokenError, PermissionDenied

from django.db import Error as DBError, transaction

from account import models
from account.types import User
from core.utils.utils import get_nodes
from core.types import Error, Upload
from core.utils.utils import snake_to_camel_case

registry = get_global_registry()


def get_model_name(model):
    """Return name of the model with first letter lowercase."""
    model_name = model.__name__
    return model_name[:1].lower() + model_name[1:]


def get_output_fields(model, return_field_name):
    """Return mutation output field for model instance."""
    model_type = registry.get_type_for_model(model)
    if not model_type:
        raise ImproperlyConfigured(
            'Unable to find type for model %s in graphene registry' %
            model.__name__)
    fields = {return_field_name: graphene.Field(model_type)}
    return fields


class ModelMutationOptions(MutationOptions):
    exclude = None
    model = None
    return_field_name = None


class BaseMutation(graphene.Mutation):
    errors = graphene.List(
        graphene.NonNull(Error),
        description='List of errors that occurred executing the mutation.')

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, description=None, **options):
        if not description:
            raise ImproperlyConfigured('No description provided in Meta')
        description = dedent(description)
        super().__init_subclass_with_meta__(description=description, **options)

    @classmethod
    def _update_mutation_arguments_and_fields(cls, arguments, fields):
        cls._meta.arguments.update(arguments)
        cls._meta.fields.update(fields)

    @classmethod
    def add_error(cls, errors, field, message):
        """Add a mutation user error.
        `errors` is the list of errors that happened during the execution of
        the mutation. `field` is the name of an input field the error is
        related to. `None` value is allowed and it indicates that the error
        is general and is not related to any of the input fields. `message`
        is the actual error message to be returned in the response.
        As a result of this method, the `errors` list is updated with an Error
        object to be returned as mutation result.
        """
        field = snake_to_camel_case(field)
        # if field:
        #     errors.append({'field':field, 'message':message})
        # else:
        #     errors.append({ 'message': message})
        errors.append(Error(field=field, message=message))

    @classmethod
    def get_node_or_error(cls, info, global_id, errors, field, only_type=None):

        if not global_id:
            return None
        node = None
        try:
            node = graphene.Node.get_node_from_global_id(
                info, global_id, only_type)
        except (AssertionError, GraphQLError) as e:
            cls.add_error(errors, field, str(e))
        else:
            if node is None:
                message = "Couldn't resolve to a node: %s" % global_id
                cls.add_error(errors, field, message)
        return node

    @classmethod
    def get_nodes_or_error(cls, ids, errors, field, only_type=None):
        instances = None
        try:
            instances = get_nodes(ids, only_type)
        except GraphQLError as e:
            cls.add_error(field=field, message=str(e), errors=errors)
        return instances

    @classmethod
    def clean_instance(cls, instance, errors):
        """Clean the instance that was created using the input data.
        Once a instance is created, this method runs `full_clean()` to perform
        model fields' validation. Returns errors ready to be returned by
        the GraphQL response (if any occurred).
        """
        try:
            instance.full_clean()
        except ValidationError as validation_errors:
            message_dict = validation_errors.message_dict
            for field in message_dict:
                if hasattr(cls._meta,
                           'exclude') and field in cls._meta.exclude:
                    continue
                for message in message_dict[field]:
                    field = snake_to_camel_case(field)
                    cls.add_error(errors, field, message)

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        """Fill instance fields with cleaned data.
        The `instance` argument is either an empty instance of a already
        existing one which was fetched from the database. `cleaned_data` is
        data to be set in instance fields. Returns `instance` with filled
        fields, but not saved to the database.
        """
        from django.db import models
        opts = instance._meta

        for f in opts.fields:
            if any([not f.editable, isinstance(f, models.AutoField),
                    f.name not in cleaned_data]):
                continue
            data = cleaned_data[f.name]

            if data is None:
                # We want to reset the file field value when None was passed
                # in the input, but `FileField.save_form_data` ignores None
                # values. In that case we manually pass False which clears
                # the file.
                if isinstance(f, FileField):
                    data = False
                if not f.null:
                    data = f._get_default()
            f.save_form_data(instance, data)
        return instance


class ModelMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
            cls,
            arguments=None,
            model=None,
            exclude=None,
            return_field_name=None,
            _meta=None,
            **options):
        if not model:
            raise ImproperlyConfigured('model is required for ModelMutation')
        if not _meta:
            _meta = ModelMutationOptions(cls)

        if exclude is None:
            exclude = []

        if not return_field_name:
            return_field_name = get_model_name(model)
        if arguments is None:
            arguments = {}
        fields = get_output_fields(model, return_field_name)

        _meta.model = model
        _meta.return_field_name = return_field_name
        _meta.exclude = exclude
        super().__init_subclass_with_meta__(_meta=_meta, **options)
        cls._update_mutation_arguments_and_fields(
            arguments=arguments, fields=fields)

    @classmethod
    def clean_uid(cls, info, cleaned_data):
        user = models.User.objects.get(pk=1)
        cleaned_data['write'] = user
        cleaned_data['create'] = user
        return cleaned_data



    @classmethod
    def clean_input(cls, info, instance, input, errors, inputCls=None):
        """Clean input data received from mutation arguments.
        Fields containing IDs or lists of IDs are automatically resolved into
        model instances. `instance` argument is the model instance the mutation
        is operating on (before setting the input data). `input` is raw input
        data the mutation receives. `errors` is a list of errors that occurred
        during mutation's execution.
        Override this method to provide custom transformations of incoming
        data.
        """

        def is_list_of_ids(field):
            return (
                isinstance(field.type, graphene.List)
                and field.type.of_type == graphene.ID)

        def is_id_field(field):
            return (
                field.type == graphene.ID
                or isinstance(field.type, graphene.NonNull)
                and field.type.of_type == graphene.ID)

        def is_upload_field(field):
            if hasattr(field.type, 'of_type'):
                return field.type.of_type == Upload
            return field.type == Upload

        if inputCls:
            InputCls = inputCls
        else:
            InputCls = getattr(cls.Arguments, 'input')



        cleaned_input = {}
        for field_name, field in InputCls._meta.fields.items():
            if field_name in input:
                value = input[field_name]
                # handle list of IDs field
                if value is not None and is_list_of_ids(field):
                    instances = cls.get_nodes_or_error(
                        value, errors=errors,
                        field=field_name) if value else []
                    cleaned_input[field_name] = instances

                # handle ID field
                elif value is not None and is_id_field(field):
                    instance = cls.get_node_or_error(
                        info, value, errors=errors, field=field_name)
                    cleaned_input[field_name] = instance

                # handle uploaded files
                elif value is not None and is_upload_field(field):
                    value = info.context.FILES.get(value)
                    cleaned_input[field_name] = value

                # handle other fields
                else:
                    cleaned_input[field_name] = value
        # cleaned_input = cls.clean_uid(info,cleaned_input)
        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        opts = instance._meta
        for f in chain(opts.many_to_many, opts.private_fields):
            if not hasattr(f, 'save_form_data'):
                continue
            if f.name in cleaned_data and cleaned_data[f.name] is not None:
                f.save_form_data(instance, cleaned_data[f.name])

    @classmethod
    def user_is_allowed(cls, user, input):
        """Determine whether user has rights to perform this mutation.
        Default implementation assumes that user is allowed to perform any
        mutation. By overriding this method, you can restrict access to it.
        `user` is the User instance associated with the request and `input` is
        the input data provided as mutation arguments.
        """
        return True

    @classmethod
    def success_response(cls, instance):
        """Return a success response."""
        return cls(**{cls._meta.return_field_name: instance, 'errors': []})

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

    @classmethod
    def mutate(cls, root, info, **data):
        """Perform model mutation.
        Depending on the input data, `mutate` either creates a new instance or
        updates an existing one. If `id` arugment is present, it is assumed
        that this is an "update" mutation. Otherwise, a new instance is
        created based on the model associated with this mutation.
        """
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        id = data.get('id')
        input = data.get('input')

        # Initialize the errors list.
        errors = []

        # Initialize model instance based on presence of `id` attribute.
        if id:
            model_type = registry.get_type_for_model(cls._meta.model)
            instance = cls.get_node_or_error(
                info, id, errors, 'id', model_type)
        else:
            instance = cls._meta.model()
        if errors:
            return cls(errors=errors)
        cleaned_input = cls.clean_input(info, instance, input, errors)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance, errors)
        if errors:
            return cls(errors=errors)
        try:
            with transaction.atomic():
                cls.save(info, instance, cleaned_input)
                cls._save_m2m(info, instance, cleaned_input)
                return cls.success_response(instance)
        except DBError as e:
            return cls(errors=[Error(field='Db', message=str(e))])


class ModelDeleteMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance, errors):
        """Perform additional logic before deleting the model instance.
        Override this method to raise custom validation error and abort
        the deletion process.
        """

    @classmethod
    def mutate(cls, root, info, **data):
        """Perform a mutation that deletes a model instance."""
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        errors = []
        node_id = data.get('id')
        model_type = registry.get_type_for_model(cls._meta.model)
        instance = cls.get_node_or_error(
            info, node_id, errors, 'id', model_type)

        if instance:
            cls.clean_instance(info, instance, errors)

        if errors:
            return cls(errors=errors)

        db_id = instance.id
        instance.delete()

        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)

class ModelStatusChangeMutation(ModelMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance, errors):
        """Perform additional logic before deleting the model instance.
        Override this method to raise custom validation error and abort
        the deletion process.
        """

    @classmethod
    def mutate(cls, root, info, **data):
        """Perform a mutation that deletes a model instance."""
        if not cls.user_is_allowed(info.context.user, data):
            raise PermissionDenied()

        errors = []
        node_id = data.get('id')
        status = data.get('status')
        cascade = data.get('cascade') or True
        model_type = registry.get_type_for_model(cls._meta.model)
        instance = cls.get_node_or_error(
            info, node_id, errors, 'id', model_type)
        if instance:
            cls.clean_instance(info, instance, errors)

        if errors:
            return cls(errors=errors)
        db_id = instance.id
        try:
            if cascade:
                instance.change_status(status)
            else:
                instance.change_status_non_cascade(status)
        except DBError as e:
            return cls(errors=[Error(field='Db', message=str(e))])
        # After the instance is deleted, set its ID to the original database's
        # ID so that the success response contains ID of the deleted object.
        instance.id = db_id
        return cls.success_response(instance)

class BaseBulkMutation(BaseMutation):
    count = graphene.Int(
        required=True, description="Returns how many objects were affected."
    )

    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(cls, model=None, _meta=None, **kwargs):
        if not model:
            raise ImproperlyConfigured("model is required for bulk mutation")
        if not _meta:
            _meta = ModelMutationOptions(cls)
        _meta.model = model

        super().__init_subclass_with_meta__(_meta=_meta, **kwargs)

    @classmethod
    def clean_instance(cls, info, instance):
        """Perform additional logic.

        Override this method to raise custom validation error and prevent
        bulk action on the instance.
        """

    @classmethod
    def bulk_action(cls, queryset, **kwargs):
        """Implement action performed on queryset."""
        raise NotImplementedError

    @classmethod
    def perform_mutation(cls, _root, info, ids, **data):
        """Perform a mutation that deletes a list of model instances."""
        clean_instance_ids, errors = [], {}
        # Allow to pass empty list for dummy mutation
        if not ids:
            return 0, errors
        instance_model = cls._meta.model
        model_type = registry.get_type_for_model(instance_model)
        instances = cls.get_nodes_or_error(ids, "id", model_type)
        for instance, node_id in zip(instances, ids):
            instance_errors = []

            # catch individual validation errors to raise them later as
            # a single error
            try:
                cls.clean_instance(info, instance)
            except ValidationError as e:
                msg = ". ".join(e.messages)
                instance_errors.append(msg)

            if not instance_errors:
                clean_instance_ids.append(instance.pk)
            else:
                instance_errors_msg = ". ".join(instance_errors)
                ValidationError({node_id: instance_errors_msg}).update_error_dict(
                    errors
                )

        if errors:
            errors = ValidationError(errors)
        count = len(clean_instance_ids)
        if count:
            qs = instance_model.objects.filter(pk__in=clean_instance_ids)
            cls.bulk_action(queryset=qs, **data)
        return count, errors

    @classmethod
    def mutate(cls, root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()

        count, errors = cls.perform_mutation(root, info, **data)
        if errors:
            return cls.handle_errors(errors, count=count)

        return cls(errors=errors, count=count)


class ModelBulkDeleteMutation(BaseBulkMutation):
    class Meta:
        abstract = True

    @classmethod
    def bulk_action(cls, queryset):
        queryset.delete()
#
#
# class BaseMetadataMutation(BaseMutation):
#     class Meta:
#         abstract = True
#
#     @classmethod
#     def __init_subclass_with_meta__(
#         cls,
#         arguments=None,
#         model=None,
#         public=False,
#         return_field_name=None,
#         _meta=None,
#         **kwargs,
#     ):
#         if not model:
#             raise ImproperlyConfigured("model is required for update meta mutation")
#         if not _meta:
#             _meta = MetaUpdateOptions(cls)
#         if not arguments:
#             arguments = {}
#         if not return_field_name:
#             return_field_name = get_model_name(model)
#         fields = get_output_fields(model, return_field_name)
#
#         _meta.model = model
#         _meta.public = public
#         _meta.return_field_name = return_field_name
#
#         super().__init_subclass_with_meta__(_meta=_meta, **kwargs)
#         cls._update_mutation_arguments_and_fields(arguments=arguments, fields=fields)
#
#     @classmethod
#     def get_store_method(cls, instance):
#         return (
#             getattr(instance, "store_meta")
#             if cls._meta.public
#             else getattr(instance, "store_private_meta")
#         )
#
#     @classmethod
#     def get_meta_method(cls, instance):
#         return (
#             getattr(instance, "get_meta")
#             if cls._meta.public
#             else getattr(instance, "get_private_meta")
#         )
#
#     @classmethod
#     def get_clear_method(cls, instance):
#         return (
#             getattr(instance, "clear_stored_meta_for_client")
#             if cls._meta.public
#             else getattr(instance, "clear_stored_private_meta_for_client")
#         )
#
#     @classmethod
#     def get_instance(cls, info, **data):
#         object_id = data.get("id")
#         if object_id:
#             model_type = registry.get_type_for_model(cls._meta.model)
#             instance = cls.get_node_or_error(info, object_id, only_type=model_type)
#         else:
#             instance = cls._meta.model()
#         return instance
#
#     @classmethod
#     def success_response(cls, instance):
#         """Return a success response."""
#         return cls(**{cls._meta.return_field_name: instance, "errors": []})
#
#
# class MetaUpdateOptions(MutationOptions):
#     model = None
#     return_field_name = None
#     public = False
#
#
# class UpdateMetaBaseMutation(BaseMetadataMutation):
#     class Meta:
#         abstract = True
#
#     class Arguments:
#         id = graphene.ID(description="ID of an object to update.", required=True)
#         input = MetaInput(
#             description="Fields required to update new or stored metadata item.",
#             required=True,
#         )
#
#     @classmethod
#     def perform_mutation(cls, root, info, **data):
#         instance = cls.get_instance(info, **data)
#         get_meta = cls.get_meta_method(instance)
#         store_meta = cls.get_store_method(instance)
#
#         metadata = data.pop("input")
#         stored_data = get_meta(metadata.namespace, metadata.client_name)
#         stored_data[metadata.key] = metadata.value
#         store_meta(
#             namespace=metadata.namespace, client=metadata.client_name, item=stored_data
#         )
#         instance.save()
#         return cls.success_response(instance)
#
#
# class ClearMetaBaseMutation(BaseMetadataMutation):
#     class Meta:
#         abstract = True
#
#     class Arguments:
#         id = graphene.ID(description="ID of a customer to update.", required=True)
#         input = MetaPath(
#             description="Fields required to identify stored metadata item.",
#             required=True,
#         )
#
#     @classmethod
#     def perform_mutation(cls, root, info, **data):
#         instance = cls.get_instance(info, **data)
#         get_meta = cls.get_meta_method(instance)
#         store_meta = cls.get_store_method(instance)
#         clear_meta = cls.get_clear_method(instance)
#
#         metadata = data.pop("input")
#         stored_data = get_meta(metadata.namespace, metadata.client_name)
#
#         cleared_value = stored_data.pop(metadata.key, None)
#         if not stored_data:
#             clear_meta(metadata.namespace, metadata.client_name)
#             instance.save()
#         elif cleared_value is not None:
#             store_meta(
#                 namespace=metadata.namespace,
#                 client=metadata.client_name,
#                 item=stored_data,
#             )
#             instance.save()
#         return cls.success_response(instance)



class CreateToken(ObtainJSONWebToken):
    """Mutation that authenticates a user and returns token and user data.
    It overrides the default graphql_jwt.ObtainJSONWebToken to wrap potential
    authentication errors in our Error type, which is consistent to how rest of
    the mutation works.
    """

    # pass

    errors = graphene.List(Error, required=True)
    user = graphene.Field(User)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        try:
            result = super().mutate(root, info, **kwargs)
        except JSONWebTokenError as e:
            return cls(errors=Error(field='user', message=str(e)))
        else:
            return result

    @classmethod
    def resolve(cls, root, info):
        if info.context.user.has_role(['CUSTOMER']):
            return cls(user=info.context.user, errors=[])
        raise JSONWebTokenError('User does not exist')


class VerifyToken(Verify):
    """Mutation that confirm if token is valid and also return user data."""

    user = graphene.Field(User)

    def resolve_user(self, info, **kwargs):
        username_field = get_user_model().USERNAME_FIELD

        kwargs = {username_field: self.payload.get(username_field)}
        return models.User.objects.get(**kwargs)