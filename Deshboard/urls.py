from django.urls import path
from .views import *
from .monthly_summary_view import MonthlySummaryAPIView
from .accounting_export_view import AccountingExportAPIView, AccountingJournalListView

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
    
    
    # invoices short list URLs
    path("invoices/short-list/", InvoiceShortListView.as_view(), name="short-invoice-list"),
    path("invoices/details/<int:pk>/", InvoiceDetailsSerializers.as_view(), name="short-invoice-detail"),

    # dashboard overview
    path("dashboard/overview/", DashboardOverviewView.as_view(), name="dashboard-overview"),

    # monthly summary
    path("monthly-summary/", MonthlySummaryAPIView.as_view(), name="monthly-summary"),

    # bank / payment operations
    path("payments/modes/", BankOperationModeView.as_view(), name="bank-operation-modes"),
    path("payments/", BankOperationListCreateView.as_view(), name="bank-operation-list-create"),
    path("payments/<int:pk>/", BankOperationDetailView.as_view(), name="bank-operation-detail"),
    path("payments/summary/", BankOperationSummaryView.as_view(), name="bank-operation-summary"),
    
    # accounting export endpoints (Pro Plan only)
    path("accounting/export/", AccountingExportAPIView.as_view(), name="accounting-export"),
    path("accounting/journal/", AccountingJournalListView.as_view(), name="accounting-journal-list"),
    
  
]