import graphene

from account.schema import UserAccountQuery, UserAccountMutations
from customer.schema import CustomerMutations, CustomerQuery
from refs.schema import QueryRef, MutationsRef
from uom.schema import UOMMutations, UOMQuery
from plans.schema import AuthenticationKeyMutations, AuthenticationKeyQuery
from products.schema import ProductQuery, ProductMutations
from store.schema import StoreQuery, StoreMutations
from store_products.schema import StoreProductMutations, StoreProductQuery
from store_shipping.schema import StoreShippingMutations, StoreShippingQuery
from offer.schema import StoreOfferMutations, StoreOfferQuery
from content.schema import ContentMutations, ContentQuery
from manufacture.schema import ManufactureMutations, ManufactureQuery
from order.schema import OrderMutations, OrderQuery
from help.schema import HelpMutations, HelpQuery
from analytics.schema import AnalyticsQuery, AnalyticsMutations
from store_content.schema import StoreContentMutations, StoreContentQuery
from delivery_boy.schema import DeliveryBoyMutations, DeliveryBoyQuery
from developer.schema import DeveloperQuery, DeveloperMutations


class Query(UserAccountQuery,
            ContentQuery,
            ManufactureQuery,
            CustomerQuery,
            QueryRef,
            UOMQuery,
            AuthenticationKeyQuery,
            StoreOfferQuery,
            ProductQuery,
            StoreQuery,
            StoreProductQuery,
            StoreShippingQuery,
            OrderQuery,
            HelpQuery,
            AnalyticsQuery,
            StoreContentQuery,
            DeliveryBoyQuery,
            DeveloperQuery,
            graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

class Mutations(UserAccountMutations,
                CustomerMutations,
                ManufactureMutations,
                MutationsRef,
                UOMMutations,
                ContentMutations,
                AuthenticationKeyMutations,
                StoreMutations,
                ProductMutations,
                StoreProductMutations,
                StoreShippingMutations,
                StoreOfferMutations,
                OrderMutations,
                HelpMutations,
                AnalyticsMutations,
                StoreContentMutations,
                DeliveryBoyMutations,
                DeveloperMutations,
                graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutations, subscription=Query)