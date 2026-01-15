from rest_framework import serializers
from .models import User, Subscription, SubscriptionPlan, Module, UserModule


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone', 'company_name', 
                 'is_email_verified', 'is_phone_verified', 'date_joined')
        read_only_fields = ('id', 'is_email_verified', 'is_phone_verified', 'date_joined')
    
    def create(self, validated_data):
        password = self.context['request'].data.get('password')
        from django.utils.crypto import get_random_string
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
        user.is_email_verified = False
        user.email_verification_token = get_random_string(32)
        user.save()
        return user


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'description', 'price', 'duration_days', 'tests_count')


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'plan', 'start_date', 'end_date', 
                 'is_active', 'remaining_tests')
        read_only_fields = ('id', 'user', 'start_date', 'end_date')


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ('id', 'name', 'description', 'price')


class UserModuleSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)
    
    class Meta:
        model = UserModule
        fields = ('id', 'user', 'module', 'purchased_at', 'expires_at', 'is_active')
