from django.contrib import admin

from .models import *  # noqa: F401, F403


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    pass


@admin.register(TenantCropLOVSelection)
class TenantCropLOVSelectionAdmin(admin.ModelAdmin):
    list_display = ["lov_value", "lov_tenant"]


@admin.register(TenantCropLOVValue)
class TenantCropLOVValueAdmin(admin.ModelAdmin):
    pass


@admin.register(UserCrop)
class UserCropAdmin(admin.ModelAdmin):
    pass
