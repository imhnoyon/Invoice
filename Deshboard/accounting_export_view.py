"""
Accounting Export API View - Provides accounting journal endpoints
with subscription plan gating for detailed features.

This is a standalone view that does not modify existing functionality.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.api_response import APIResponse
from Subscriptions.models import UserSubscription

from .accounting_export import AccountingJournalBuilder


class AccountingExportAPIView(APIView):
    """
    API endpoint for detailed accounting journal export.
    
    Query Parameters:
    - year: Fiscal year (default: current year)
    - month: Specific month (optional, for monthly breakdown)
    - format: Export format (default: json, future: csv, pdf)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_subscription_state(self, user):
        """Determine if user has Pro plan for showing detailed accounting."""
        user_subscription = UserSubscription.objects.select_related("plan").filter(user=user).first()
        plan_name = (user_subscription.plan.name if user_subscription and user_subscription.plan else "") or ""
        is_pro_plan = bool(plan_name) and "pro" in plan_name.lower()
        return {"is_pro_plan": is_pro_plan}
    
    def get(self, request):
        """Generate and return accounting journal."""
        # Check subscription for feature access
        subscription_state = self.get_subscription_state(request.user)
        
        if not subscription_state["is_pro_plan"]:
            return APIResponse.error(
                message="Accounting export is available only for Pro Plan subscribers.",
                status_code=403
            )
        
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        
        try:
            builder = AccountingJournalBuilder(request.user, year=year, month=month)
            payload = builder.build()
            
            return APIResponse.success(
                message="Accounting journal exported successfully.",
                data=payload
            )
        except Exception as e:
            return APIResponse.error(
                message=f"Error generating accounting export: {str(e)}",
                status_code=400
            )


class AccountingJournalListView(APIView):
    """
    List all journal entries for a given period with optional filtering.
    
    Query Parameters:
    - year: Fiscal year
    - month: Optional month
    - journal: Filter by journal code (ACH, VEN, BAN, etc.)
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_subscription_state(self, user):
        """Determine if user has Pro plan."""
        user_subscription = UserSubscription.objects.select_related("plan").filter(user=user).first()
        plan_name = (user_subscription.plan.name if user_subscription and user_subscription.plan else "") or ""
        is_pro_plan = bool(plan_name) and "pro" in plan_name.lower()
        return {"is_pro_plan": is_pro_plan}
    
    def get(self, request):
        """List accounting journal entries with optional filtering."""
        subscription_state = self.get_subscription_state(request.user)
        
        if not subscription_state["is_pro_plan"]:
            return APIResponse.error(
                message="Accounting journal access is available only for Pro Plan subscribers.",
                status_code=403
            )
        
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        journal_filter = request.query_params.get("journal")
        
        try:
            builder = AccountingJournalBuilder(request.user, year=year, month=month)
            full_export = builder.build()
            
            entries = []
            if journal_filter:
                for group in full_export.get("grouped_entries", []):
                    # Filter by journal code
                    journal_code = None
                    for journal_code_check in ["ACH", "VEN", "IMM", "LOY", "SAL", "BAN", "OD"]:
                        if group.get("nature").startswith(journal_code_check) or journal_code_check in group.get("journal_code", ""):
                            if journal_code_check == journal_filter:
                                entries.extend(group.get("entries", []))
                            break
            else:
                # Return all entries
                for group in full_export.get("grouped_entries", []):
                    entries.extend(group.get("entries", []))
            
            return APIResponse.success(
                message="Journal entries retrieved successfully.",
                data={
                    "period": full_export.get("period"),
                    "company": full_export.get("enterprise"),
                    "entries": entries,
                    "totals": full_export.get("totals"),
                    "entry_count": len(entries),
                }
            )
        except Exception as e:
            return APIResponse.error(
                message=f"Error retrieving journal entries: {str(e)}",
                status_code=400
            )
