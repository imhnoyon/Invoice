from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from Authentication import models
from utils.paginations import CustomPagination
from utils.api_response import APIResponse
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Max

from .models import Client, Invoice, Supplier
from .serializers import (
   IndependentClientSerializer,
    CompanyClientSerializer,
    ClientSerializer,
    IndividualSupplierSerializer,
    CompanySupplierSerializer,
    SupplierSerializer,
    InvoiceCreateSerializer,
    InvoiceListSerializer,
)

CLIENT_SERIALIZER_MAP = {
    "Indépendant": IndependentClientSerializer,
    "Société": CompanyClientSerializer,
}

VALUE_ALIASES = {
    "client_type": {
        "independent": "Indépendant",
        "company": "Société",
    },
    "client_category": {
        "eu_client": "Client dans l'UE (hors France)",
        "non_eu_client": "Client hors UE",
        "france_client": "Client en France",
    },
    "city": {
        "paris": "Paris",
        "lyon": "Lyon",
        "marseille": "Marseille",
        "bordeaux": "Bordeaux",
        "toulouse": "Toulouse",
    },
    "country": {
        "france": "France",
        "belgium": "Belgique",
        "switzerland": "Suisse",
        "luxembourg": "Luxembourg",
    },
}


def normalize_choice_values(data):
    """Accept both key-style values and French labels for choice-like fields."""
    normalized = data.copy()
    for field, aliases in VALUE_ALIASES.items():
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = aliases.get(value.strip().lower(), value)
    return normalized


