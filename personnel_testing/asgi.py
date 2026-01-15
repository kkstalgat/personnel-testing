"""
ASGI config for personnel_testing project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personnel_testing.settings')

application = get_asgi_application()
