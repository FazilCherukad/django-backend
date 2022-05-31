class FilterPojo:

    def __init__(self, **kwargs):
        self._categories = kwargs.get("categories") or None
        self._departments = kwargs.get("departments") or None
        self._brands = kwargs.get("brands") or None
        self._stores = kwargs.get("stores") or None
        self._ids = kwargs.get("ids") or None
        self._search = kwargs.get("search") or None
        self._offset = kwargs.get("offset") or None
        self._limit = kwargs.get("limit") or None
        self._sort = kwargs.get("sort") or None
        self._status = kwargs.get("status") or ['ACTIVE']
        self._price = kwargs.get("price") or None
        self._stock = kwargs.get("stock") or None
        self._offer = kwargs.get("offer") or None
        self._type = kwargs.get("type") or 'active_records'
        self.group = kwargs.get("group") or 'enabled'

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, value):
        self._categories = value

    @property
    def departments(self):
        return self._departments

    @departments.setter
    def departments(self, value):
        self._departments = value

    @property
    def brands(self):
        return self._brands

    @brands.setter
    def brands(self, value):
        self._brands = value

    @property
    def stores(self):
        return self._stores

    @stores.setter
    def stores(self, value):
        self._stores = value

    @property
    def ids(self):
        return self._ids

    @ids.setter
    def ids(self, value):
        self._ids = value

    @property
    def search(self):
        return self._search

    @search.setter
    def search(self, value):
        self._search = value

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value

    @property
    def limit(self):
        return self._limit

    @limit.setter
    def limit(self, value):
        self._limit = value

    @property
    def sort(self):
        return self._sort

    @sort.setter
    def sort(self, value):
        self._sort = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def offer(self):
        return self._offer

    @offer.setter
    def offer(self, value):
        self._offer = value

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, value):
        self._stock = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = value

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

class StoreProductPojo:

    def __init__(self, sort, filter, search):
        self.sort = sort
        self.filter = filter
        self.search = search

    @property
    def sort(self):
        return self.sort

    @sort.setter
    def sort(self, value):
        self.sort = value

    @property
    def filter(self):
        return self.filter

    @filter.setter
    def filter(self, value):
        self.filter = value

    @property
    def search(self):
        return self.search

    @search.setter
    def search(self, value):
        self.search = value