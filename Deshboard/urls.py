from django.urls import path
from .views import *

urlpatterns = [
    # Client URLs
    path("clients/", ClientListView.as_view(), name="client-list"),
    path("clients/add/", ClientCreateView.as_view(), name="client-create"),
    path("clients/<int:pk>/", ClientDetailView.as_view(), name="client-detail"),
    
    # Supplier URLs would be added similarly
    path("suppliers/", SupplierListView.as_view(), name="supplier-list"),
    path("suppliers/add/", SupplierCreateView.as_view(), name="supplier-create"),   
    path("suppliers/<int:pk>/", SupplierDetailView.as_view(), name="supplier-detail"),
    
    
    # Invoice URLs
    path("invoices/",                        InvoiceListCreateView.as_view(), name="invoice-list-create"),
    path("invoices/<int:pk>/",               InvoiceDetailView.as_view(),     name="invoice-detail"),
    path("invoices/<int:pk>/toggle-tva/",    InvoiceTVAToggleView.as_view(),  name="invoice-toggle-tva"),
    path("invoices/<int:pk>/confirm/",       InvoiceConfirmView.as_view(),    name="invoice-confirm"),
]