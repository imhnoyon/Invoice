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