from enum import Enum

class AuthType(Enum):
    SINGLE = 'SINGLE'
    TWO_FACTOR_NEW = 'TWO_FACTOR_NEW'
    TWO_FACTOR_OTP = 'TWO_FACTOR_OTP'
    TWO_FACTOR_EMAIL = 'TWO_FACTOR_EMAIL'

class BusinessType(Enum):
    RETAIL = 'RETAIL'
    WHOLESALE = 'WHOLESALE'

class DeliveryMode(Enum):
    STORE = 'STORE'
    A_TEAM = 'A_TEAM'
    OTHER = 'OTHER'

class AddressType(Enum):
    WORK = 'WORK'
    HOME = 'HOME'
    OTHER = 'OTHER'

class PaymentOption(Enum):
    CASH = 'CASH'
    ONLINE = 'ONLINE'
    UPI = 'UPI'

class PaymentStatus(Enum):
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    PENDING = 'PENDING'

class TransactionType(Enum):
    PAYMENT = 'PAYMENT'
    REFUND = 'REFUND'

class LocationType(Enum):
    VILLAGE = 'VILLAGE'
    CITY = 'CITY'
    METRO = 'METRO'
    RURAL = 'RURAL'

class PolicyType(Enum):
    RETURN = 'RETURN'
    RESALE = 'RESALE'
    SALE = 'SALE'
    TAX = 'TAX'
    COMPLAINT = 'COMPLAINT'
    REPLACE = 'REPLACE'

class WarrantyType(Enum):
    REPLACEMENT = 'REPLACEMENT'
    REPAIR = 'REPAIR'

class TimeType(Enum):
    MINUTES = 'MINUTES'
    HOURS = 'HOURS'
    DAYS = 'DAYS'
    WEEK = 'WEEK'
    MONTH = 'MONTH'
    YEAR = 'YEAR'

class BranchType(Enum):
    HEAD = 'HEAD'
    UNIT = 'UNIT'
    SUBUNIT = 'SUBUNIT'
    FACTORY = 'FACTORY'

class ProductPackingType(Enum):
    SINGLE = 'SINGLE'
    PACK = 'PACK'
    COMBO = 'COMBO'

class MeasureType(Enum):
    WEIGHT = 'WEIGHT'
    LENGTH = 'LENGTH'
    VOLUME = 'VOLUME'
    NUMBER = 'NUMBER'

class ContactType(Enum):
    WEBSITE = 'WEBSITE'
    EMAIL = 'EMAIL'
    MOBILE = 'MOBILE'
    FAX = 'FAX'
    FACEBOOK = 'FACEBOOK'
    INSTAGRAM = 'INSTAGRAM'
    WHATSAPP = 'WHATSAPP'
    YOUTUBE = 'YOUTUBE'
    BLOG = 'BLOG'

class WeekDay(Enum):
    MONDAY = 'MONDAY'
    TUESDAY = 'TUESDAY'
    WEDNESDAY = 'WEDNESDAY'
    THURSDAY = 'THURSDAY'
    FRIDAY = 'FRIDAY'
    SATURDAY = 'SATURDAY'
    SUNDAY = 'SUNDAY'
    EVERYDAY = 'EVERYDAY'

