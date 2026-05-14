from Subscriptions.models import SubscriptionPlan

# Plan configurations from the image
plans = [
    {
        "name": "Basic Plan",
        "monthly_amount": 300,
    },
    {
        "name": "Pro Plan",
        "monthly_amount": 500,
    }
]

for plan_data in plans:
    plan, created = SubscriptionPlan.objects.get_or_create(
        name=plan_data["name"],
        defaults={
            "monthly_amount": plan_data["monthly_amount"],
        }
    )
    if not created:
        plan.monthly_amount = plan_data["monthly_amount"]
        plan.save()
    print(f"Plan {plan.name} {'created' if created else 'updated'}")
