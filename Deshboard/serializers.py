from rest_framework import serializers
from .models import Client


class IndependentClientSerializer(serializers.ModelSerializer):
    client_type = serializers.HiddenField(default="Indépendant")

    class Meta:
        model = Client
        fields = ["id", "client_type", "first_name", "last_name","email", "phone", "billing_address", "postal_code", "city", 
                  "country","client_category", "internal_notes","created_at", "updated_at",]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        if not attrs.get("first_name"):
            raise serializers.ValidationError({"first_name": "Ce champ est obligatoire pour un indépendant."})
        if not attrs.get("last_name"):
            raise serializers.ValidationError({"last_name": "Ce champ est obligatoire pour un indépendant."})
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
            raise serializers.ValidationError({"company_name": "Ce champ est obligatoire pour une société."})
        if not attrs.get("siren_siret"):
            raise serializers.ValidationError({"siren_siret": "Ce champ est obligatoire pour une société."})
        return attrs


class ClientSerializer(serializers.ModelSerializer):
    """Read serializer — returns all fields for list/retrieve."""

    class Meta:
        model = Client
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at"]