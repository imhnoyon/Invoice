from decimal import Decimal

from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Invoice, BankOperation


def _format_currency(value):
    amount = Decimal(str(value or 0))
    if amount == amount.to_integral():
        return f"{int(amount):,} €".replace(",", " ")
    return f"{amount.quantize(Decimal('0.01')):f} €".replace(".", ",")


def _month_label(month_number):
    labels = [
        "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
    ]
    return labels[month_number - 1]


class MonthlySummaryBuilder:
    def __init__(self, user, year=None):
        self.user = user
        self.year = int(year or timezone.now().year)
        self.today = timezone.localdate()

    def _invoice_queryset(self):
        return Invoice.objects.filter(company=self.user, invoice_type__in=["vente", "achat"], invoice_subtype="facture")

    def _monthly_invoice_stats(self, month_number):
        invoices = self._invoice_queryset().filter(invoice_date__year=self.year, invoice_date__month=month_number)

        sales = invoices.filter(invoice_type="vente")
        purchases = invoices.filter(invoice_type="achat")

        sales_ht = sales.aggregate(total=Coalesce(Sum("total_ht"), Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2))))["total"]
        purchases_ht = purchases.aggregate(total=Coalesce(Sum("total_ht"), Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2))))["total"]
        tva_collected = sales.aggregate(total=Coalesce(Sum("total_tva"), Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2))))["total"]
        tva_deductible = purchases.aggregate(total=Coalesce(Sum("total_tva"), Value(Decimal("0"), output_field=DecimalField(max_digits=12, decimal_places=2))))["total"]

        unpaid_sales = sales.filter(amount_paid__lt=F("total_ttc")).count()
        unpaid_purchases = purchases.filter(amount_paid__lt=F("total_ttc")).count()
        alerts = unpaid_sales + unpaid_purchases
        solde_tva = tva_collected - tva_deductible
        result_ht = sales_ht - purchases_ht
        profit_rate = (result_ht / sales_ht * Decimal("100")) if sales_ht > 0 else Decimal("0")

        month_operations = BankOperation.objects.filter(
            user=self.user,
            payment_date__year=self.year,
            payment_date__month=month_number,
        )
        references = [ref for ref in month_operations.exclude(bank_reference="").values_list("bank_reference", flat=True).distinct()]
        if references:
            reference_bank = references[0]
        elif alerts > 0:
            reference_bank = "Facture impayée"
        else:
            reference_bank = "Voir les détails"

        return {
            "sales_ht": sales_ht,
            "purchases_ht": purchases_ht,
            "tva_collected": tva_collected,
            "tva_deductible": tva_deductible,
            "solde_tva": solde_tva,
            "result_ht": result_ht,
            "reference_bank": reference_bank,
            "alerts": alerts,
            "profit_rate": profit_rate,
        }

    def build(self):
        rows = []
        total_sales_ht = Decimal("0")
        total_purchases_ht = Decimal("0")
        total_tva_collected = Decimal("0")
        total_tva_deductible = Decimal("0")
        total_alerts = 0

        for month_number in range(1, 13):
            stats = self._monthly_invoice_stats(month_number)
            if (
                stats["sales_ht"] == 0
                and stats["purchases_ht"] == 0
                and stats["tva_collected"] == 0
                and stats["tva_deductible"] == 0
                and stats["alerts"] == 0
            ):
                continue

            total_sales_ht += stats["sales_ht"]
            total_purchases_ht += stats["purchases_ht"]
            total_tva_collected += stats["tva_collected"]
            total_tva_deductible += stats["tva_deductible"]
            total_alerts += stats["alerts"]

            rows.append(
                {
                    "no": len(rows) + 1,
                    "month": f"{_month_label(month_number)} {self.year}",
                    "sales_ht_display": _format_currency(stats["sales_ht"]),
                    "purchases_ht_display": _format_currency(stats["purchases_ht"]),
                    "tva_collected_display": _format_currency(stats["tva_collected"]),
                    "tva_deductible_display": _format_currency(stats["tva_deductible"]),
                    "solde_tva_display": _format_currency(stats["solde_tva"]),
                    "result_ht_display": _format_currency(stats["result_ht"]),
                    "reference_bank": stats["reference_bank"],
                }
            )

        net_result = total_sales_ht - total_purchases_ht
        profit_rate = (net_result / total_sales_ht * Decimal("100")) if total_sales_ht > 0 else Decimal("0")
        selected_period_label = f"{self.year}"

        return {
            "alerts_summary": {
                "cards": [
                    {
                        "icon": "📅",
                        "label": "Période",
                        "value": _format_currency(total_sales_ht),
                    },
                    {
                        "icon": "💰",
                        "label": "Résultat Net",
                        "value": _format_currency(net_result),
                    },
                    {
                        "icon": "⚠️",
                        "label": "Alertes",
                        "value": str(total_alerts),
                    },
                ],
            },
            
            "table": {
                "title": "Tableau récapitulatif",
                "columns": [
                    "No",
                    "Mois",
                    "Ventes (HT)",
                    "Achats (HT)",
                    "TVA Collectée",
                    "TVA Déductible",
                    "Solde TVA",
                    "Résultat (HT)",
                    "Référence banque",
                ],
                "rows": rows,
                "totals": {
                    "label": "Total",
                    "sales_ht_display": _format_currency(total_sales_ht),
                    "purchases_ht_display": _format_currency(total_purchases_ht),
                    "tva_collected_display": _format_currency(total_tva_collected),
                    "tva_deductible_display": _format_currency(total_tva_deductible),
                    "solde_tva_display": _format_currency(total_tva_collected - total_tva_deductible),
                    "result_ht_display": _format_currency(net_result),
                    "profit_rate_display": f"{profit_rate.quantize(Decimal('0.01'))}% Profit" if total_sales_ht > 0 else "0% Profit",
                },
            },
            
            "quick_summary": {
                "title": "Résumé rapide",
                "cards": [
                    {
                        "label": "Revenu total",
                        "value": _format_currency(total_sales_ht),
                    },
                    {
                        "label": "Dépenses totales",
                        "value": _format_currency(total_purchases_ht),
                    },
                    {
                        "label": "Bénéfice net",
                        "value": _format_currency(net_result),
                    },
                    {
                        "label": "Marge bénéficiaire",
                        "value": f"{profit_rate.quantize(Decimal('0.01'))}%" if total_sales_ht > 0 else "0%",
                    },
                ],
            },
            "selected_period": selected_period_label,
             "tva_accounting": {
                "title": "Comptabilité TVA",
                "export_comptable": f"Exporté - {_month_label(self.today.month)} {self.today.year}",
                "ecriture_comptable": "Voir l'écriture",
                "resultat_si_bilan": _format_currency(total_tva_collected - total_tva_deductible),
                "compte_resultat_annee": str(self.year),
            },
        }