import graphene
from .enum import MeasureType as MeasureTypeNormal
from .enum import TimeType as NormalTimeType
from .enum import WarrantyType as NormalWarrantyType
from .enum import PolicyType as NormalPolicyType
from .enum import ProductPackingType as NormalProductPackingType, FileType as NormalFileType, \
    Maturity as NormalMaturity, Priority as NormalPriority
from .enum import ShippingChargeBy as NormalShippingChargeBy, DeliveryType as NormalDeliveryType, \
    PaymentOption as NormalPaymentOption, WeekDay as NormalWeekDay

MeasureType = graphene.Enum(
    'MeasureType',
    [(type.name, type.value) for type in MeasureTypeNormal])

TimeType = graphene.Enum(
    'TimeType',
    [(type.name, type.value) for type in NormalTimeType]
)

WarrantyType = graphene.Enum(
    'WarrantyType',
    [(type.name, type.value) for type in NormalWarrantyType]
)

PolicyType = graphene.Enum(
    'PolicyType',
    [(type.name, type.value) for type in NormalPolicyType]
)

ProductPackingType = graphene.Enum(
    'ProductPackingType',
    [(type.name, type.value) for type in NormalProductPackingType]
)

FileType = graphene.Enum(
    'FileType',
    [(type.name, type.value) for type in NormalFileType]
)

Maturity = graphene.Enum(
    'Maturity',
    [(type.name, type.value) for type in NormalMaturity]
)

Priority = graphene.Enum(
    'Priority',
    [(type.name, type.value) for type in NormalPriority]
)

ShippingChargeBy = graphene.Enum(
    'ShippingChargeBy',
    [(type.name, type.value) for type in NormalShippingChargeBy]
)

DeliveryType = graphene.Enum(
    'DeliveryType',
    [(type.name, type.value) for type in NormalDeliveryType]
)

PaymentOption = graphene.Enum(
    'PaymentOption',
    [(type.name, type.value) for type in NormalPaymentOption]
)

WeekDay = graphene.Enum(
    'WeekDay',
    [(type.name, type.value) for type in NormalWeekDay]
)

class ReportingPeriod(graphene.Enum):
    TODAY = 'TODAY'
    THIS_MONTH = 'THIS_MONTH'