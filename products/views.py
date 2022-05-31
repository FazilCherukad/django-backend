from django.shortcuts import render

# Create your views here.

# from .models import Product

def homeview(request, *args, **kwargs):

    # obj = Product.objects.get(id=1)
    #
    # context = {
    #     'title' : obj.title
    # }

    return render(request,'products/detail.html',{})
