from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from .utils import COUNTRY_TYPES
    
class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(
            email,
            password,
            **extra_fields
        )
        
        
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ("admin", "Admin"),
        ("user", "User"),
        ("pro_user", "Pro_user"),
    )
    
    CURRANCY_CHOICES = (
        ("USD", "Dollar"),
        ("EUR", "Euro"),
        ("GBP", "GBP"),
       
    )

    FORM_CHOICES = (
        ("SARL", "SARL"),
        ("SAS", "SAS"),
        ("SASU", "SASU"),
        ("EURL", "EURL"),
        ("EI", "EI"),
    )
    
    role = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="user")
    full_name = models.CharField(max_length=255)
    surename = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    company_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, choices=COUNTRY_TYPES)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)
 
    
    #Company Information
    company_address = models.CharField(max_length=255, blank=True, null=True)
    company_country= models.CharField(max_length=100, blank=True, null=True, choices=COUNTRY_TYPES)
    siren_siret_number = models.CharField(max_length=14, blank=True, null=True)
    default_currency = models.CharField(max_length=10, blank=True, null=True, choices=CURRANCY_CHOICES, default="EUR")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    legal_form = models.CharField(max_length=50, blank=True, null=True, choices=FORM_CHOICES, default="SARL")
    business_sector = models.CharField(max_length=100, blank=True, null=True)
    share_capital = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rcs_city = models.CharField(max_length=100, blank=True, null=True)

    username = None

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    objects = UserManager()

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)
        