"""testproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from .views import home_view, lov_crop_value_create_view, lov_tenant_crop_selection_view, lov_user_crop_selection_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home_view"),
    path("lov_crop_value_create_view/", lov_crop_value_create_view, name="lov_crop_value_create_view"),
    path("lov_tenant_crop_selection_view/", lov_tenant_crop_selection_view, name="lov_tenant_crop_selection_view"),
    path("lov_user_crop_selection_view/", lov_user_crop_selection_view, name="lov_user_crop_selection_view"),
]
