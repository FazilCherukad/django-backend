from django.db import models
from django.db.models import F, Max, Q
from django.db.models import ProtectedError
from django.db import Error as DBError, transaction
from simple_history.models import HistoricalRecords

from core.enums.enum import Status

# Create your models here.

class IPAddressHistoricalModel(models.Model):
    ip_address = models.GenericIPAddressField(default='127.0.0.1')

    class Meta:
        abstract = True

class SimpleHistory(models.Model):
    history = HistoricalRecords(inherit=True, bases=[IPAddressHistoricalModel, ])

    class Meta:
        abstract = True

class CoreModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class BaseModel(CoreModel, SimpleHistory):

    class Meta:
        abstract = True

class ExportModel(models.Model):
    last_exported = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True



class SoftDeleteQuerySet(models.QuerySet):

  @transaction.atomic
  def change_status(self, status=None):
      for x in self:
        x.change_status(status=status)

  def get_queryset(self):
      self.get_queryset().all()

class SoftDeleteManager(models.Manager):

  def __init__(self, *args, **kwargs):
    self.all_records = kwargs.pop('all_records', False)
    self.active_records = kwargs.pop('active_records', False)
    self.deleted_records = kwargs.pop('deleted_records', False)
    self.with_stock_and_price = kwargs.pop('with_stock_and_price', False)
    super(SoftDeleteManager, self).__init__(*args, **kwargs)

  def _base_queryset(self):
    return super().get_queryset().all()

  def get_queryset(self):
    if self.active_records and self.with_stock_and_price:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(status='ACTIVE', stock__gt=0, retail_price__gt=0)
    if self.active_records:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(status='ACTIVE')
    if self.deleted_records:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(status='DELETED')
    if self.all_records:
        return SoftDeleteQuerySet(self.model, using=self._db)
    if hasattr(self.model, 'status'):
        return SoftDeleteQuerySet(self.model, using=self._db).exclude(status='DELETED')
    if hasattr(self.model, 'active'):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(active=True)

  def change_status(self):
      return self.get_queryset().change_status()


class SoftDeleteModel(CoreModel):
    status = models.CharField(max_length=10, choices=[(type.name, type.value) for type in Status],
                              default=Status.ACTIVE.value)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(all_records=True)
    active_records = SoftDeleteManager(active_records=True)
    deleted_objects = SoftDeleteManager(deleted_records=True)

    class Meta:
        abstract = True

    @transaction.atomic
    def change_status_non_cascade(self, status, **kwargs):
        if hasattr(self, 'status'):
            result = self.validate_choices(status)
            if result is None or True:
                self.status = status
                self.save()
        elif hasattr(self, 'active'):
            self.active = False
            self.save()
        raise DBError

    @transaction.atomic
    def change_status(self, status, **kwargs):
        if hasattr(self, 'status'):
            result = self.validate_choices(status)
            if result is None or True:
                self.status = status
                self.save()
                self._on_change_status(**kwargs)
            else:
                raise DBError('Invalid choice')
        elif hasattr(self, 'active'):
            self.active = False
            self.save()
        else:
            self.delete()

    def validate_choices(self, status):
        field = self._meta.get_field('status')
        found = None
        if len(field.choices) > 0:
            found = False
            for choice in field.choices:
                if choice[0] == status:
                    found = True
                    break
        return found


    def _on_change_status(self, **kwargs):

        for relation in self._meta._relation_tree:
            on_delete = getattr(relation.remote_field, 'on_delete', models.DO_NOTHING)
            if on_delete in [None, models.DO_NOTHING]:
                continue

            filter = {relation.name: self}
            related_queryset = relation.model.objects.filter(**filter)

            if on_delete == models.CASCADE:
                obj = relation.model.objects.filter(**filter)
                if issubclass(relation.model, SoftDeleteModel):
                    obj.change_status(self.status)
                else:
                    obj.delete(**kwargs)
            elif on_delete == models.SET_NULL:
                pass

            elif on_delete == models.PROTECT:
                if related_queryset.count() > 0:
                    raise ProtectedError()
            else:
                raise (NotImplementedError())


class SoftDeleteHistoryModel(SoftDeleteModel, SimpleHistory):

    class Meta:
        abstract = True

class SoftDeleteHistoryStoreProductModel(SoftDeleteHistoryModel):

    active_records = SoftDeleteManager(active_records=True, with_stock_and_price=True)

    class Meta:
        abstract = True

class SortableModel(models.Model):
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    class Meta:
        abstract = True

    def get_ordering_queryset(self):
        raise NotImplementedError("Unknown ordering queryset")

    def get_max_sort_order(self, qs):
        existing_max = qs.aggregate(Max("sort_order"))
        existing_max = existing_max.get("sort_order__max")
        return existing_max

    def save(self, *args, **kwargs):
        # if self.pk is None:
        #     qs = self.get_ordering_queryset()
        #     existing_max = self.get_max_sort_order(qs)
        #     self.sort_order = 0 if existing_max is None else existing_max + 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # if self.sort_order is not None:
        #     qs = self.get_ordering_queryset()
        #     qs.filter(sort_order__gt=self.sort_order).update(
        #         sort_order=F("sort_order") - 1
        #     )
        super().delete(*args, **kwargs)




