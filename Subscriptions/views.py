import stripe
from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, views, permissions
from rest_framework.response import Response
from .models import SubscriptionPlan, UserSubscription, PaymentHistory
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class PlanListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

class CreateCheckoutSessionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        user_subscription, created = UserSubscription.objects.get_or_create(user=user)

        # Check if it's the first time subscription to add setup fee
        # A user is "first-time" if they don't have a stripe_customer_id or have never had an ACTIVE subscription
        # However, the requirement says "When a user subscribes for the first time: Add one-time setup fee"
        # We'll check if they have any PaymentHistory or if stripe_customer_id is empty.
        
        add_setup_fee = not user_subscription.stripe_customer_id or not PaymentHistory.objects.filter(user=user).exists()

        try:
            if not user_subscription.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=user.email,
                    name=user.full_name,
                )
                user_subscription.stripe_customer_id = customer.id
                user_subscription.save()

            checkout_session_data = {
                "customer": user_subscription.stripe_customer_id,
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price_data": {
                            "currency": "bdt",
                            "product_data": {
                                "name": plan.name,
                            },
                            "unit_amount": int(plan.monthly_amount * 100),
                            "recurring": {
                                "interval": "month",
                            },
                        },
                        "quantity": 1,
                    },
                ],
                "mode": "subscription",
                "subscription_data": {
                    "metadata": {
                        "user_id": str(user.id),
                        "plan_id": str(plan.id),
                    }
                },
                "success_url": "http://localhost:3000/success?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": "http://localhost:3000/cancel",
                "metadata": {
                    "user_id": str(user.id),
                    "plan_id": str(plan.id),
                }
            }

            if add_setup_fee:
                checkout_session_data["line_items"].append({
                    "price_data": {
                        "currency": "bdt",
                        "product_data": {
                            "name": "One-time Setup Fee",
                        },
                        "unit_amount": int(settings.SETUP_FEE_AMOUNT * 100),
                    },
                    "quantity": 1,
                })

            session = stripe.checkout.Session.create(**checkout_session_data)
            return Response({"checkout_url": session.url})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_session_completed(session)
        
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            self.handle_subscription_updated(subscription)

        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            self.handle_subscription_deleted(subscription)

        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            self.handle_invoice_payment_succeeded(invoice)

        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            self.handle_invoice_payment_failed(invoice)

        return Response(status=status.HTTP_200_OK)

    def handle_checkout_session_completed(self, session):
        session_dict = session.to_dict() if hasattr(session, 'to_dict') else dict(session)
        metadata = session_dict.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        subscription_id = session_dict.get('subscription')

        if user_id and plan_id and subscription_id:
            try:
                # Retrieve and convert the subscription object
                subscription = stripe.Subscription.retrieve(subscription_id)
                sub_dict = subscription.to_dict() if hasattr(subscription, 'to_dict') else dict(subscription)
                
                user_sub = UserSubscription.objects.get(user_id=user_id)
                user_sub.stripe_subscription_id = subscription_id
                user_sub.plan_id = plan_id
                
                # Robust date handling with fallback to timezone.now()
                start_ts = sub_dict.get('current_period_start')
                end_ts = sub_dict.get('current_period_end')

                if start_ts:
                    user_sub.start_date = timezone.datetime.fromtimestamp(start_ts, tz=timezone.get_current_timezone())
                else:
                    user_sub.start_date = timezone.now()

                if end_ts:
                    user_sub.end_date = timezone.datetime.fromtimestamp(end_ts, tz=timezone.get_current_timezone())
                
                user_sub.status = 'ACTIVE'
                user_sub.save()
                print(f"Successfully updated subscription for user {user_id}")
            except Exception as e:
                print(f"Error saving subscription in checkout: {str(e)}")

    def handle_subscription_updated(self, subscription):
        sub_dict = subscription.to_dict() if hasattr(subscription, 'to_dict') else dict(subscription)
        stripe_subscription_id = sub_dict.get('id')
        metadata = sub_dict.get('metadata', {})
        user_id = metadata.get('user_id')
        plan_id = metadata.get('plan_id')
        
        user_sub = UserSubscription.objects.filter(stripe_subscription_id=stripe_subscription_id).first()
        
        if not user_sub and user_id:
            user_sub = UserSubscription.objects.filter(user_id=user_id).first()
            if user_sub:
                user_sub.stripe_subscription_id = stripe_subscription_id

        if user_sub:
            if plan_id:
                user_sub.plan_id = plan_id
            
            stripe_status = subscription['status']
            if stripe_status == 'active':
                user_sub.status = 'ACTIVE'
            elif stripe_status == 'past_due':
                user_sub.status = 'PAST_DUE'
            elif stripe_status == 'canceled':
                user_sub.status = 'CANCELED'
            elif stripe_status == 'incomplete_expired':
                user_sub.status = 'EXPIRED'
            
            user_sub.start_date = timezone.datetime.fromtimestamp(subscription['current_period_start'])
            user_sub.end_date = timezone.datetime.fromtimestamp(subscription['current_period_end'])
            user_sub.save()

    def handle_subscription_deleted(self, subscription):
        stripe_subscription_id = subscription['id']
        user_sub = UserSubscription.objects.filter(stripe_subscription_id=stripe_subscription_id).first()
        if user_sub:
            user_sub.status = 'EXPIRED'
            user_sub.save()

    def handle_invoice_payment_succeeded(self, invoice):
        inv_dict = invoice.to_dict() if hasattr(invoice, 'to_dict') else dict(invoice)
        customer_id = inv_dict.get('customer')
        subscription_id = inv_dict.get('subscription')
        
        user_sub = UserSubscription.objects.filter(stripe_customer_id=customer_id).first()
        if user_sub:
            if subscription_id and (not user_sub.stripe_subscription_id or not user_sub.plan):
                try:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    sub_dict = subscription.to_dict() if hasattr(subscription, 'to_dict') else dict(subscription)
                    
                    user_sub.stripe_subscription_id = subscription_id
                    sub_metadata = sub_dict.get('metadata', {})
                    user_sub.plan_id = sub_metadata.get('plan_id')
                    
                    user_sub.start_date = timezone.datetime.fromtimestamp(
                        sub_dict.get('current_period_start'), tz=timezone.get_current_timezone()
                    )
                    user_sub.end_date = timezone.datetime.fromtimestamp(
                        sub_dict.get('current_period_end'), tz=timezone.get_current_timezone()
                    )
                except Exception as e:
                    print(f"Error retrieving subscription in invoice handler: {str(e)}")

            PaymentHistory.objects.create(
                user=user_sub.user,
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_paid'] / 100,
                status='SUCCEEDED'
            )
            user_sub.status = 'ACTIVE'
            user_sub.save()

    def handle_invoice_payment_failed(self, invoice):
        customer_id = invoice['customer']
        user_sub = UserSubscription.objects.filter(stripe_customer_id=customer_id).first()
        if user_sub:
            PaymentHistory.objects.create(
                user=user_sub.user,
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_due'] / 100,
                status='FAILED'
            )
            # If payment fails, status might become PAST_DUE
            # Stripe usually handles the retries and status updates
            user_sub.status = 'PAST_DUE'
            user_sub.save()

class CancelSubscriptionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_sub = getattr(request.user, 'subscription', None)
        if not user_sub or not user_sub.stripe_subscription_id:
            return Response({"error": "No active subscription found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # We can either cancel immediately or at the end of period
            # For this requirement, we'll cancel it and let webhook handle the status update
            stripe.Subscription.delete(user_sub.stripe_subscription_id)
            user_sub.status = 'CANCELED'
            user_sub.save()
            return Response({"message": "Subscription canceled successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ReactivateSubscriptionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_sub = getattr(request.user, 'subscription', None)
        if not user_sub:
            return Response({"error": "Subscription record not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # To "reactivate" in Stripe, if it's already canceled, we usually create a new one.
        # If it was canceled but still in "cancel_at_period_end" state, we can undo it.
        # But here, we'll just redirect them to create a new checkout session if they are EXPIRED or CANCELED.
        # The requirement says "User can reactivate later without creating a new account".
        # This implies they can just subscribe again.
        
        return Response({"message": "Please use the checkout session to subscribe again."})

class SubscriptionStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_sub, created = UserSubscription.objects.get_or_create(user=request.user)
        serializer = UserSubscriptionSerializer(user_sub)
        return Response(serializer.data)
