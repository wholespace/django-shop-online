from urllib.parse import urlparse
from django.urls import path
from .views import *

app_name = 'shop_app'
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", AboutView.as_view(), name="about"),
    path("contact-us/", ContactView.as_view(), name="contact"),
]
