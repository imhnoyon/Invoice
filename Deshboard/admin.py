from django.contrib import admin
from .models import Client, Invoice, Supplier
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
    
    
    
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "client", "invoice_number", "accounting_number", "invoice_type", "invoice_subtype", "invoice_date", "created_at")
    list_filter = ("invoice_date", )
    search_fields = ("company__username", "client__email")