class ClientCreateView(APIView):
    """
    POST /clients/
    Body must include client_type = "Indépendant" | "Société"
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = normalize_choice_values(request.data)
        client_type = payload.get("client_type")

        SerializerClass = CLIENT_SERIALIZER_MAP.get(client_type)
        if not SerializerClass:
            return APIResponse.error(
                {"client_type": "Invalid value. Choose 'Indépendant' or 'Société'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SerializerClass(data=payload)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return APIResponse.success(message="Client created.", data=serializer.data, status_code=status.HTTP_201_CREATED)

        return APIResponse.error(message="Validation error.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class ClientListView(APIView):
    """GET /clients/ — list all clients belonging to the authenticated user."""
    permission_classes = [IsAuthenticated]
    paginatation_class = CustomPagination

    def get(self, request):
        paginator = self.paginatation_class()
        clients = Client.objects.filter(user=request.user).order_by("-created_at")
        page = paginator.paginate_queryset(clients, request)
        serializer = ClientSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ClientDetailView(APIView):
    """GET / PATCH / DELETE /clients/<pk>/"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Client.objects.get(pk=pk, user=user)
        except Client.DoesNotExist:
            return None

    def get(self, request, pk):
        client = self.get_object(pk, request.user)
        if not client:
            return APIResponse.error({"detail": "Client not found."}, status_code=status.HTTP_404_NOT_FOUND)
        return APIResponse.success(message="Client retrieved.", data=ClientSerializer(client).data)

    def patch(self, request, pk):
        client = self.get_object(pk, request.user)
        if not client:
            return APIResponse.error({"detail": "Client not found."}, status_code=status.HTTP_404_NOT_FOUND)

        payload = normalize_choice_values(request.data)

        # Route to the right serializer based on stored client_type
        SerializerClass = CLIENT_SERIALIZER_MAP.get(client.client_type, ClientSerializer)
        serializer = SerializerClass(client, data=payload, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(message="Client updated.", data=serializer.data)
        return APIResponse.error(message="Validation error.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        client = self.get_object(pk, request.user)
        if not client:
            return APIResponse.error({"detail": "Client not found."}, status_code=status.HTTP_404_NOT_FOUND)
        client.delete()
        return APIResponse.success(message="Client deleted.", data=None, status_code=status.HTTP_204_NO_CONTENT)


    
    
# The Supplier views would be implemented similarly, with appropriate adjustments for the Supplier model and serializers.


SUPPLIER_SERIALIZER_MAP = {
    "Indépendant": IndividualSupplierSerializer,
    "Société": CompanySupplierSerializer,
}


class SupplierCreateView(APIView):
    """
    POST /suppliers/
    Body must include client_type = "Indépendant" | "Société"
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = normalize_choice_values(request.data)
        client_type = payload.get("client_type")

        SerializerClass = SUPPLIER_SERIALIZER_MAP.get(client_type)
        if not SerializerClass:
            return APIResponse.error(
                {"client_type": "Invalid value. Choose 'Indépendant' or 'Société'."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SerializerClass(data=payload)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return APIResponse.success(message="Supplier created.", data=serializer.data, status_code=status.HTTP_201_CREATED)

        return APIResponse.error(message="Validation error.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)


class SupplierListView(APIView):
    """GET /suppliers/ — list all suppliers belonging to the authenticated user."""
    permission_classes = [IsAuthenticated]
    paginatation_class = CustomPagination

    def get(self, request):
        paginator = self.paginatation_class()
        suppliers = Supplier.objects.filter(user=request.user).order_by("-created_at")
        page = paginator.paginate_queryset(suppliers, request)
        serializer = SupplierSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    
class SupplierDetailView(APIView):
    """GET / PATCH / DELETE /suppliers/<pk>/"""
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Supplier.objects.get(pk=pk, user=user)
        except Supplier.DoesNotExist:
            return None

    def get(self, request, pk):
        supplier = self.get_object(pk, request.user)
        if not supplier:
            return APIResponse.error({"detail": "Supplier not found."}, status_code=status.HTTP_404_NOT_FOUND)
        return APIResponse.success(message="Details retrieved", data=SupplierSerializer(supplier).data)

    def patch(self, request, pk):
        supplier = self.get_object(pk, request.user)
        if not supplier:
            return APIResponse.error({"detail": "Supplier not found."}, status_code=status.HTTP_404_NOT_FOUND)

        payload = normalize_choice_values(request.data)

        # Route to the right serializer based on stored client_type
        SerializerClass = SUPPLIER_SERIALIZER_MAP.get(supplier.client_type, SupplierSerializer)
        serializer = SerializerClass(supplier, data=payload, partial=True)
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(message="Supplier updated.", data=serializer.data)
        return APIResponse.error(message="Validation error.", data=serializer.errors, status_code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        supplier = self.get_object(pk, request.user)
        if not supplier:
            return APIResponse.error({"detail": "Supplier not found."}, status_code=status.HTTP_404_NOT_FOUND)
        supplier.delete()
        return APIResponse.success(message="Supplier deleted.", data=None, status_code=status.HTTP_204_NO_CONTENT)
    
    
    
    
# The Invoice views would be implemented similarly, with appropriate adjustments for the Invoice model and serializers.

# views.py



class InvoiceListCreateView(APIView):
    """
    GET  /invoices/   → list (filter by tab/search)
    POST /invoices/   → create new invoice
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_company(self, request):
        try:
            return request.user
        except Exception:
            return None

    # ── LIST ────────────────────────────────────────────────
    def get(self, request):
        company = self.get_company(request)
        if not company:
            return Response(
                {"detail": "Please configure your company first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Invoice.objects.filter(company=company).order_by("-invoice_date", "-accounting_number")

        # Tab filter: ?tab=ventes | achats | avoirs
        tab = request.query_params.get("tab")
        if tab == "ventes":
            qs = qs.filter(invoice_type="vente", invoice_subtype="facture")
        elif tab == "achats":
            qs = qs.filter(invoice_type="achat", invoice_subtype="facture")
        elif tab == "avoirs":
            qs = qs.filter(invoice_subtype="avoir")

        # Search: ?search=INV001 বা client name
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) |
                Q(client__first_name__icontains=search) |
                Q(client__last_name__icontains=search) |
                Q(client__company_name__icontains=search) |
                Q(supplier__first_name__icontains=search) |
                Q(supplier__last_name__icontains=search) |
                Q(supplier__company_name__icontains=search) |
                Q(supplier__email__icontains=search)
            )

        # Status filter: ?status=brouillon
        inv_status = request.query_params.get("status")
        if inv_status:
            qs = qs.filter(status=inv_status)

        serializer = InvoiceListSerializer(qs, many=True)
        return APIResponse.success(message="Invoices retrieved.", data={
            "count":   qs.count(),
            "results": serializer.data,
        })

    # ── CREATE ──────────────────────────────────────────────
    def post(self, request):
        company = self.get_company(request)
        if not company:
            return Response(
                {"detail": "Please configure your company first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InvoiceCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            invoice = serializer.save(company=company)
            return APIResponse.success(message="Invoice created.", data=InvoiceCreateSerializer(invoice, context={"request": request}).data)
        return APIResponse.error(message="Invalid data.", errors=serializer.errors)

class InvoiceDetailView(APIView):
    """
    GET    /invoices/<pk>/   → retrieve
    PATCH  /invoices/<pk>/   → update (frozen হলে না)
    DELETE /invoices/<pk>/   → delete + renumber
    """
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_invoice(self, pk, request):
        try:
            return Invoice.objects.get(pk=pk, company=request.user)
        except Invoice.DoesNotExist:
            return None

    def get(self, request, pk):
        invoice = self.get_invoice(pk, request)
        if not invoice:
            return APIResponse.error(message="Invoice not found.", status=404)
        return APIResponse.success(message="Invoice retrieved.", data=InvoiceCreateSerializer(invoice, context={"request": request}).data)

    def patch(self, request, pk):
        invoice = self.get_invoice(pk, request)
        if not invoice:
            return APIResponse.error(message="Invoice not found.", status=404)
        if invoice.is_frozen:
            return APIResponse.error(message="This invoice is locked.", status=status.HTTP_403_FORBIDDEN)

        serializer = InvoiceCreateSerializer(
            invoice, data=request.data,
            partial=True,
            context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(message="Invoice updated.", data=serializer.data)
        return APIResponse.error(message="Invalid data.", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        invoice = self.get_invoice(pk, request)
        if not invoice:
            return APIResponse.error(message="Invoice not found.", status=404)
        if invoice.is_frozen:
            return APIResponse.error(message="A locked invoice cannot be deleted.", status=status.HTTP_403_FORBIDDEN)

        company        = invoice.company
        deleted_number = invoice.accounting_number
        invoice.delete()

        # ✅ Accounting number reassign (gap পূরণ করো)
        Invoice.objects.filter(
            company=company,
            accounting_number__gt=deleted_number,
            is_frozen=False
        ).order_by("accounting_number").update(
            accounting_number=models.F("accounting_number") - 1
        )

        return APIResponse.success(message="Invoice deleted.", status=status.HTTP_204_NO_CONTENT)


class InvoiceTVAToggleView(APIView):
    """
    PATCH /invoices/<pk>/toggle-tva/
    body: { "apply_tva": true | false }

    Toggle করলে সব lines recalculate হবে।
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            invoice = Invoice.objects.get(pk=pk, company=request.user)
        except Invoice.DoesNotExist:
            return APIResponse.error(message="Invoice not found.", status=404)

        if invoice.is_frozen:
            return APIResponse.error(message="This invoice is locked.", status=status.HTTP_403_FORBIDDEN)

        apply_tva = request.data.get("apply_tva")
        if apply_tva is None:
            return APIResponse.error(message="The apply_tva field is required.", status=status.HTTP_400_BAD_REQUEST)
               

        invoice.apply_tva = apply_tva
        invoice.save(update_fields=["apply_tva"])

        # ✅ সব line recalculate
        for line in invoice.lines.all():
            if not apply_tva:
                line.tva_rate = 0
            line.save()

        # ✅ Invoice totals recompute
        invoice.compute_totals()
        invoice.save(update_fields=["total_ht", "total_tva", "total_ttc"])

        return Response({
            "apply_tva": invoice.apply_tva,
            "total_ht":  invoice.total_ht,
            "total_tva": invoice.total_tva,
            "total_ttc": invoice.total_ttc,
            "lines": [
                {
                    "id":        l.id,
                    "tva_rate":  l.tva_rate,
                    "total_ht":  l.total_ht,
                    "total_tva": l.total_tva,
                    "total_ttc": l.total_ttc,
                }
                for l in invoice.lines.all()
            ]
        })


class InvoiceConfirmView(APIView):
    """
    POST /invoices/<pk>/confirm/
    Brouillon → a_traiter (Confirmer et envoyer la facture)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            invoice = Invoice.objects.get(pk=pk, company=request.user)
        except Invoice.DoesNotExist:
            return APIResponse.error(message="Invoice not found.", status=404)

        if invoice.is_frozen:
            return APIResponse.error(message="Invoice is already locked.", status=status.HTTP_403_FORBIDDEN)

        if invoice.status != "brouillon":
            return APIResponse.error(message=f"Current status: {invoice.status}. Cannot confirm.", status=status.HTTP_400_BAD_REQUEST)

        # Required fields check
        errors = {}
        if not invoice.client and invoice.invoice_type == "vente":
            errors["client"] = "A client name is required."
        if not invoice.due_date:
            errors["due_date"] = "The due date is required."
        if not invoice.service_date:
            errors["service_date"] = "The service date is required."
        if not invoice.lines.exists():
            errors["lines"] = "At least one line item is required."

        if errors:
            return APIResponse.error(message=errors, status=status.HTTP_400_BAD_REQUEST)

        invoice.status = "a_traiter"
        invoice.save(update_fields=["status"])

        return APIResponse.success(message="Invoice confirmed and sent.", data={
            "detail":  "Invoice confirmed and sent.",
            "status":  invoice.status,
            "invoice": InvoiceCreateSerializer(invoice, context={"request": request}).data,
        })