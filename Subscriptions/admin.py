from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(SubscriptionPlan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'monthly_amount', 'stripe_price_id')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('id',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'status', 'start_date', 'end_date')
    list_filter = ('status',)
    search_fields = ('user__email', 'user__username', 'plan__name')
    ordering = ('id',)

@admin.register(PaymentHistory)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'user__username')
    ordering = ('id',)
