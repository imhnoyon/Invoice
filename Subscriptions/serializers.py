from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, PaymentHistory


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'status', 'plan', 'plan_name', 'start_date', 'end_date']

class PaymentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentHistory
        fields = '__all__'


class SubscriptionCurrentPlanSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(allow_null=True)
    plan_name = serializers.CharField(allow_blank=True, allow_null=True)
    status = serializers.CharField()
    status_label = serializers.CharField()
    next_billing_date = serializers.DateTimeField(allow_null=True)
    next_billing_date_display = serializers.CharField(allow_blank=True, allow_null=True)
    monthly_amount = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    monthly_amount_display = serializers.CharField()
    manage_label = serializers.CharField()


class SubscriptionInvoiceHistorySerializer(serializers.Serializer):
    no = serializers.IntegerField()
    invoice_id = serializers.CharField(allow_blank=True, allow_null=True)
    invoice_date = serializers.DateTimeField(allow_null=True)
    invoice_date_display = serializers.CharField(allow_blank=True, allow_null=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_display = serializers.CharField()
    plan = serializers.CharField(allow_blank=True, allow_null=True)
    action_url = serializers.CharField(allow_blank=True, allow_null=True)
    action_label = serializers.CharField()


class SubscriptionOverviewSerializer(serializers.Serializer):
    current_plan = SubscriptionCurrentPlanSerializer()
    invoice_history = SubscriptionInvoiceHistorySerializer(many=True)
