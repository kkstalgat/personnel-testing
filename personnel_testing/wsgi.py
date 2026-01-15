"""
WSGI config for personnel_testing project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'personnel_testing.settings')

application = get_wsgi_application()
