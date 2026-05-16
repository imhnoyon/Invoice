from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from utils.paginations import CustomPagination
from utils.api_response import APIResponse

from .models import Client, Supplier
from .serializers import (
   IndependentClientSerializer,
    CompanyClientSerializer,
    ClientSerializer,
    IndividualSupplierSerializer,
    CompanySupplierSerializer,
    SupplierSerializer
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