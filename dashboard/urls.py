from django.urls import path
from .views import home

urlpatterns = [
    path("dispatch/", home, name="dispatch"),
]
