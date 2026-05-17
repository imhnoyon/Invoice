from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager

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
    role = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="user")
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)

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
        