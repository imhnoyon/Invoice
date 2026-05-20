from rest_framework import serializers
from .models import Client, Supplier, BankOperation, Invoice
from decimal import Decimal
from django.db import transaction
from django.utils import timezone


class IndependentClientSerializer(serializers.ModelSerializer):
    client_type = serializers.HiddenField(default="Indépendant")

    class Meta:
        model = Client
        fields = ["id", "client_type", "first_name", "last_name","email", "phone", "billing_address", "postal_code", "city", 
                  "country","client_category", "internal_notes","created_at", "updated_at",]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("first_name"):
            raise serializers.ValidationError({"first_name": "This field is required for an individual."})
        if not attrs.get("last_name"):
            raise serializers.ValidationError({"last_name": "This field is required for an individual."})
        return attrs


class CompanyClientSerializer(serializers.ModelSerializer):
    client_type = serializers.HiddenField(default="Société")

    class Meta:
        model = Client
        fields = ["id", "client_type","client_name", "company_name","email", "phone","billing_address", "postal_code", "city", "country",
            "siren_siret", "vat_number",
            "client_category", "internal_notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("company_name"):
            raise serializers.ValidationError({"company_name": "This field is required for a company."})
        if not attrs.get("siren_siret"):
            raise serializers.ValidationError({"siren_siret": "This field is required for a company."})
        return attrs


class ClientSerializer(serializers.ModelSerializer):
    """Read serializer — returns all fields for list/retrieve."""

    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at"]
        
        
        
        
        
# The Supplier serializers would be implemented similarly, with appropriate adjustments for the Supplier model and fields.

class IndividualSupplierSerializer(serializers.ModelSerializer):
    client_type = serializers.HiddenField(default="Indépendant")

    class Meta:
        model = Supplier
        fields = ["id", "client_type", "first_name", "last_name","email", "phone", "billing_address", "postal_code", "city", 
                  "country","client_category", "payment_method", "internal_notes","created_at", "updated_at",]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("first_name"):
            raise serializers.ValidationError({"first_name": "This field is required for an individual."})
        if not attrs.get("last_name"):
            raise serializers.ValidationError({"last_name": "This field is required for an individual."})
        return attrs
    
    
    
class CompanySupplierSerializer(serializers.ModelSerializer):
    client_type = serializers.HiddenField(default="Société")

    class Meta:
        model = Supplier
        fields = ["id", "client_type","client_name", "company_name","email", "phone","billing_address", "postal_code", "city", "country",
            "siren_siret", "vat_number",
            "client_category", "payment_method", "internal_notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("company_name"):
            raise serializers.ValidationError({"company_name": "This field is required for a company."})
        if not attrs.get("siren_siret"):
            raise serializers.ValidationError({"siren_siret": "This field is required for a company."})
        return attrs    
    
    
class SupplierSerializer(serializers.ModelSerializer):
    """Read serializer — returns all fields for list/retrieve."""

    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at"]
        
        
        
        
# Invoices serializers would be implemented similarly, with appropriate adjustments for the Invoice model and fields.
# serializers.py
from rest_framework import serializers
from .models import Invoice, InvoiceLine
from django.db.models import Max


class InvoiceLineSerializer(serializers.ModelSerializer):
    total_ht  = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_tva = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_ttc = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = InvoiceLine
        fields = [
            "id", "description", "quantity",
            "unit_price_ht", "tva_rate",
            "total_ht", "total_tva", "total_ttc",
        ]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        return value

    def validate_unit_price_ht(self, value):
        if value < 0:
            raise serializers.ValidationError("The unit price cannot be negative.")
        return value

    def validate_tva_rate(self, value):
        # Accept any percentage between 1 and 100 when TVA is applied.
        # If the parent invoice has apply_tva=False and value == 0, allow 0.
        try:
            dec = Decimal(str(value))
        except Exception:
            raise serializers.ValidationError("Invalid number for tva_rate.")

        # Check if apply_tva was explicitly disabled in the invoice payload
        apply_tva_flag = None
        try:
            # parent -> ListSerializer -> parent (InvoiceCreateSerializer)
            invoice_initial = getattr(self.parent, 'parent', None)
            if invoice_initial is not None and hasattr(invoice_initial, 'initial_data'):
                apply_tva_flag = invoice_initial.initial_data.get('apply_tva')
        except Exception:
            apply_tva_flag = None

        if apply_tva_flag is False and dec == Decimal("0"):
            return value

        if dec < Decimal("1") or dec > Decimal("100"):
            raise serializers.ValidationError("tva_rate must be between 1 and 100 when TVA is applied.")
        return value


class InvoiceCreateSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)

    # Read-only computed fields
    total_ht   = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_tva  = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_ttc  = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = Invoice
        fields = [
            "id",
            "client",
            "supplier",
            "invoice_number", "invoice_type", "invoice_subtype",
            "invoice_date", "due_date", "service_date",
            "payment_method", "payment_conditions",
            "currency", "status", "client_category",
            "apply_tva",
            "attachment",
            "total_ht", "total_tva", "total_ttc", "amount_paid",
            "lines",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "invoice_number", "status",
            "total_ht", "total_tva", "total_ttc",
            "amount_paid", "created_at", "updated_at",
        ]

    # ── Validation ──────────────────────────────────────────
    def validate(self, attrs):
        invoice_type = attrs.get("invoice_type")
        client       = attrs.get("client")
        supplier     = attrs.get("supplier")

        # vente → client required
        if invoice_type == "vente" and not client:
            raise serializers.ValidationError(
                {"client": "A client is required for a sales invoice."}
            )
        # achat → supplier required
        if invoice_type == "achat" and not supplier:
            raise serializers.ValidationError(
                {"supplier": "A supplier is required for a purchase invoice."}
            )

        lines = attrs.get("lines", [])
        if not lines:
            raise serializers.ValidationError(
                {"lines": "At least one line item is required."}
            )

        # TVA OFF হলে tva_rate থাকলেও warn করবো না, শুধু 0 করবো
        if not attrs.get("apply_tva", True):
            for line in lines:
                line["tva_rate"] = 0

        return attrs

    def validate_client(self, client):
        """Client must belong to the authenticated user."""
        request = self.context.get("request")
        if client and request:
            if client.user != request.user:
                raise serializers.ValidationError(
                    "This client does not belong to your account."
                )
        return client

    def validate_supplier(self, supplier):
        """Supplier must belong to the authenticated user."""
        request = self.context.get("request")
        if supplier and request:
            if supplier.user != request.user:
                raise serializers.ValidationError(
                    "This supplier does not belong to your account."
                )
        return supplier

    def validate_due_date(self, value):
        invoice_date = self.initial_data.get("invoice_date")
        if invoice_date and value:
            from datetime import date
            if str(value) < str(invoice_date):
                raise serializers.ValidationError(
                    "The due date cannot be earlier than the invoice date."
                )
        return value

    # ── Create ──────────────────────────────────────────────
    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        company    = validated_data["company"]

        # Auto invoice number
        last = Invoice.objects.filter(company=company).aggregate(Max("accounting_number"))
        next_num = (last["accounting_number__max"] or 0) + 1
        year     = str(validated_data["invoice_date"])[:4]

        validated_data["accounting_number"] = next_num
        validated_data["invoice_number"]    = f"F-{year}-{next_num:04d}"
        validated_data["status"]            = "brouillon"

        invoice = Invoice.objects.create(**validated_data)

        # Lines save
        for line_data in lines_data:
            line = InvoiceLine(invoice=invoice, **line_data)
            line.save()  # auto compute total_ht/tva/ttc

        # Invoice totals
        invoice.compute_totals()
        invoice.save()

        return invoice

    # ── Update ──────────────────────────────────────────────
    def update(self, instance, validated_data):
        if instance.is_frozen:
            raise serializers.ValidationError(
                "This invoice is locked and can no longer be modified."
            )

        lines_data = validated_data.pop("lines", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                line = InvoiceLine(invoice=instance, **line_data)
                line.save()

        instance.compute_totals()
        instance.save()
        return instance


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight — list table-এর জন্য।"""
    clientSupplier_name     = serializers.SerializerMethodField()
    payment_percent = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model  = Invoice
        fields = [
            "id",
            "client",
            "clientSupplier_name",
            "supplier",
            "invoice_number", "invoice_type", "invoice_subtype",
            "invoice_date", "due_date", "service_date",
            "payment_method", "payment_conditions",
            "currency", "status", "client_category",
            "apply_tva",
            "attachment",
            "total_ht", "total_tva", "total_ttc", "amount_paid",
            "payment_percent",
            "remaining_balance",
            "created_at", "updated_at",
        ]
    def get_clientSupplier_name(self, obj):
        if obj.client:
            if obj.client.client_type == "Indépendant":
                return f"{obj.client.first_name} {obj.client.last_name}"
            return obj.client.company_name or ""
        if obj.supplier:
            if obj.supplier.client_type == "Indépendant":
                return f"{obj.supplier.first_name} {obj.supplier.last_name}"
            return obj.supplier.company_name or ""
        return ""

    def get_payment_percent(self, obj):
        if obj.total_ttc and obj.total_ttc > 0:
            return round((obj.amount_paid / obj.total_ttc) * 100)
        return 0
    def get_remaining_balance(self, obj):
        try:
            return obj.total_ttc - obj.amount_paid
        except Exception:
            return None
    
    
    
class InvoiceShortListSerializer(serializers.ModelSerializer):
    """Short list for dropdowns, etc."""
    ClientSupplierName = serializers.SerializerMethodField()
    total_ht = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_tva = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_ttc = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = Invoice
        fields = ["id", "invoice_number", "ClientSupplierName", "total_ht", "total_tva", "total_ttc"]
        
    def get_ClientSupplierName(self, obj):
        if obj.client:
            if obj.client.client_type == "Indépendant":
                return f"{obj.client.first_name} {obj.client.last_name}"
            return obj.client.company_name or ""
        if obj.supplier:
            if obj.supplier.client_type == "Indépendant":
                return f"{obj.supplier.first_name} {obj.supplier.last_name}"
            return obj.supplier.company_name or ""
        return ""


class BankOperationSerializer(serializers.ModelSerializer):
    invoice = serializers.PrimaryKeyRelatedField(source="linked_invoice", queryset=Invoice.objects.all(), write_only=True, required=False)
    category = serializers.CharField(required=False, allow_blank=True)
    invoice_number = serializers.CharField(source="linked_invoice.invoice_number", read_only=True)
    invoice_total = serializers.DecimalField(source="linked_invoice.total_ttc", max_digits=12, decimal_places=2, read_only=True)
    invoice_remaining_balance = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    reconciliation_status_label = serializers.SerializerMethodField()
    payment_status_label = serializers.SerializerMethodField()

    class Meta:
        model = BankOperation
        fields = [
            "id",
            "invoice",
            "linked_invoice",
            "invoice_number",
            "invoice_total",
            "invoice_remaining_balance",
            "payment_date",
            "category",
            "amount",
            "payment_direction",
            "payment_method",
            "bank_account",
            "bank_reference",
            "attachment",
            "notes",
            "reconciliation_status",
            "reconciliation_status_label",
            "payment_status",
            "payment_status_label",
            "is_validated",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "invoice_number",
            "invoice_total",
            "invoice_remaining_balance",
            "reconciliation_status",
            "reconciliation_status_label",
            "payment_status",
            "payment_status_label",
            "is_validated",
            "created_at",
            "updated_at",
        ]

    def get_invoice_remaining_balance(self, obj):
        if not obj.linked_invoice:
            return None
        return obj.linked_invoice.total_ttc - obj.linked_invoice.amount_paid

    def get_payment_status(self, obj):
        return obj.get_payment_status()

    def get_payment_status_label(self, obj):
        labels = {
            "unpaid": "Unpaid",
            "partial": "Partial",
            "paid": "Paid",
            "overpaid": "Overpaid",
            "pending": "Pending",
        }
        return labels.get(obj.get_payment_status(), obj.get_payment_status())

    def get_reconciliation_status_label(self, obj):
        labels = {
            "not_linked": "Not linked",
            "partially_reconciled": "Partially reconciled",
            "reconciled": "Reconciled / Validated",
        }
        return labels.get(obj.get_reconciliation_status(), obj.get_reconciliation_status())

    def validate(self, attrs):
        request = self.context.get("request")
        linked_invoice = attrs.get("linked_invoice")

        if linked_invoice and request and linked_invoice.company != request.user:
            raise serializers.ValidationError({"linked_invoice": "This invoice does not belong to your account."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user:
            validated_data["user"] = request.user

        linked_invoice = validated_data.get("linked_invoice")
        if linked_invoice and not validated_data.get("category"):
            validated_data["category"] = f"Paiement lié à la facture: {linked_invoice.invoice_number}"

        with transaction.atomic():
            return super().create(validated_data)

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance.revert_from_invoice()

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            if instance.linked_invoice and not instance.category:
                instance.category = f"Paiement lié à la facture: {instance.linked_invoice.invoice_number}"

            if not instance.linked_invoice:
                instance.reconciliation_status = "not_linked"
            instance.apply_to_invoice()
            instance.save()
            return instance


class BankOperationSummarySerializer(serializers.Serializer):
    month = serializers.CharField()
    incoming_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    outgoing_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoice_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    manual_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    validated_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()


class BankOperationCreateResponseSerializer(serializers.Serializer):
    operation = BankOperationSerializer()
    invoice_payment_status = serializers.CharField(allow_null=True)
    reconciliation_status = serializers.CharField()


class BankOperationAccountingBlockSerializer(serializers.Serializer):
    account = serializers.SerializerMethodField()
    accounting_export = serializers.SerializerMethodField()
    accounting_label_search = serializers.SerializerMethodField()
    third_party_accounting = serializers.SerializerMethodField()
    automatic_third_party_accounting = serializers.SerializerMethodField()
    final_export = serializers.SerializerMethodField()
    income_statement_year = serializers.SerializerMethodField()

    def _counterparty_name(self, obj):
        invoice = obj.linked_invoice
        if not invoice:
            return obj.category or ""

        if invoice.client:
            if invoice.client.client_type == "Indépendant":
                return f"{invoice.client.first_name} {invoice.client.last_name}".strip()
            return invoice.client.company_name or invoice.client.email or ""

        if invoice.supplier:
            if invoice.supplier.client_type == "Indépendant":
                return f"{invoice.supplier.first_name} {invoice.supplier.last_name}".strip()
            return invoice.supplier.company_name or invoice.supplier.email or ""

        return obj.category or ""

    def get_account(self, obj):
        user = getattr(obj, "user", None)
        if not user:
            return ""
        return user.company_name or user.full_name or user.email or ""

    def get_accounting_export(self, obj):
        if obj.bank_reference:
            return obj.bank_reference
        if obj.linked_invoice:
            return obj.linked_invoice.invoice_number
        return f"TRX-{obj.id:06d}"

    def get_accounting_label_search(self, obj):
        return "Entree" if obj.payment_direction == "incoming" else "Sortie"

    def get_third_party_accounting(self, obj):
        return self._counterparty_name(obj)

    def get_automatic_third_party_accounting(self, obj):
        labels = {
            "bank_transfer": "Virement",
            "cash": "Espèces",
            "card": "Carte",
            "cheque": "Chèque",
            "direct_debit": "Prelevement",
            "other": "Autre",
        }
        return labels.get(obj.payment_method, obj.payment_method)

    def get_final_export(self, obj):
        if obj.bank_reference:
            return obj.bank_reference
        if obj.linked_invoice:
            return f"REF-{obj.linked_invoice.invoice_number}"
        return f"REF-{obj.id:06d}"

    def get_income_statement_year(self, obj):
        if obj.payment_date:
            return obj.payment_date.year
        return timezone.now().year


class BankOperationDetailResponseSerializer(serializers.Serializer):
    pure_accounting_block = BankOperationAccountingBlockSerializer(source="*")
    advanced_reconciliation_block = serializers.SerializerMethodField()

    def get_advanced_reconciliation_block(self, obj):
        user = getattr(obj, "user", None)
        account = ""
        if user:
            account = user.company_name or user.full_name or user.email or ""
        return {"account": account}
    