from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from utils.api_response import APIResponse

from .monthly_summary import MonthlySummaryBuilder
from Subscriptions.models import UserSubscription


class MonthlySummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_subscription_state(self, user):
        user_subscription = UserSubscription.objects.select_related("plan").filter(user=user).first()
        plan_name = (user_subscription.plan.name if user_subscription and user_subscription.plan else "") or ""
        is_pro_plan = bool(plan_name) and "pro" in plan_name.lower()
        return {"is_pro_plan": is_pro_plan}

    def get(self, request):
        year = request.query_params.get("year")
        payload = MonthlySummaryBuilder(request.user, year).build()
        subscription_state = self.get_subscription_state(request.user)
        payload["show_details"] = bool(subscription_state["is_pro_plan"])
        return APIResponse.success(
            message="Monthly summary retrieved successfully.",
            data=payload,
        )