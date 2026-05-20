from rest_framework.views import APIView
from rest_framework import status
from Authentication.serializers import RegisterSerializer
from utils.api_response import APIResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.password_validation import validate_password

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
                "role": user.role,
            }
        )
        
        
        
# Profile 
class UserDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(
            request.user,
            context={"request": request}
        )

        return APIResponse.success(
            message="User details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        
    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                message="User details updated successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        return APIResponse.error(
            message="Failed to update user details.",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
        
# Personal details update 
class UserpersonalDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserpersonalDetailsSerializer(
            request.user,
            context={"request": request}
        )

        return APIResponse.success(
            message="User details retrieved successfully.",
            data=serializer.data,
            status_code=status.HTTP_200_OK
        )
        
    def patch(self, request):
        serializer = UserpersonalDetailsSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return APIResponse.success(
                message="User details updated successfully.",
                data=serializer.data,
                status_code=status.HTTP_200_OK
            )

        return APIResponse.error(
            message="Failed to update user details.",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )




class PasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data["new_password"]
            validate_password(new_password, request.user)
            request.user.set_password(new_password)
            request.user.save()
            return APIResponse.success(
                message="Password changed successfully."
            )
        return APIResponse.error(
            message="Failed to change password.",
            data=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )