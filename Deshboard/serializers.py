from rest_framework import serializers
from .models import Client, Supplier
from decimal import Decimal


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
    