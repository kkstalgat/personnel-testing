from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SubscriptionPlan, Subscription, Module, UserModule


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'company_name', 'is_email_verified', 'is_phone_verified', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_email_verified', 'is_phone_verified', 'date_joined')
    search_fields = ('username', 'email', 'phone', 'company_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'company_name', 'is_email_verified', 'is_phone_verified')
        }),
    )


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'tests_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active', 'remaining_tests')
    list_filter = ('is_active', 'plan', 'start_date')
    search_fields = ('user__email', 'user__username', 'plan__name')
    readonly_fields = ('start_date', 'end_date')


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(UserModule)
class UserModuleAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'purchased_at', 'expires_at', 'is_active')
    list_filter = ('is_active', 'module')
    search_fields = ('user__email', 'module__name')