class Status(Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    SUSPENDED = 'SUSPENDED'
    DELETED = 'DELETED'
    CLOSED = 'CLOSED'
    EXPIRED = 'EXPIRED'
    USED = 'USED'

# class KeyStatus(Enum):
#
#     ACTIVE = 'ACTIVE'
#     EXPIRED = 'EXPIRED'
#     USED = 'USED'
#     CANCELLED = 'CANCELLED'
#     DELETED = 'DELETED'


# class ProductStatus(Enum):
#     ACTIVE = 'ACTIVE'
#     DISBALED = 'DISABLED'
#     DELETED = 'DELETED'

class PlanTransactionType(Enum):
    CREATED = 'CREATED'
    RENEWAL = 'RENEWAL'
    BLOCK = 'BLOCK'
    EXPIRED = 'EXPIRED'

class ProductPackQuality(Enum):

    NEW = 'NEW'
    REFURBISHED = 'REFURBISHED'
    USED = 'USED'
    DAMAGE = 'DAMAGE'
    EXPIRED = 'EXPIRED'
    INCOMPLETE = 'INCOMPLETE BOX'

class Priority(Enum):

    EXCELLENT = 'EXCELLENT'
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'

class Maturity(Enum):

    UNMATURED = 'UNMATURED'
    MATURED = 'MATURED'
    CITIZEN ='CITIZEN'

class Direction(Enum):

    SINGLE = 'SINGLE'
    BOTH = 'BOTH'

class FileType(Enum):
    VIDEO = 'VIDEO'
    AUDIO ='AUDIO'
    IMAGE = 'IMAGE'

class ValueType(Enum):
    FREE = 'FREE'
    PAID ='PAID'

class ProductLevel(Enum):
    DEPARTMENT = 'DEPARTMENT'
    CATEGORY = 'CATEGORY'
    PRODUCT_TEMPLATE = 'PRODUCT_TEMPLATE'
    PRODUCT_MASTER = 'PRODUCT_MASTER'
    PRODUCT = 'PRODUCT'

class ShippingChargeBy(Enum):
    PRICE = 'PRICE'
    WEIGHT = 'WEIGHT'
    DISTANCE = 'DISTANCE'

class DeliveryType(Enum):
    NORMAL = 'NORMAL'
    FAST = 'FAST'
    TAKE_AWAY = 'TAKE_AWAY'

class VolumeOfferType(Enum):
    PRICE = 'PRICE'
    WEIGHT = 'WEIGHT'

class UserType(Enum):
    ADMIN = 'ADMIN'
    STORE = 'STORE'
    DELIVERY = 'DELIVERY'
    CUSTOMER = 'CUSTOMER'
    SPONSOR = 'SPONSOR'
    EXECUTIVE = 'EXECUTIVE'
    DEVELOPER = 'DEVELOPER'

class DeviceType(Enum):
    IPHONE = 'IPHONE'
    ANDROID = 'ANDROID'
    WINDOWS = 'WINDOWS'
    WEBSITE = 'WEBSITE'

class BannerType(Enum):
    SLIDING = 'SLIDING'
    STILL = 'STILL'
    SQUARE_CARD = 'SQUARE_CARD'
    VOLUME = 'VOLUME'

class StockType(Enum):
    INITIAL = 'INITIAL'
    NEW = 'NEW'
    RETURN = 'RETURN'
    OLD = 'OLD'

class BuildAction(Enum):
    DO_NOTHING = 'DO_NOTHING'
    UPDATE = 'UPDATE'
    MANDATORY_UPDATE = 'MANDATORY_UPDATE'


class OfferType(Enum):
    VOLUME = 'VOLUME'
    PRODUCT = 'PRODUCT'
    COLLECTION = 'COLLECTION'
    COUPON = 'COUPON'
    CAMPAIGN = 'CAMPAIGN'
    CAMPAIGN_COUPON = 'CAMPAIGN_COUPON'
    CUSTOMER_LEVEL = 'CUSTOMER_LEVEL'
    ADMIN = 'ADMIN'

class OfferBy(Enum):
    PERCENTAGE = 'PERCENTAGE'
    FIXED_PRICE = 'FIXED_PRICE'
    BY_PRICE = 'BY_PRICE'

class OrderStatus(Enum):
    PENDING = "PENDING"
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    PACKING = "PACKING"
    PACKED = "PACKED"
    ASSIGNED = "ASSIGNED"
    SHIPPING = "SHIPPING"
    RESCHEDULED = 'RESCHEDULED'
    UNABLE_TO_PROCESS = 'UNABLE_TO_PROCESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

class OrderType(Enum):
    NORMAL = 'NORMAL'
    ASSISTANT = 'ASSISTANT'

class HelpReasonType(Enum):
    CANCEL = 'CANCEL'
    ORDER_NOT_RECEIVED = 'ORDER_NOT_RECEIVED'
    RESCHEDULE = 'RESCHEDULE'
    NEW_PAYMENT = 'NEW_PAYMENT'
    ITEMS_MISSING = 'ITEMS_MISSING'
    QUANTITY_NOT_ADEQUATE = 'QUANTITY_NOT_ADEQUATE'
    DIFFERENT_ITEMS = 'DIFFERENT_ITEMS'
    BAD_QUALITY = 'BAD_QUALITY'
    UPDATE_ORDER = 'UPDATE_ORDER'
    PAYMENT_RELATED = 'PAYMENT_RELATED'
    COUPON_RELATED = 'COUPON_RELATED'
    UPDATE_MESSAGE = 'UPDATE_MESSAGE'
    CHAT = 'CHAT'
    OTHER = 'OTHER'


class OrderItemChange(Enum):
    ADDED = "ADDED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"

class UserPolicy(Enum):
    DELIVERY = "DELIVERY"

class AnalyticsActions(Enum):
    VIEW = "VIEW"
    ADD_TO_CART = "ADD_TO_CART"
    BUY = "BUY"
    SEARCH = "SEARCH"
    CRASH = "CRASH"
    PAGE_VISIT = "PAGE_VISIT"

class CouponStatus(Enum):
    GENERATED = "GENERATED"
    VIEW = "VIEW"
    REDEEMED = "REDEEMED"
    EXPIRED = 'EXPIRED'
    GIFT = "GIFT"
    DELETED = 'DELETED'

class FileUploadStatus(Enum):
    PENDING = 'PENDING'
    PROCESSED = 'PROCESSED'
    FAILED = 'FAILED'

class DeliveryStatus(Enum):
    CREATED = 'CREATED'
    ON_THE_WAY = 'ON_THE_WAY'
    RESCHEDULED = 'RESCHEDULED'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'
    ASSIGN_CANCEL = 'ASSIGN_CANCEL'

class OrderHelpAction(Enum):
    CANCEL = 'CANCEL'
    RESCHEDULE = 'RESCHEDULE'
    PAYMENT_ISSUE = 'PAYMENT_ISSUE'
    OUT_OF_DELIVERY = 'OUT_OF_DELIVERY'
    SHORT_IN_ITEM = 'SHORT_IN_ITEM'
    OTHER = 'OTHER'

class ProductAccessQueryType(Enum):
    TODAY = "TODAY"
    PICKED = "PICKED"
    DEPARTMENT = "DEPARTMENT"
    CATEGORY = "CATEGORY"
    SEARCH = "SEARCH"
    FILTER = "FILTER"
    COLLECTION = "COLLECTION"
    BRAND = "BRAND"

class FilterViewType(Enum):
    RANGE = "RANGE"
    RADIO = "RADIO"

class ViewType(Enum):
    FOOD = "FOOD"
    GROCERY = "GROCERY"
    ELECTRONICS = "ELECTRONICS"
    FASHION = "FASHION"


def get_status_integer(status):
    status_array = [type.value for type in Status]
    arr = []
    if isinstance(status, list):
        for a in status:
            arr.append(status_array.index(a))
        return arr
    return status_array.index(status)







