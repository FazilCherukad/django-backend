from django.contrib import admin

# Register your models here.
#
# from .models import Product
from .models import ProductTemplate
from .models import ProductMaster

# admin.site.register(Product)
admin.site.register(ProductTemplate)
admin.site.register(ProductMaster)