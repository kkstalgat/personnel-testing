"""
URL configuration for personnel_testing project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def api_root(request):
    """Корневой endpoint для API"""
    return JsonResponse({
        'message': 'Personnel Testing API',
        'version': '1.0',
        'endpoints': {
            'accounts': '/api/accounts/',
            'tests': '/api/tests/',
            'admin': '/admin/',
        },
        'documentation': '/api/docs/'
    })


def home(request):
    """Главная страница"""
    from django.shortcuts import render
    return render(request, 'index.html')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register'),
    path('verify-email/<str:token>/', TemplateView.as_view(template_name='verify_email.html'), name='verify_email'),
    path('api/', api_root, name='api_root'),
    path('api/accounts/', include('accounts.urls')),
    path('api/tests/', include('tests.urls')),
    re_path(r'^test/(?P<session_id>[^/]+)/$', TemplateView.as_view(template_name='test_page.html'), name='test_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
