from django.contrib import admin
from .models import Client, Supplier
# Register your models here.
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "client_type", "email", "phone", "city", "country", "created_at")
    list_filter = ("client_type", "city", "country")
    search_fields = ("email", "phone", "billing_address")
    
    
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "client_type", "email", "phone", "city", "country", "created_at")
    list_filter = ("client_type", "city", "country")
    search_fields = ("email", "phone", "billing_address")