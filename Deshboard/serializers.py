from rest_framework import serializers
from .models import Client, Supplier


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
            raise serializers.ValidationError("Quantité doit être supérieure à 0.")
        return value

    def validate_unit_price_ht(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix unitaire ne peut pas être négatif.")
        return value

    def validate_tva_rate(self, value):
        allowed = [0, 2.1, 5.5, 8.5, 10, 17, 20, 21]
        if float(value) not in allowed:
            raise serializers.ValidationError(f"Taux TVA invalide. Choisissez parmi : {allowed}")
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
                {"client": "Le nom du client est requis pour une vente."}
            )
        # achat → supplier required
        if invoice_type == "achat" and not supplier:
            raise serializers.ValidationError(
                {"supplier": "Le fournisseur est requis pour un achat."}
            )

        lines = attrs.get("lines", [])
        if not lines:
            raise serializers.ValidationError(
                {"lines": "Au moins une ligne d'article est requise."}
            )

        # TVA OFF হলে tva_rate থাকলেও warn করবো না, শুধু 0 করবো
        if not attrs.get("apply_tva", True):
            for line in lines:
                line["tva_rate"] = 0

        return attrs

    def validate_client(self, client):
        """Client অবশ্যই এই company-র হতে হবে।"""
        request = self.context.get("request")
        if client and request:
            company = request.user.company
            if client.company != company:
                raise serializers.ValidationError(
                    "Ce client n'appartient pas à votre entreprise."
                )
        return client

    def validate_due_date(self, value):
        invoice_date = self.initial_data.get("invoice_date")
        if invoice_date and value:
            from datetime import date
            if str(value) < str(invoice_date):
                raise serializers.ValidationError(
                    "La date d'échéance ne peut pas être antérieure à la date de facture."
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
            # apply_tva=False হলে tva force 0
            if not invoice.apply_tva:
                line.tva_rate = 0
            line.save()  # auto compute total_ht/tva/ttc

        # Invoice totals
        invoice.compute_totals()
        invoice.save()

        return invoice

    # ── Update ──────────────────────────────────────────────
    def update(self, instance, validated_data):
        if instance.is_frozen:
            raise serializers.ValidationError(
                "Cette facture est verrouillée et ne peut plus être modifiée."
            )

        lines_data = validated_data.pop("lines", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                line = InvoiceLine(invoice=instance, **line_data)
                if not instance.apply_tva:
                    line.tva_rate = 0
                line.save()

        instance.compute_totals()
        instance.save()
        return instance


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight — list table-এর জন্য।"""
    client_name     = serializers.SerializerMethodField()
    payment_percent = serializers.SerializerMethodField()

    class Meta:
        model  = Invoice
        fields = [
            "id", "invoice_number", "invoice_type", "invoice_subtype",
            "client_name", "client_category",
            "invoice_date", "status", "is_frozen",
            "total_ht", "total_tva", "total_ttc",
            "amount_paid", "payment_percent",
        ]

    def get_client_name(self, obj):
        if obj.client:
            if obj.client.client_type == "independent":
                return f"{obj.client.first_name} {obj.client.last_name}"
            return obj.client.company_name or ""
        if obj.supplier:
            return obj.supplier.name
        return ""

    def get_payment_percent(self, obj):
        if obj.total_ttc and obj.total_ttc > 0:
            return round((obj.amount_paid / obj.total_ttc) * 100)
        return 0