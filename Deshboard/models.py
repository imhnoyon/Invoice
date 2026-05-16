from django.db import models
from Authentication.models import User
from django_countries.fields import CountryField


class Client(models.Model):

    CLIENT_TYPE_CHOICES = (
    ("Indépendant", "Indépendant"),
    ("Société", "Société"),)

    CLIENT_CATEGORY_CHOICES = (
    ("Client dans l'UE (hors France)", "Client dans l'UE (hors France)"),
    ("Client hors UE", "Client hors UE"),
    ("Client en France", "Client en France"),)
    
    CITY_CHOICES = (
    ("Paris", "Paris"),
    ("Lyon", "Lyon"),
    ("Marseille", "Marseille"),
    ("Bordeaux", "Bordeaux"),
    ("Toulouse", "Toulouse"),)
       
    COUNTRY_CHOICES = (
    ("France", "France"),
    ("Belgique", "Belgique"),
    ("Suisse", "Suisse"),
    ("Luxembourg", "Luxembourg"),)
    
    #User 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="clients")

    # Common Fields
    client_type = models.CharField(max_length=20,choices=CLIENT_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    billing_address = models.TextField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100, choices=CITY_CHOICES)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)

    client_category = models.CharField(max_length=100,choices=CLIENT_CATEGORY_CHOICES)
    internal_notes = models.TextField(blank=True,null=True)

    # Individual Fields
    first_name = models.CharField(max_length=100,blank=True,null=True)
    last_name = models.CharField(max_length=100,blank=True,null=True)

    # Company Fields
    client_name = models.CharField(max_length=255,blank=True,null=True)
    company_name = models.CharField(max_length=255,blank=True,null=True)
    siren_siret = models.CharField(max_length=100,blank=True,null=True)
    vat_number = models.CharField(max_length=100,blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.client_type == "Indépendant":
            return f"{self.first_name} {self.last_name}"
        return self.company_name or self.email
    
    
from django.utils.translation import override    
class FrenchCountryField(CountryField):
    def get_choices(self, *args, **kwargs):
        with override("fr"):
            return super().get_choices(*args, **kwargs)
    
class Supplier(models.Model):

    SUPPLIER_TYPE_CHOICES = (
    ("Indépendant", "Indépendant"),
    ("Société", "Société"),)

    CLIENT_CATEGORY_CHOICES = (
    ("Client dans l'UE (hors France)", "Client dans l'UE (hors France)"),
    ("Client hors UE", "Client hors UE"),
    ("Client en France", "Client en France"),)
    
    CITY_CHOICES = (
    ("Paris", "Paris"),
    ("Lyon", "Lyon"),
    ("Marseille", "Marseille"),
    ("Bordeaux", "Bordeaux"),
    ("Toulouse", "Toulouse"),)
       
    COUNTRY_CHOICES = (
    ("France", "France"),
    ("Belgique", "Belgique"),
    ("Suisse", "Suisse"),
    ("Luxembourg", "Luxembourg"),)
    
    
    PAYMENT_METHOD_CHOICES = (
    ("Virement bancaire", "Virement bancaire"),  # Bank Transfer
    ("Chèque", "Chèque"),                      # Cheque
    ("Carte de crédit", "Carte de crédit"),    # Credit Card
    ("Espèces", "Espèces"),                    # Cash
)
    
    #User 
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="suppliers")

    # Common Fields
    client_type = models.CharField(max_length=20,choices=SUPPLIER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    billing_address = models.TextField()
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100, choices=CITY_CHOICES)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES)
    client_category = models.CharField(max_length=100,choices=CLIENT_CATEGORY_CHOICES)
    internal_notes = models.TextField(blank=True,null=True)

    # Individual Fields
    first_name = models.CharField(max_length=100,blank=True,null=True)
    last_name = models.CharField(max_length=100,blank=True,null=True)

    # Company Fields
    client_name = models.CharField(max_length=255,blank=True,null=True)
    company_name = models.CharField(max_length=255,blank=True,null=True)
    siren_siret = models.CharField(max_length=100,blank=True,null=True)
    vat_number = models.CharField(max_length=100,blank=True,null=True)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.client_type == "Indépendant":
            return f"{self.first_name} {self.last_name}"
        return self.company_name or self.email