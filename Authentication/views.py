from rest_framework.views import APIView
from rest_framework import status
from Authentication.serializers import RegisterSerializer
from utils.api_response import APIResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return APIResponse.success(
                message="Registration successful",
                data={
                    "user_id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                }
            )

        return APIResponse.error(
            message="Registration failed",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
        
class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return APIResponse.error(
                message="Email and password required",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)

        if not user:
            return APIResponse.error(
                message="Invalid credentials",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        return APIResponse.success(
            message="Login successful",
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        )
        
