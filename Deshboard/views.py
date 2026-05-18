from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from Authentication import models
from utils.paginations import CustomPagination
from utils.api_response import APIResponse
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q, Max
from decimal import Decimal
from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce, TruncMonth
from django.utils import timezone
from dateutil.relativedelta import relativedelta

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
    InvoiceShortListSerializer,
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
        
        
class InvoiceShortListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.filter(company=request.user).order_by("-id")
        # Ensure computed totals reflect current line values (do not persist)
        for inv in invoices:
            try:
                inv.compute_totals()
            except Exception:
                pass
        serializer = InvoiceShortListSerializer(invoices, many=True)
        return APIResponse.success(
            message="Invoice list retrieved successfully.",
            data=serializer.data
        )
        
        
        
class InvoiceDetailsSerializers(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            invoice = Invoice.objects.get(pk=pk, company=request.user)
        except Invoice.DoesNotExist:
            return APIResponse.error(message="Invoice not found.", status=404)
        # Ensure totals reflect current line values (do not persist)
        try:
            invoice.compute_totals()
        except Exception:
            pass

        serializer = InvoiceListSerializer(invoice, context={"request": request})
        return APIResponse.success(message="Invoice details retrieved successfully.", data=serializer.data)
    
    def patch(self, request, pk):
        try:
            invoice = Invoice.objects.get(pk=pk, company=request.user)
        except Invoice.DoesNotExist:
            return APIResponse.error(message="Invoice not found.", status=404)

        if invoice.is_frozen:
            return APIResponse.error(message="This invoice is locked.", status=status.HTTP_403_FORBIDDEN)
        data = request.data or {}

        # If client sent `lines`, treat them as adjustment amounts (do NOT overwrite original invoice prices)
        if isinstance(data, dict) and data.get("lines"):
            lines = data.get("lines") or []
            adjustment_total = Decimal("0")
            try:
                for l in lines:
                    qty = Decimal(str(l.get("quantity", 0)))
                    unit = Decimal(str(l.get("unit_price_ht", 0)))
                    line_ht = qty * unit
                    if invoice.apply_tva:
                        tva_rate = Decimal(str(l.get("tva_rate", 0)))
                        line_tva = line_ht * (tva_rate / Decimal("100"))
                    else:
                        line_tva = Decimal("0")
                    line_total = line_ht + line_tva
                    adjustment_total += line_total
            except Exception as e:
                return APIResponse.error(message="Invalid line values.", errors={"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            # previous remaining balance
            prev_remaining = invoice.total_ttc - invoice.amount_paid
            new_remaining = prev_remaining - adjustment_total

            # Update amount_paid so remaining decreases by adjustment_total
            invoice.amount_paid = invoice.amount_paid + adjustment_total
            invoice.save(update_fields=["amount_paid"])

            out = InvoiceListSerializer(invoice, context={"request": request})
            return APIResponse.success(message="Invoice adjusted and remaining balance updated.", data={
                "invoice": out.data,
                "adjustment_total": float(adjustment_total),
                "previous_remaining": float(prev_remaining),
                "new_remaining": float(new_remaining),
            })

        # Fallback: reuse existing create/update serializer logic to validate and persist full invoice updates
        serializer = InvoiceCreateSerializer(
            invoice, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            invoice = serializer.save()
            # Ensure totals are up-to-date (serializer.save already computes totals)
            try:
                invoice.compute_totals()
                invoice.save(update_fields=["total_ht", "total_tva", "total_ttc"])
            except Exception:
                pass

            out = InvoiceListSerializer(invoice, context={"request": request})
            return APIResponse.success(message="Invoice updated and recalculated.", data=out.data)

        return APIResponse.error(message="Invalid data.", errors=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def _to_float(self, value):
        if value is None:
            return 0.0
        return float(value)

    def _sum_value(self, qs, field_name):
        return qs.aggregate(total=Coalesce(Sum(field_name), Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))))["total"]

    def _remaining_expr(self):
        return ExpressionWrapper(
            F("total_ttc") - F("amount_paid"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

    def _card_trend(self, current_value, previous_value):
        current = Decimal(str(current_value or 0))
        previous = Decimal(str(previous_value or 0))
        if previous == 0:
            if current == 0:
                return 0.0
            return 100.0
        return float(((current - previous) / previous) * Decimal("100"))

    def _effective_due_date(self, invoice):
        """Use explicit due_date if present; otherwise derive it from payment_conditions."""
        if invoice.due_date:
            return invoice.due_date

        payment_days = {
            "immediate": 0,
            "15_jours": 15,
            "30_jours": 30,
            "45_jours": 45,
            "60_jours": 60,
        }
        days = payment_days.get(invoice.payment_conditions)
        if days is None:
            return invoice.invoice_date

        return invoice.invoice_date + timezone.timedelta(days=days)

    def get(self, request):
        company = request.user
        today = timezone.localdate()

        month_start = today.replace(day=1)
        prev_month_end = month_start - timezone.timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        base_qs = Invoice.objects.filter(company=company)
        sales_qs = base_qs.filter(invoice_type="vente", invoice_subtype="facture")
        purchase_qs = base_qs.filter(invoice_type="achat", invoice_subtype="facture")

        # Financial cards
        current_revenue = self._sum_value(
            sales_qs.filter(invoice_date__gte=month_start, invoice_date__lte=today),
            "amount_paid",
        )
        prev_revenue = self._sum_value(
            sales_qs.filter(invoice_date__gte=prev_month_start, invoice_date__lte=prev_month_end),
            "amount_paid",
        )

        current_receivables = self._sum_value(
            sales_qs.annotate(remaining=self._remaining_expr()).filter(remaining__gt=0),
            "remaining",
        )
        prev_receivables = self._sum_value(
            sales_qs.filter(invoice_date__gte=prev_month_start, invoice_date__lte=prev_month_end)
            .annotate(remaining=self._remaining_expr())
            .filter(remaining__gt=0),
            "remaining",
        )

        current_debts = self._sum_value(
            purchase_qs.annotate(remaining=self._remaining_expr()).filter(remaining__gt=0),
            "remaining",
        )
        prev_debts = self._sum_value(
            purchase_qs.filter(invoice_date__gte=prev_month_start, invoice_date__lte=prev_month_end)
            .annotate(remaining=self._remaining_expr())
            .filter(remaining__gt=0),
            "remaining",
        )

        # Revenue / expense trend (last 7 months)
        chart_start = month_start - relativedelta(months=6)
        monthly_sales = (
            sales_qs.filter(invoice_date__gte=chart_start)
            .annotate(month=TruncMonth("invoice_date"))
            .values("month")
            .annotate(total=Coalesce(Sum("total_ttc"), Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))))
            .order_by("month")
        )
        monthly_expenses = (
            purchase_qs.filter(invoice_date__gte=chart_start)
            .annotate(month=TruncMonth("invoice_date"))
            .values("month")
            .annotate(total=Coalesce(Sum("total_ttc"), Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))))
            .order_by("month")
        )

        # TruncMonth on a DateField can return either date or datetime depending on backend.
        # Normalize both safely into a date key.
        sales_map = {
            (item["month"].date() if hasattr(item["month"], "date") else item["month"]): item["total"]
            for item in monthly_sales
            if item.get("month")
        }
        expense_map = {
            (item["month"].date() if hasattr(item["month"], "date") else item["month"]): item["total"]
            for item in monthly_expenses
            if item.get("month")
        }

        chart_points = []
        for idx in range(7):
            d = (chart_start + relativedelta(months=idx))
            key = d
            rev = sales_map.get(key, Decimal("0"))
            exp = expense_map.get(key, Decimal("0"))
            chart_points.append(
                {
                    "month": d.strftime("%b"),
                    "revenue": self._to_float(rev),
                    "expenses": self._to_float(exp),
                }
            )

        # Top clients by billed sales amount
        top_clients_qs = (
            sales_qs.filter(client__isnull=False)
            .values("client_id", "client__first_name", "client__last_name", "client__company_name", "client__email")
            .annotate(total=Coalesce(Sum("total_ttc"), Value(Decimal("0"), output_field=DecimalField(max_digits=14, decimal_places=2))))
            .order_by("-total")[:6]
        )
        top_clients = []
        for row in top_clients_qs:
            name = " ".join(
                [v for v in [row.get("client__first_name"), row.get("client__last_name")] if v]
            ).strip() or row.get("client__company_name") or "N/A"
            top_clients.append(
                {
                    "client_id": row.get("client_id"),
                    "name": name,
                    "email": row.get("client__email") or "",
                    "amount": self._to_float(row.get("total")),
                }
            )

        # Reminders = overdue invoices that still have pending balance.
        overdue_invoices = base_qs.select_related("client", "supplier").order_by("due_date", "-id")
        reminders = []
        for inv in overdue_invoices:
            effective_due_date = self._effective_due_date(inv)
            if not effective_due_date or effective_due_date > today:
                continue

            remaining_balance = Decimal(str(inv.total_ttc)) - Decimal(str(inv.amount_paid))
            if remaining_balance <= 0:
                continue

            days_late = (today - effective_due_date).days
            reminders.append(
                {
                    "invoice_id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "status": inv.status,
                    "due_date": effective_due_date,
                    "days_overdue": days_late,
                    "remaining_balance": self._to_float(remaining_balance),
                    "payment_status": "pending",
                }
            )
            if len(reminders) >= 5:
                break

        # Recent invoices table
        recent_qs = base_qs.order_by("-invoice_date", "-id")[:6]
        recent_invoices = []
        for inv in recent_qs:
            remaining = inv.total_ttc - inv.amount_paid
            effective_due_date = self._effective_due_date(inv)
            payment_status = "paid" if remaining <= 0 else ("overdue" if effective_due_date and effective_due_date < today else "pending")
            recent_invoices.append(
                {
                    "id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "date": inv.invoice_date,
                    "due_date": effective_due_date,
                    "amount": self._to_float(inv.total_ttc),
                    "invoice_type": inv.invoice_type,
                    "status": inv.status,
                    "payment_status": payment_status,
                    "remaining_balance": self._to_float(remaining),
                }
            )

        total_sales = self._sum_value(sales_qs, "total_ttc")
        total_expenses = self._sum_value(purchase_qs, "total_ttc")
        net_result = total_sales - total_expenses

        payload = {
            "financial_overview": {
                "revenue": {
                    "value": self._to_float(current_revenue),
                    "change_percent": self._card_trend(current_revenue, prev_revenue),
                },
                "unpaid_receivables": {
                    "value": self._to_float(current_receivables),
                    "change_percent": self._card_trend(current_receivables, prev_receivables),
                },
                "total_debts": {
                    "value": self._to_float(current_debts),
                    "change_percent": self._card_trend(current_debts, prev_debts),
                },
            },
            "top_clients": top_clients,
            "revenue_chart": {
                "points": chart_points,
                "summary": {
                    "total_revenue": self._to_float(total_sales),
                    "total_expenses": self._to_float(total_expenses),
                    "net_result": self._to_float(net_result),
                },
            },
            "reminders": reminders,
            "recent_invoices": recent_invoices,
            "counts": {
                "total_invoices": base_qs.count(),
                "overdue_invoices": len(reminders),
                # Count invoices by type so clients + suppliers remains aligned with invoice totals
                "clients": base_qs.filter(invoice_type="vente").count(),
                "suppliers": base_qs.filter(invoice_type="achat").count(),
            },
        }

        return APIResponse.success(message="Dashboard overview retrieved successfully.", data=payload)
    
    
    
