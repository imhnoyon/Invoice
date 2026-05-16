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
]