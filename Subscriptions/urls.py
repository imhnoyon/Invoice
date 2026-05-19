from django.urls import path
from .views import *

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('reactivate/', ReactivateSubscriptionView.as_view(), name='reactivate-subscription'),
    path('status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('overview/', SubscriptionOverviewView.as_view(), name='subscription-overview'),
]
