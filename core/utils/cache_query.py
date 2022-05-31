from products.models import ProductMaster
from store_products.models import StoreProduct
from .memcached import client

TIMEOUT = 1800

def categories_cache(category):
    category_list_key = 'category_list_' + str(category.id)
    category_result = client.get(category_list_key)
    ids = [category.id]
    children = category.children.all().values_list('id', flat=True)
    for child in children:
        ids.append(child)
    if category_result is None:
        client.set(category_list_key, list(ids))
    return ids

def store_product_pack_cache(product, packs):
    product_result = client.get(product.code)
    if product_result:
        return product_result
    if packs:
        client.set(product.code, packs, 20)
    return None