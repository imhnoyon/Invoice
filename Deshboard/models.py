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
    
    
    
    
# Invoice Section
class Invoice(models.Model):
    TYPE_CHOICES = (
        ("vente", "Vente"),
        ("achat", "Achat"),
    )
    SUBTYPE_CHOICES = (
        ("facture", "Facture"),
        ("avoir",   "Avoir"),
    )
    STATUS_CHOICES = (
        ("brouillon",  "Brouillon"),
        ("a_traiter",  "À traiter"),
        ("traite",     "Traité"),
        ("verrouille", "Verrouillé / Exporté"),
    )
    PAYMENT_METHOD_CHOICES = (
        ("virement_bancaire", "Virement bancaire"),
        ("cheque",            "Chèque"),
        ("especes",           "Espèces"),
        ("carte_bancaire",    "Carte bancaire"),
        ("prelevement",       "Prélèvement automatique"),
    )
    PAYMENT_CONDITIONS_CHOICES = (
        ("immediate", "Immédiat"),
        ("15_jours",  "15 jours"),
        ("30_jours",  "30 jours"),
        ("45_jours",  "45 jours"),
        ("60_jours",  "60 jours"),
    )
    CLIENT_CATEGORY_CHOICES = (
        ("france_b2b_b2c", "France (B2B & B2C)"),
        ("eu_b2b",         "UE B2B"),
        ("eu_b2c",         "UE B2C"),
        ("non_eu",         "Hors UE"),
    )
    CURRENCY_CHOICES = (
        ("EUR", "€ Euro"),
        ("USD", "$ Dollar"),
        ("GBP", "£ Livre sterling"),
    )

    # Tenant isolation — MANDATORY per PDF spec
    company  = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")

    # Parties
    client   = models.ForeignKey(Client,   null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices")

    # Identity
    invoice_number     = models.CharField(max_length=50)       # accounting doc number, unique per company
    accounting_number  = models.PositiveIntegerField(null=True) # sequential: 1,2,3… per company
    invoice_type       = models.CharField(max_length=20, choices=TYPE_CHOICES)
    invoice_subtype    = models.CharField(max_length=20, choices=SUBTYPE_CHOICES, default="facture")
    original_invoice   = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="avoirs")

    # Dates
    invoice_date  = models.DateField()
    due_date      = models.DateField(null=True, blank=True)
    service_date  = models.DateField(null=True, blank=True)
    accounting_month = models.CharField(max_length=7, blank=True)  # "2024-12"

    # Payment
    payment_method     = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_conditions = models.CharField(max_length=50, choices=PAYMENT_CONDITIONS_CHOICES, blank=True)
    currency           = models.CharField(max_length=10, choices=CURRENCY_CHOICES, default="EUR")

    # Status & Category
    status          = models.CharField(max_length=30, choices=STATUS_CHOICES, default="brouillon")
    client_category = models.CharField(max_length=50, choices=CLIENT_CATEGORY_CHOICES, blank=True)
    apply_tva       = models.BooleanField(default=True)

    # Attachment (PDF/image upload)
    attachment = models.FileField(upload_to="invoices/%Y/%m/", null=True, blank=True)

    # Totals (computed from lines)
    total_ht   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Accounting account (e.g. 411000)
    accounting_account = models.CharField(max_length=20, blank=True)

    # CSC / freeze status
    is_frozen = models.BooleanField(default=False)

    # Airtable sync
    airtable_id = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("company", "invoice_number")
        ordering = ["-invoice_date", "-accounting_number"]

    def compute_totals(self):
        lines = self.lines.all()
        self.total_ht  = sum(l.total_ht  for l in lines)
        self.total_tva = sum(l.total_tva for l in lines)
        self.total_ttc = self.total_ht + self.total_tva

    def set_accounting_month(self):
        if self.invoice_date:
            self.accounting_month = self.invoice_date.strftime("%Y-%m")

    def save(self, *args, **kwargs):
        self.set_accounting_month()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} ({self.company.company_name})"


# ─────────────────────────────────────────
# 7. INVOICE LINE
# ─────────────────────────────────────────
class InvoiceLine(models.Model):
    invoice        = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    description    = models.CharField(max_length=500)
    quantity       = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price_ht  = models.DecimalField(max_digits=12, decimal_places=2)
    tva_rate       = models.DecimalField(max_digits=5,  decimal_places=2, default=0)

    # Computed
    total_ht  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total_ht  = self.quantity * self.unit_price_ht
        self.total_tva = self.total_ht * (self.tva_rate / 100)
        self.total_ttc = self.total_ht + self.total_tva
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice.invoice_number} – {self.description}"