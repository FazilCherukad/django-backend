"""odruz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings

from products.views import homeview
from refs.views import image_view
from core.utils.utils import CustomGraphQlView

from graphql.backend import GraphQLCoreBackend

class GraphQLCustomCoreBackend(GraphQLCoreBackend):
    def __init__(self, executor=None):
        # type: (Optional[Any]) -> None
        super().__init__(executor)
        self.execute_params['allow_subscriptions'] = True

urlpatterns = [
    path('detail/', homeview),
    # path('admin/', admin.site.urls),
    path('test',image_view),
    url(r'^graphql', CustomGraphQlView.as_view(graphiql=True, backend=GraphQLCustomCoreBackend())),
    # url('',
    #          (r'^media/(?P<path>.*)$', 'django.views.static.serve',
    #           {'document_root': 'brand-images'}),
    #          )
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENABLE_SILK:
    urlpatterns += [
        url(r'^silk/', include('silk.urls', namespace='silk'))]

# urlpatterns += patterns('django.views.static',(r'^media/(?P<path>.*)','serve',{'document_root':settings.MEDIA_ROOT}), )
