from rest_framework import serializers
from .models import User
from django.utils.translation import override



class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["full_name", "email", "company_name", "country", "password", "confirm_password"]

        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "company_name", "company_address", "company_country",  "email", "siren_siret_number", "default_currency", 
                  "phone_number", "legal_form", "business_sector", "share_capital", "rcs_city",]



class UserpersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "surename", "email", "phone_number", "profile_picture"]
        
        
        
        
class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)
    
   

    