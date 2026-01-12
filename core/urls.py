"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from dashboard.views import home , fabric , sample, oih, prod
urlpatterns = [
    path("admin/", admin.site.urls),
    path("dispatch/", home, name="dispatch"), 
    path("fabric/", fabric, name="fabric"),
    path("sample/", sample, name="sample") ,  
    path("oih/", oih, name="oih"), 
    path("warp/", prod, name="warp") , 
    path("", home, name="home"),               
]

