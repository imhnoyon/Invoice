"""
Accounting Export Module - Generates detailed accounting journal entries
with complete financial data structured for accounting software export.

This module is independent and does not modify existing functionality.
"""
from decimal import Decimal
from django.db.models import Sum, F, Value, DecimalField, Q, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Invoice, InvoiceLine, BankOperation
import random



def generate_account():
    random_number = random.randint(1000, 9999)
    return f"Acc-{random_number}"



def _format_currency(value):
    """Format decimal value to currency string with space separator."""
    amount = Decimal(str(value or 0))
    if amount == amount.to_integral():
        return f"{int(amount):,} €".replace(",", " ")
    return f"{amount.quantize(Decimal('0.01')):f} €".replace(".", ",")


def _month_label(month_number):
    """Get French month name from month number."""
    labels = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ]
    return labels[month_number - 1]


class AccountingJournalBuilder:
    """Builds comprehensive accounting journal with all transaction types."""
    
    def __init__(self, user, year=None, month=None):
        self.user = user
        self.year = int(year or timezone.now().year)
        self.month = int(month) if month else None
        self.today = timezone.localdate()
        self.entry_counter = 0
    
    def _next_entry_number(self):
        """Generate sequential entry number."""
        self.entry_counter += 1
        return self.entry_counter
    
    def _get_company_info(self):
        """Get dynamic company information from user."""
        return {
            "name": self.user.company_name or "TESTCOMPTA SARL",
            "siret": self.user.siren_siret_number or "123 456 789",
            "legal_form": self.user.legal_form or "SARL",
            "rcs_city": self.user.rcs_city or "Paris",
            "fiscal_year_start": f"01/01/{self.year}",
            "fiscal_year_end": f"31/12/{self.year}",
        }
    
    def _get_invoices_queryset(self):
        """Get base invoices queryset filtered by user and date range."""
        qs = Invoice.objects.filter(
            company=self.user,
            invoice_type__in=["vente", "achat"],
            invoice_subtype="factura"
        )
        
        if self.month:
            qs = qs.filter(invoice_date__year=self.year, invoice_date__month=self.month)
        else:
            qs = qs.filter(invoice_date__year=self.year)
        
        return qs
    
    def _build_purchase_entries(self):
        """Generate accounting entries for purchase invoices (ACH)."""
        entries = []
        
        purchases = Invoice.objects.filter(
            company=self.user,
            invoice_type="achat",
            invoice_subtype="factura"
        )
        
        if self.month:
            purchases = purchases.filter(
                invoice_date__year=self.year,
                invoice_date__month=self.month
            )
        else:
            purchases = purchases.filter(invoice_date__year=self.year)
        
        for invoice in purchases:
            lines = invoice.invoiceline_set.all()
            
            for line in lines:
                entry_num = self._next_entry_number()
                
                # Main purchase entry
                entry = {
                    "journal": "ACH",
                    "entry_number": entry_num,
                    "date": invoice.invoice_date.strftime("%d/%m/%Y"),
                    "account": generate_account(),
                    "account_label": "Fournisseurs",
                    "auxiliary": "SARL ISTM",
                    "tiers": invoice.supplier.name if invoice.supplier else "---",
                    "piece_ref": invoice.invoice_number or f"ACH-{entry_num}",
                    "piece_date": invoice.invoice_date.strftime("%d/%m/%Y"),
                    "description": line.description or "Achat fournitures",
                    "debit": float(line.line_total_ht) if line.line_total_ht else 0,
                    "credit": 0,
                }
                entries.append(entry)
                
                # TVA deductible entry
                if line.tva_rate and line.tva_rate > 0:
                    tva_amount = line.line_total_ht * (Decimal(str(line.tva_rate)) / Decimal("100"))
                    entry_num = self._next_entry_number()
                    entries.append({
                        "journal": "ACH",
                        "entry_number": entry_num,
                        "date": invoice.invoice_date.strftime("%d/%m/%Y"),
                        "account": generate_account(),
                        "account_label": f"TVA déductible {line.tva_rate}%",
                        "auxiliary": "SARL ISTM",
                        "tiers": invoice.supplier.name if invoice.supplier else "---",
                        "piece_ref": invoice.invoice_number or f"ACH-{entry_num}",
                        "piece_date": invoice.invoice_date.strftime("%d/%m/%Y"),
                        "description": f"TVA déductible {line.tva_rate}%",
                        "debit": float(tva_amount),
                        "credit": 0,
                    })
        
        return entries
    
    def _build_sales_entries(self):
        """Generate accounting entries for sales invoices (VEN)."""
        entries = []
        
        sales = Invoice.objects.filter(
            company=self.user,
            invoice_type="vente",
            invoice_subtype="factura"
        )
        
        if self.month:
            sales = sales.filter(
                invoice_date__year=self.year,
                invoice_date__month=self.month
            )
        else:
            sales = sales.filter(invoice_date__year=self.year)
        
        for invoice in sales:
            lines = invoice.invoiceline_set.all()
            
            for line in lines:
                entry_num = self._next_entry_number()
                
                # Main sales entry
                entry = {
                    "journal": "VEN",
                    "entry_number": entry_num,
                    "date": invoice.invoice_date.strftime("%d/%m/%Y"),
                    "account": generate_account(),
                    "account_label": "Clients",
                    "auxiliary": str(invoice.client.id) if invoice.client else "---",
                    "tiers": invoice.client.name if invoice.client else "---",
                    "piece_ref": invoice.invoice_number or f"VEN-{entry_num}",
                    "piece_date": invoice.invoice_date.strftime("%d/%m/%Y"),
                    "description": line.description or "Vente services",
                    "debit": 0,
                    "credit": float(line.line_total_ht) if line.line_total_ht else 0,
                }
                entries.append(entry)
                
                # TVA collected entry
                if line.tva_rate and line.tva_rate > 0:
                    tva_amount = line.line_total_ht * (Decimal(str(line.tva_rate)) / Decimal("100"))
                    entry_num = self._next_entry_number()
                    entries.append({
                        "journal": "VEN",
                        "entry_number": entry_num,
                        "date": invoice.invoice_date.strftime("%d/%m/%Y"),
                        "account": generate_account(),
                        "account_label": f"TVA collectée {line.tva_rate}%",
                        "auxiliary": str(invoice.client.id) if invoice.client else "---",
                        "tiers": invoice.client.name if invoice.client else "---",
                        "piece_ref": invoice.invoice_number or f"VEN-{entry_num}",
                        "piece_date": invoice.invoice_date.strftime("%d/%m/%Y"),
                        "description": f"TVA collectée {line.tva_rate}%",
                        "debit": 0,
                        "credit": float(tva_amount),
                    })
        
        return entries
    
    def _build_bank_entries(self):
        """Generate accounting entries for bank operations (BAN)."""
        entries = []
        
        operations = BankOperation.objects.filter(user=self.user)
        
        if self.month:
            operations = operations.filter(
                payment_date__year=self.year,
                payment_date__month=self.month
            )
        else:
            operations = operations.filter(payment_date__year=self.year)
        
        for operation in operations:
            entry_num = self._next_entry_number()
            
            # Map payment method to account
            account_map = {
                "bank_transfer": "bank_transfer",
                "cash": "cash",
                "card": "card",
                "cheque": "cheque",
                "direct_debit": "direct_debit",
                "other": "other",
            }
            account = account_map.get(operation.payment_method, "512000")
            
            entry = {
                "journal": "BAN",
                "entry_number": entry_num,
                "date": operation.payment_date.strftime("%d/%m/%Y"),
                "account": account,
                "account_label": operation.category or "Banque",
                "auxiliary": operation.bank_reference or "---",
                "tiers": operation.bank_reference or operation.category or "---",
                "piece_ref": operation.bank_reference or f"BAN-{entry_num}",
                "piece_date": operation.payment_date.strftime("%d/%m/%Y"),
                "description": operation.notes or operation.category or "Opération bancaire",
                "debit": float(operation.amount) if operation.payment_direction == "incoming" else 0,
                "credit": float(operation.amount) if operation.payment_direction == "outgoing" else 0,
            }
            entries.append(entry)
        
        return entries
    
    def _get_salary_entries(self):
        """Get salary entries from bank operations marked as salaries (SAL)."""
        entries = []
        
        # Query bank operations with salary-related categories
        salary_operations = BankOperation.objects.filter(
            user=self.user,
            category__icontains="salaire"
        )
        
        if self.month:
            salary_operations = salary_operations.filter(
                payment_date__year=self.year,
                payment_date__month=self.month
            )
        else:
            salary_operations = salary_operations.filter(payment_date__year=self.year)
        
        for operation in salary_operations:
            entry_num = self._next_entry_number()
            
            entry = {
                "journal": "SAL",
                "entry_number": entry_num,
                "date": operation.payment_date.strftime("%d/%m/%Y"),
                "account": generate_account(),
                "account_label": "Personnel",
                "auxiliary": "Employees",
                "tiers": operation.category or "Salaires",
                "piece_ref": operation.bank_reference or f"SAL-{entry_num}",
                "piece_date": operation.payment_date.strftime("%d/%m/%Y"),
                "description": f"Paiement salaires - {operation.notes or operation.category}",
                "debit": 0,
                "credit": float(operation.amount) if operation.payment_direction == "outgoing" else 0,
            }
            entries.append(entry)
        
        return entries
    
    def _get_rent_entries(self):
        """Get rent/loyer entries from bank operations marked as rent (LOY)."""
        entries = []
        
        # Query bank operations with rent-related categories
        rent_operations = BankOperation.objects.filter(
            user=self.user,
            category__icontains="loyer"
        )
        
        if self.month:
            rent_operations = rent_operations.filter(
                payment_date__year=self.year,
                payment_date__month=self.month
            )
        else:
            rent_operations = rent_operations.filter(payment_date__year=self.year)
        
        for operation in rent_operations:
            entry_num = self._next_entry_number()
            
            entry = {
                "journal": "LOY",
                "entry_number": entry_num,
                "date": operation.payment_date.strftime("%d/%m/%Y"),
                "account":generate_account(), 
                "account_label": "Loyer immédiat",
                "auxiliary": "Tiers",
                "tiers": operation.category or "Loyer",
                "piece_ref": operation.bank_reference or f"LOY-{entry_num}",
                "piece_date": operation.payment_date.strftime("%d/%m/%Y"),
                "description": f"Paiement loyer - {operation.notes or operation.category}",
                "debit": float(operation.amount) if operation.payment_direction == "outgoing" else 0,
                "credit": 0,
            }
            entries.append(entry)
        
        return entries
    
    def _get_misc_entries(self):
        """Get miscellaneous entries (OD - Opérations diverses)."""
        entries = []
        
        # Query bank operations that don't match other categories
        excluded_categories = ["salaire", "loyer"]
        
        misc_operations = BankOperation.objects.filter(user=self.user)
        
        if self.month:
            misc_operations = misc_operations.filter(
                payment_date__year=self.year,
                payment_date__month=self.month
            )
        else:
            misc_operations = misc_operations.filter(payment_date__year=self.year)
        
        # Exclude those already processed in other categories
        for operation in misc_operations:
            category_lower = (operation.category or "").lower()
            is_excluded = any(exc in category_lower for exc in excluded_categories)
            if is_excluded:
                continue
            
            entry_num = self._next_entry_number()
            
            entry = {
                "journal": "OD",
                "entry_number": entry_num,
                "date": operation.payment_date.strftime("%d/%m/%Y"),
                "account": generate_account(),
                "account_label": "Opérations diverses",
                "auxiliary": "Divers",
                "tiers": operation.category or "---",
                "piece_ref": operation.bank_reference or f"OD-{entry_num}",
                "piece_date": operation.payment_date.strftime("%d/%m/%Y"),
                "description": operation.notes or operation.category or "Opération diverse",
                "debit": float(operation.amount) if operation.payment_direction == "incoming" else 0,
                "credit": float(operation.amount) if operation.payment_direction == "outgoing" else 0,
            }
            entries.append(entry)
        
        return entries
    
    def build(self):
        """Build complete accounting journal with all transaction types."""
        company_info = self._get_company_info()
        
        # Collect all entries from all sources
        all_entries = []
        all_entries.extend(self._build_purchase_entries())
        all_entries.extend(self._build_sales_entries())
        all_entries.extend(self._get_rent_entries())
        all_entries.extend(self._get_salary_entries())
        all_entries.extend(self._build_bank_entries())
        all_entries.extend(self._get_misc_entries())
        
        # Sort by date, then by journal
        all_entries.sort(key=lambda x: (x["date"], x["journal"], x["entry_number"]))
        
        # Group by journal
        grouped_entries = {}
        journal_labels = {
            "ACH": "Factures Achat",
            "VEN": "Factures Vente",
            "IMM": "Immobilisations",
            "LOY": "Loyers",
            "SAL": "Salaires",
            "BAN": "Banque",
            "OD": "Opérations diverses"
        }
        
        for entry in all_entries:
            journal = entry["journal"]
            if journal not in grouped_entries:
                grouped_entries[journal] = {
                    "journal": journal,
                    "label": journal_labels.get(journal, journal),
                    "entries": []
                }
            grouped_entries[journal]["entries"].append(entry)
        
        # Calculate totals
        journals_summary = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")
        
        for journal_code in ["ACH", "VEN", "IMM", "LOY", "SAL", "BAN", "OD"]:
            if journal_code in grouped_entries:
                group = grouped_entries[journal_code]
                debit_sum = sum(Decimal(str(e["debit"])) for e in group["entries"])
                credit_sum = sum(Decimal(str(e["credit"])) for e in group["entries"])
                
                total_debit += debit_sum
                total_credit += credit_sum
                
                journals_summary.append({
                    "journal": journal_code,
                    "label": group["label"],
                    "entry_count": len(group["entries"]),
                    "debit_total": float(debit_sum),
                    "credit_total": float(credit_sum),
                    "balance": float(debit_sum - credit_sum),
                })
        
        period_label = f"{_month_label(self.month)} {self.year}" if self.month else f"Exercice {self.year}"
        
        return {
            "title": "COMPTAAI - Export détaillé des écritures comptables",
            "subtitle": f"Exercice {self.year}",
            "period": period_label,
            "enterprise": {
                "name": company_info["name"],
                "siret": company_info["siret"],
                "legal_form": company_info["legal_form"],
                "rcs_city": company_info["rcs_city"],
                "fiscal_year_start": company_info["fiscal_year_start"],
                "fiscal_year_end": company_info["fiscal_year_end"],
                "structure": "Structure conforme au Plan Comptable Général (France) - FEC généré séparément.",
            },
            "journals_summary": journals_summary,
            "grouped_entries": [
                {
                    "nature": group["label"],
                    "journal_code": journal,
                    "entries": group["entries"]
                }
                for journal, group in sorted(grouped_entries.items())
            ],
            "totals": {
                "total_debit": float(total_debit),
                "total_credit": float(total_credit),
                "balance": float(total_debit - total_credit),
            },
            "table_columns": [
                "Journal",
                "Numéro d'Écriture",
                "Date",
                "Compte",
                "Libellé du compte",
                "Aux",
                "Tiers",
                "Pièce",
                "Date pièce",
                "Libellé d'écriture",
                "Débit",
                "Crédit"
            ],
            "generated_at": self.today.isoformat(),
        }
