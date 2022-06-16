from xml.dom.minidom import Document
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("shop_app.urls")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# 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

# git remote set-url origin https://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@github.com/MarkPage2k1/Shop_Online

