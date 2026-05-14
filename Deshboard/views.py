from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Client
from .serializers import (
   IndependentClientSerializer,
    CompanyClientSerializer,
    ClientSerializer,
)

SERIALIZER_MAP = {
    "Indépendant": IndependentClientSerializer,
    "Société": CompanyClientSerializer,
}


class ClientCreateView(APIView):
    """
    POST /clients/
    Body must include client_type = "Indépendant" | "Société"
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        client_type = request.data.get("client_type")

        SerializerClass = SERIALIZER_MAP.get(client_type)
        if not SerializerClass:
            return Response(
                {"client_type": "Valeur invalide. Choisissez 'Indépendant' ou 'Société'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SerializerClass(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientListView(APIView):
    """GET /clients/ — list all clients belonging to the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clients = Client.objects.filter(user=request.user).order_by("-created_at")
        serializer = ClientSerializer(clients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
            return Response({"detail": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClientSerializer(client).data)

    def patch(self, request, pk):
        client = self.get_object(pk, request.user)
        if not client:
            return Response({"detail": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)

        # Route to the right serializer based on stored client_type
        SerializerClass = SERIALIZER_MAP.get(client.client_type, ClientSerializer)
        serializer = SerializerClass(client, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        client = self.get_object(pk, request.user)
        if not client:
            return Response({"detail": "Client introuvable."}, status=status.HTTP_404_NOT_FOUND)
        client.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)