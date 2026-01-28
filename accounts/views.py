from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Subscription, SubscriptionPlan, Module, UserModule
from .serializers import UserSerializer, SubscriptionSerializer, SubscriptionPlanSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Регистрация нового пользователя"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            
            # Отправка email с подтверждением
            verification_link = f"{settings.SITE_URL}/verify-email/{user.email_verification_token}/"
            send_mail(
                'Подтверждение регистрации',
                f'Перейдите по ссылке для подтверждения: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({'message': 'Регистрация успешна. Проверьте email для подтверждения.'}, 
                          status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_email(self, request):
        """Подтверждение email"""
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Токен не предоставлен'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email_verification_token=token)
            user.is_email_verified = True
            user.email_verification_token = ''
            user.save()
            return Response({'message': 'Email успешно подтвержден'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Неверный токен'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Авторизация пользователя с JWT токенами"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({'error': 'Email и пароль обязательны'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if not user.is_email_verified:
                    return Response({'error': 'Email не подтвержден'}, 
                                  status=status.HTTP_400_BAD_REQUEST)
                
                # Генерация JWT токенов
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                serializer = self.get_serializer(user)
                
                return Response({
                    'user': serializer.data,
                    'access': access_token,
                    'refresh': refresh_token
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Неверный пароль'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Получить профиль текущего пользователя"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Получить текущую активную подписку"""
        subscription = Subscription.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        return Response({'message': 'Активная подписка не найдена'}, 
                      status=status.HTTP_404_NOT_FOUND)
